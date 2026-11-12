"""Web Routes for SEDRS System Frontend"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, current_app, send_file, send_from_directory
from functools import wraps
from datetime import datetime, timedelta
import os
import io

from extensions import db
from models import Patient, Interaction, Recommendation, SystemMetrics, AuditLog

web_bp = Blueprint('web', __name__)

def login_required(f):
    """Decorator for routes requiring login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'patient_id' not in session:
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for routes requiring admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'patient_id' not in session:
            return redirect(url_for('web.login'))
        if session.get('role') != 'admin':
            return render_template('error.html', error='Admin access required'), 403
        return f(*args, **kwargs)
    return decorated_function

@web_bp.route('/', methods=['GET'])
def index():
    """Landing page"""
    total_patients = Patient.query.count()
    total_interactions = Interaction.query.count()
    total_recommendations = Recommendation.query.count()
    
    return render_template('index.html',
                         total_patients=total_patients,
                         total_interactions=total_interactions,
                         total_recommendations=total_recommendations)

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Patient login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        patient = Patient.query.filter_by(email=email).first()
        
        if patient and patient.check_password(password):
            session['patient_id'] = patient.id
            session['patient_email'] = patient.email
            session['role'] = patient.role or 'patient'
            if patient.role == 'admin':
                return redirect(url_for('web.admin_dashboard'))
            return redirect(url_for('web.dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password'), 401
    
    return render_template('login.html')

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Patient registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if Patient.query.filter_by(email=email).first():
            return render_template('register.html', error='Patient already exists'), 409
        
        patient = Patient(
            email=email,
            age=request.form.get('age', type=int),
            gender=request.form.get('gender'),
            medical_conditions=request.form.get('medical_conditions'),
            allergies=request.form.get('allergies'),
            current_medications=request.form.get('current_medications')
        )
        patient.set_password(password)
        
        db.session.add(patient)
        db.session.commit()
        
        session['patient_id'] = patient.id
        session['patient_email'] = patient.email
        session['role'] = 'patient'
        
        return redirect(url_for('web.dashboard'))
    
    return render_template('register.html')

@web_bp.route('/logout', methods=['GET'])
def logout():
    """Patient logout"""
    session.clear()
    return redirect(url_for('web.index'))

@web_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Patient dashboard with health trends"""
    patient_id = session.get('patient_id')
    patient = Patient.query.get(patient_id)
    
    # Get recent interactions
    recent_interactions = Interaction.query.filter_by(patient_id=patient_id)\
        .order_by(Interaction.created_at.desc()).limit(5).all()
    
    # Get statistics
    total_interactions = Interaction.query.filter_by(patient_id=patient_id).count()
    avg_confidence = db.session.query(db.func.avg(Interaction.overall_confidence))\
        .filter_by(patient_id=patient_id).scalar() or 0
    
    # Get most recent recommendations
    recent_recs = db.session.query(Recommendation).join(Interaction)\
        .filter(Interaction.patient_id == patient_id)\
        .order_by(Recommendation.created_at.desc()).limit(5).all()
    
    # Calculate health trend
    health_trend = _calculate_health_trend(patient_id)
    
    return render_template('dashboard.html',
                         patient=patient,
                         interactions=recent_interactions,
                         recommendations=recent_recs,
                         total_interactions=total_interactions,
                         avg_confidence=round(float(avg_confidence), 4),
                         stats_available=total_interactions > 0,
                         health_trend=health_trend)

@web_bp.route('/patient/profile', methods=['GET', 'POST'])
@login_required
def patient_profile():
    """Patient profile view and edit"""
    patient_id = session.get('patient_id')
    patient = Patient.query.get(patient_id)
    
    if request.method == 'POST':
        patient.age = request.form.get('age', type=int) or patient.age
        patient.gender = request.form.get('gender') or patient.gender
        patient.medical_conditions = request.form.get('medical_conditions') or patient.medical_conditions
        patient.allergies = request.form.get('allergies') or patient.allergies
        patient.current_medications = request.form.get('current_medications') or patient.current_medications
        patient.updated_at = datetime.utcnow()
        
        db.session.commit()
        return redirect(url_for('web.patient_profile'))
    
    # Stats for profile page
    total_interactions = Interaction.query.filter_by(patient_id=patient_id).count()
    total_recommendations = db.session.query(Recommendation).join(Interaction)\
        .filter(Interaction.patient_id == patient_id).count()
    health_status = _calculate_health_trend(patient_id)
    health_status = health_status.capitalize() if health_status else 'Stable'
    
    return render_template('patient_profile.html', patient=patient,
                         total_interactions=total_interactions,
                         total_recommendations=total_recommendations,
                         health_status=health_status)

@web_bp.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze_input():
    """Multi-modal analysis interface"""
    patient_id = session.get('patient_id')
    
    if request.method == 'POST':
        interaction_id = request.form.get('interaction_id')
        if interaction_id and interaction_id.isdigit():
            return redirect(url_for('web.analysis_results', 
                                  interaction_id=int(interaction_id)))
        # If no interaction_id or invalid, just render the page again
        # This prevents "invalid literal for int()" error if empty string is passed
        return render_template('analyze.html', patient_id=patient_id)
    
    return render_template('analyze.html', patient_id=patient_id)

@web_bp.route('/results/<int:interaction_id>', methods=['GET'])
@login_required
def analysis_results(interaction_id):
    """Display analysis results"""
    patient_id = session.get('patient_id')
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Verify ownership
    if interaction.patient_id != patient_id:
        return render_template('error.html', error='Unauthorized'), 403
    
    recommendations = Recommendation.query.filter_by(interaction_id=interaction_id)\
        .order_by(Recommendation.rank).all()
    
    return render_template('results.html',
                         interaction=interaction,
                         recommendations=recommendations)

@web_bp.route('/feedback/<int:recommendation_id>', methods=['GET', 'POST'])
@login_required
def feedback_form(recommendation_id):
    """Feedback submission"""
    patient_id = session.get('patient_id')
    recommendation = Recommendation.query.get_or_404(recommendation_id)
    
    if recommendation.patient_id != patient_id:
        return render_template('error.html', error='Unauthorized'), 403
    
    if request.method == 'POST':
        return redirect(url_for('web.feedback_confirmation',
                               recommendation_id=recommendation_id))
    
    return render_template('feedback.html', recommendation=recommendation)

@web_bp.route('/feedback/confirmation/<int:recommendation_id>', methods=['GET'])
@login_required
def feedback_confirmation(recommendation_id):
    """Feedback confirmation"""
    recommendation = Recommendation.query.get_or_404(recommendation_id)
    return render_template('feedback_confirmation.html',
                         recommendation=recommendation)

@web_bp.route('/history', methods=['GET'])
@login_required
def interaction_history():
    """Patient interaction history"""
    patient_id = session.get('patient_id')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    interactions = Interaction.query.filter_by(patient_id=patient_id)\
        .order_by(Interaction.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('history.html',
                         interactions=interactions,
                         patient_id=patient_id)

@web_bp.route('/recommendations', methods=['GET'])
@login_required
def recommendations_view():
    """Patient recommendations history"""
    patient_id = session.get('patient_id')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    recommendations = db.session.query(Recommendation).join(Patient)\
        .filter(Patient.id == patient_id)\
        .order_by(Recommendation.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('recommendations.html',
                         recommendations=recommendations,
                         patient_id=patient_id)

@web_bp.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    """Admin system metrics dashboard"""
    
    total_patients = Patient.query.count()
    total_interactions = Interaction.query.count()
    total_recommendations = Recommendation.query.count()
    
    # Metrics over time
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_interactions = Interaction.query.filter(
        Interaction.created_at >= seven_days_ago
    ).count()
    
    avg_confidence = db.session.query(db.func.avg(Interaction.overall_confidence)).scalar() or 0
    
    # Top drugs
    top_drugs = db.session.query(
        Recommendation.drug_name,
        db.func.count(Recommendation.id).label('count')
    ).group_by(Recommendation.drug_name).order_by(db.text('count DESC')).limit(10).all()
    
    # Top conditions
    top_conditions = db.session.query(
        Interaction.condition,
        db.func.count(Interaction.id).label('count')
    ).group_by(Interaction.condition).order_by(db.text('count DESC')).limit(10).all()
    
    # Recent audit logs
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    
    # Sentiment distribution
    sentiment_dist = db.session.query(
        Interaction.sentiment_label,
        db.func.count(Interaction.id)
    ).filter(Interaction.sentiment_label.isnot(None))\
    .group_by(Interaction.sentiment_label).all()
    
    # Model accuracy metrics from IEEE paper
    model_metrics = {
        'bert_accuracy': 93.6,
        'bert_precision': 92.8,
        'bert_recall': 93.2,
        'bert_f1': 93.0,
        'cnn_lstm_accuracy': 90.9,
        'cnn_lstm_precision': 89.8,
        'cnn_lstm_recall': 90.4,
        'cnn_lstm_f1': 90.2,
        'resnet_accuracy': 88.1,
        'overall_accuracy': 90.2
    }
    
    # Avg feedback rating
    avg_feedback = db.session.query(db.func.avg(Recommendation.user_feedback))\
        .filter(Recommendation.user_feedback.isnot(None)).scalar() or 0
    
    # Recent Interactions List for Dashboard
    recent_interactions_list = Interaction.query.order_by(Interaction.created_at.desc()).limit(10).all()

    return render_template('admin_dashboard.html',
                         total_patients=total_patients,
                         total_interactions=total_interactions,
                         total_recommendations=total_recommendations,
                         recent_interactions_7d=recent_interactions,
                         avg_confidence=round(float(avg_confidence), 4),
                         top_drugs=top_drugs,
                         top_conditions=top_conditions,
                         audit_logs=audit_logs,
                         sentiment_dist=sentiment_dist,
                         model_metrics=model_metrics,
                         recent_interactions_list=recent_interactions_list,
                         avg_feedback=round(float(avg_feedback), 1))

@web_bp.route('/admin/patients', methods=['GET'])
@admin_required
def admin_patients():
    """Admin patient management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search = request.args.get('search', '')
    
    query = Patient.query
    if search:
        query = query.filter(Patient.email.ilike(f'%{search}%'))
    
    patients = query.order_by(Patient.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('admin_patients.html',
                         patients=patients,
                         search=search)

@web_bp.route('/admin/interactions', methods=['GET'])
@admin_required
def admin_interactions():
    """Admin interaction logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    interactions = Interaction.query.order_by(Interaction.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('admin_interactions.html',
                         interactions=interactions)

@web_bp.route('/admin/audit', methods=['GET'])
@admin_required
def admin_audit():
    """Admin audit trail"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = AuditLog.query.order_by(AuditLog.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('admin_audit.html',
                         logs=logs)

@web_bp.route('/admin/patient/<int:patient_id>', methods=['GET'])
@admin_required
def admin_patient_view(patient_id):
    """Admin view of specific patient profile"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get interactions for this patient
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    interactions = Interaction.query.filter_by(patient_id=patient_id)\
        .order_by(Interaction.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('admin_patient_profile.html',
                         patient=patient,
                         interactions=interactions)

@web_bp.route('/admin/patient/clear-history/<int:patient_id>', methods=['POST'])
@admin_required
def admin_clear_patient_history(patient_id):
    """Clear all interaction history for a patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Delete all interactions (cascading should handle recommendations if set up, 
    # but let's be safe and rely on the model's cascade)
    try:
        num_deleted = Interaction.query.filter_by(patient_id=patient_id).delete()
        
        # Log the action
        log = AuditLog(
            action='Clear History',
            resource_type='Patient',
            resource_id=patient_id,
            old_value=f'{num_deleted} interactions deleted',
            ip_address=request.remote_addr,
            user_agent=str(request.user_agent)
        )
        db.session.add(log)
        db.session.commit()
        
        # Flash message usage requires secret key which should be in config
        # For now we'll just redirect
        return redirect(url_for('web.admin_patient_view', patient_id=patient_id))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error clearing history: {e}")
        return render_template('error.html', error='Failed to clear history'), 500

@web_bp.route('/admin/report/patient/<int:patient_id>', methods=['GET'])
@admin_required
def admin_patient_report(patient_id):
    """Download full patient history report"""
    patient = Patient.query.get_or_404(patient_id)
    interactions = Interaction.query.filter_by(patient_id=patient_id)\
        .order_by(Interaction.created_at.desc()).all()
    
    from report_generator import generate_full_patient_report
    pdf_bytes = generate_full_patient_report(patient, interactions)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'SEDRS_Full_Report_{patient.id}_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@web_bp.route('/api/chart-data', methods=['GET'])
def chart_data():
    """Get chart data for dashboard"""
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily interactions
    daily_data = db.session.query(
        db.func.date(Interaction.created_at).label('date'),
        db.func.count(Interaction.id).label('count'),
        db.func.avg(Interaction.overall_confidence).label('avg_confidence')
    ).filter(Interaction.created_at >= start_date)\
    .group_by(db.func.date(Interaction.created_at))\
    .order_by('date').all()
    
    return jsonify({
        'dates': [str(d[0]) for d in daily_data],
        'interaction_counts': [d[1] for d in daily_data],
        'avg_confidence': [round(float(d[2]) if d[2] else 0, 4) for d in daily_data]
    })


@web_bp.route('/patient/chart-data', methods=['GET'])
@login_required
def patient_chart_data():
    """Get chart data for the current patient's dashboard"""
    patient_id = session.get('patient_id')
    
    interactions = Interaction.query.filter_by(patient_id=patient_id)\
        .order_by(Interaction.created_at.asc()).all()
    
    dates = []
    confidences = []
    for inter in interactions:
        dates.append(inter.created_at.strftime('%b %d') if inter.created_at else 'N/A')
        confidences.append(round(float(inter.overall_confidence or 0), 4))
    
    return jsonify({
        'dates': dates,
        'avg_confidence': confidences
    })


@web_bp.route('/report/<int:interaction_id>', methods=['GET'])
@login_required
def download_report(interaction_id):
    """Download PDF report for an interaction"""
    patient_id = session.get('patient_id')
    interaction = Interaction.query.get_or_404(interaction_id)
    
    # Verify ownership
    if interaction.patient_id != patient_id:
        return render_template('error.html', error='Unauthorized'), 403
    
    patient = Patient.query.get(patient_id)
    recommendations = Recommendation.query.filter_by(interaction_id=interaction_id)\
        .order_by(Recommendation.rank).all()
    
    from report_generator import generate_report
    pdf_bytes = generate_report(patient, interaction, recommendations)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'SEDRS_Report_{interaction_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
    )


def _calculate_health_trend(patient_id):
    """Calculate health trend based on recent interaction confidence scores.
    
    Compares the average confidence of the last 3 interactions vs the 3 before that.
    Returns 'improving', 'declining', or 'stable'.
    """
    recent = Interaction.query.filter_by(patient_id=patient_id)\
        .order_by(Interaction.created_at.desc()).limit(6).all()
    
    if len(recent) < 2:
        return 'stable'
    
    recent_scores = [float(i.overall_confidence or 0) for i in recent[:3]]
    older_scores = [float(i.overall_confidence or 0) for i in recent[3:]]
    
    if not older_scores:
        return 'stable'
    
    avg_recent = sum(recent_scores) / len(recent_scores)
    avg_older = sum(older_scores) / len(older_scores)
    
    diff = avg_recent - avg_older
    if diff > 0.05:
        return 'improving'
    elif diff < -0.05:
        return 'declining'
    return 'stable'


@web_bp.route('/chatbot', methods=['GET'])
def chatbot_page():
    """Gemma-powered medical chatbot with chain-of-thought UI"""
    return render_template('chatbot_gemma.html')


@web_bp.route('/naxerion/')
def naxerion_index():
    """Serve Naxerion AI interface"""
    # Assuming app run from project root
    return send_file(os.path.join(os.getcwd(), 'Naxerion - AI-Online', 'index.html'))

@web_bp.route('/naxerion/<path:filename>')
def naxerion_static(filename):
    """Serve Naxerion AI static files"""
    return send_from_directory(os.path.join(os.getcwd(), 'Naxerion - AI-Online'), filename)

@web_bp.route('/naxerion-offline/')
def naxerion_offline_index():
    """Serve Naxerion AI Offline interface"""
    return send_file(os.path.join(os.getcwd(), 'Naxerion-AI-Offline', 'frontend', 'index.html'))

@web_bp.route('/naxerion-offline/<path:filename>')
def naxerion_offline_static(filename):
    """Serve Naxerion AI Offline static files"""
    return send_from_directory(os.path.join(os.getcwd(), 'Naxerion-AI-Offline', 'frontend'), filename)

@web_bp.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('error.html', error='Page not found'), 404

@web_bp.errorhandler(500)
def server_error(e):
    """500 error handler"""
    return render_template('error.html', error='Internal server error'), 500

