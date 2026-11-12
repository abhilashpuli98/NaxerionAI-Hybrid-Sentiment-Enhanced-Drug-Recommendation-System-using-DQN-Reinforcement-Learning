"""REST API Routes for SEDRS System"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import time
import os
import json
import torch
import numpy as np

from extensions import db
from models import Patient, Interaction, Recommendation, SystemMetrics, AuditLog
from main_system import SEDRSystem
from data_utils import MetricsCalculator

api_bp = Blueprint('api', __name__)


def _auto_detect_condition(text):
    """Auto-detect medical condition from patient text input."""
    text_lower = text.lower()
    conditions = [
        ('heart', ['heart', 'cardiac', 'chest', 'stroke', 'attack', 'breathing']),
        ('malaria', ['malaria', 'plasmodium']),
        ('fever', ['fever', 'temperature', 'chills', 'shivering']),
        ('flu', ['flu', 'influenza']),
        ('cold', ['cold', 'runny nose', 'sneezing']),
        ('headache', ['headache', 'migraine', 'head pain']),
        ('pain', ['body ache', 'pain', 'sore', 'ache']),
        ('infection', ['infection', 'bacterial', 'infected']),
        ('cough', ['cough', 'coughing']),
        ('diabetes', ['diabetes', 'blood sugar', 'insulin']),
        ('hypertension', ['hypertension', 'blood pressure', 'bp']),
        ('allergy', ['allergy', 'allergic', 'itching']),
        ('diarrhea', ['diarrhea', 'loose motion', 'stomach']),
        ('depression', ['depression', 'depressed', 'anxiety', 'anxious']),
        ('asthma', ['asthma', 'breathing difficulty', 'wheezing']),
        ('skin', ['rash', 'skin', 'fungal', 'eczema']),
        ('acid reflux', ['acid', 'reflux', 'gerd', 'heartburn']),
        ('cholesterol', ['cholesterol']),
        ('thyroid', ['thyroid']),
    ]
    for condition_name, keywords in conditions:
        for kw in keywords:
            if kw in text_lower:
                return condition_name
    return 'general'

# Lazy-load SEDRS system on first use
_sedrs_instance = None

def get_sedrs():
    """Get or create SEDRS system instance (lazy loading)"""
    global _sedrs_instance
    if _sedrs_instance is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        _sedrs_instance = SEDRSystem(device=device)
    return _sedrs_instance

def allowed_file(filename, filetype='audio'):
    """Validate file extension"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if filetype == 'audio':
        return ext in {'wav', 'mp3', 'm4a', 'flac'}
    elif filetype == 'image':
        return ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    return False

def log_audit(action, resource_type, resource_id, old_value=None, new_value=None):
    """Log audit trail"""
    try:
        audit = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=str(old_value)[:1000] if old_value else None,
            new_value=str(new_value)[:1000] if new_value else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Audit logging error: {e}")

@api_bp.route('/health', methods=['GET'])
def health_check():
    """System health check endpoint"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'device': 'cpu',
        'models': {
            'text_analyzer': 'loaded',
            'audio_analyzer': 'loaded',
            'image_analyzer': 'loaded',
            'dqn_agent': 'loaded'
        }
    }), 200

@api_bp.route('/patients', methods=['POST'])
def create_patient():
    """Create new patient record"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        if Patient.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Patient already exists'}), 409
        
        patient = Patient(
            email=data['email'],
            age=data.get('age'),
            gender=data.get('gender'),
            medical_conditions=data.get('medical_conditions'),
            allergies=data.get('allergies'),
            current_medications=data.get('current_medications')
        )
        
        db.session.add(patient)
        db.session.commit()
        
        log_audit('CREATE', 'Patient', patient.id, 
                 new_value={'email': patient.email, 'age': patient.age})
        
        return jsonify(patient.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create patient error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get patient details"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        data = patient.to_dict()
        data['interactions_count'] = len(patient.interactions)
        data['recommendations_count'] = len(patient.recommendations)
        return jsonify(data), 200
    except Exception as e:
        current_app.logger.error(f"Get patient error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Update patient information"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        data = request.get_json()
        
        old_value = patient.to_dict()
        
        if 'age' in data:
            patient.age = data['age']
        if 'gender' in data:
            patient.gender = data['gender']
        if 'medical_conditions' in data:
            patient.medical_conditions = data['medical_conditions']
        if 'allergies' in data:
            patient.allergies = data['allergies']
        if 'current_medications' in data:
            patient.current_medications = data['current_medications']
        
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit('UPDATE', 'Patient', patient_id, old_value, patient.to_dict())
        
        return jsonify(patient.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update patient error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analyze', methods=['POST'])
def analyze_patient_input():
    """Analyze patient input and generate recommendations"""
    start_time = time.time()
    
    try:
        patient_id = request.form.get('patient_id')
        condition = request.form.get('condition', '').strip()
        text_input = request.form.get('text_input', '')
        top_k = request.form.get('top_k', 5, type=int)
        
        # Clamp top_k to reasonable range
        if top_k < 1:
            top_k = 5
        if top_k > 50:
            top_k = 50
        
        # Auto-detect condition from text if not provided
        if not condition:
            if text_input:
                condition = _auto_detect_condition(text_input)
            else:
                condition = "General"
                
        # Persist condition to form data for consistency
        request.form = request.form.copy()
        request.form['condition'] = condition
        
        if not patient_id or not patient_id.strip():
             return jsonify({'error': 'Patient ID is required'}), 400
             
        try:
            patient_id = int(patient_id)
        except ValueError:
            return jsonify({'error': 'Invalid Patient ID format'}), 400
        
        patient = Patient.query.get_or_404(patient_id)
        
        audio_file = None
        audio_key = 'audio_file' if 'audio_file' in request.files else 'audio_input'
        if audio_key in request.files:
            file = request.files[audio_key]
            if file and file.filename and allowed_file(file.filename, 'audio'):
                filename = secure_filename(f"{patient_id}_{int(time.time())}_audio.wav")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                audio_file = filepath
        
        image_file = None
        image_key = 'image_file' if 'image_file' in request.files else 'image_input'
        if image_key in request.files:
            file = request.files[image_key]
            if file and file.filename and allowed_file(file.filename, 'image'):
                filename = secure_filename(f"{patient_id}_{int(time.time())}_image.jpg")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_file = filepath
        
        # Run full pipeline
        report = get_sedrs().full_pipeline(
            patient_condition=condition,
            text_review=text_input,
            audio_path=audio_file,
            image_path=image_file,
            top_k=top_k
        )
        
        # Derive sentiment label from text prediction
        text_pred = report['sentiment_analysis']['text']['prediction']
        sentiment_labels = {0: 'negative', 1: 'neutral', 2: 'positive'}
        sentiment_label = sentiment_labels.get(text_pred, 'neutral') if text_pred is not None else 'neutral'
        
        # Create interaction record
        interaction = Interaction(
            patient_id=patient_id,
            condition=condition,
            text_input=text_input,
            audio_file=audio_file,
            image_file=image_file,
            text_sentiment=report['sentiment_analysis']['text']['prediction'],
            text_confidence=report['sentiment_analysis']['text']['confidence'],
            audio_emotion=report['sentiment_analysis']['audio']['prediction'],
            audio_confidence=report['sentiment_analysis']['audio']['confidence'],
            image_validity=report['sentiment_analysis']['image']['prediction'],
            image_confidence=report['sentiment_analysis']['image']['confidence'],
            sentiment_label=sentiment_label,
            sentiment_score=report['sentiment_analysis']['fused_sentiment_score'],
            fused_score=report['sentiment_analysis']['fused_sentiment_score'],
            overall_confidence=report['sentiment_analysis']['overall_confidence'],
            result_json=str(report),
            processed_at=datetime.utcnow()
        )
        
        db.session.add(interaction)
        db.session.flush()
        
        # Store recommendations
        for idx, rec in enumerate(report['recommendations'], 1):
            recommendation = Recommendation(
                patient_id=patient_id,
                interaction_id=interaction.id,
                drug_id=rec.get('drug_id'),
                drug_name=rec['drug_name'],
                category=rec['category'],
                score=rec['score'],
                base_rating=rec['base_rating'],
                confidence=rec['confidence'],
                rank=idx,
                composite_score=rec.get('composite_score', 0.0),
                efficacy_score=rec.get('efficacy_score', 0.0),
                sentiment_score=rec.get('sentiment_score', 0.0),
                side_effects=', '.join(rec.get('side_effects', [])),
                reason=rec.get('reason', '')
            )
            db.session.add(recommendation)
        
        db.session.commit()
        
        log_audit('ANALYZE', 'Interaction', interaction.id, 
                 new_value={'condition': condition, 'confidence': interaction.overall_confidence})
        
        # Response time
        elapsed_time = (time.time() - start_time) * 1000
        
        response_data = {
            'interaction_id': interaction.id,
            'status': 'success',
            'timestamp': interaction.processed_at.isoformat(),
            'response_time_ms': round(elapsed_time, 2),
            'sentiment_analysis': {
                'text': {
                    'sentiment': report['sentiment_analysis']['text']['prediction'],
                    'confidence': round(report['sentiment_analysis']['text']['confidence'], 4)
                },
                'audio': {
                    'emotion': report['sentiment_analysis']['audio']['prediction'],
                    'confidence': round(report['sentiment_analysis']['audio']['confidence'], 4)
                },
                'image': {
                    'validity': {0: 'Invalid', 1: 'Uncertain', 2: 'Valid'}.get(
                        report['sentiment_analysis']['image']['prediction'], 'Unknown'
                    ),
                    'confidence': round(report['sentiment_analysis']['image']['confidence'], 4)
                },
                'fused_score': round(report['sentiment_analysis']['fused_sentiment_score'], 4),
                'overall_confidence': round(report['sentiment_analysis']['overall_confidence'], 4)
            },
            'recommendations': [
                {
                    'rank': idx + 1,
                    'drug_name': rec['drug_name'],
                    'category': rec['category'],
                    'score': round(rec['score'], 4),
                    'confidence': round(rec['confidence'], 4),
                    'side_effects': rec.get('side_effects', [])
                }
                for idx, rec in enumerate(report['recommendations'][:5])
            ]
        }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e), 'status': 'failed'}), 500

@api_bp.route('/interactions/<int:interaction_id>', methods=['GET'])
def get_interaction(interaction_id):
    """Get interaction details"""
    try:
        interaction = Interaction.query.get_or_404(interaction_id)
        data = interaction.to_dict()
        data['recommendations'] = [r.to_dict() for r in interaction.recommendations]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/recommendations/<int:recommendation_id>/feedback', methods=['POST'])
def submit_feedback(recommendation_id):
    """Submit user feedback on recommendation"""
    try:
        recommendation = Recommendation.query.get_or_404(recommendation_id)
        data = request.get_json()
        
        recommendation.user_feedback = data.get('rating')
        recommendation.effectiveness = data.get('effectiveness')
        recommendation.adverse_effects = data.get('adverse_effects')
        recommendation.feedback_date = datetime.utcnow()
        
        db.session.commit()
        
        get_sedrs().apply_reinforcement_learning(
            state=np.random.randn(256),
            drug_id=recommendation.drug_id,
            reward=data.get('rating', 3) / 5.0
        )
        
        log_audit('FEEDBACK', 'Recommendation', recommendation_id,
                 new_value={'rating': data.get('rating'), 'effectiveness': data.get('effectiveness')})
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback recorded',
            'recommendation': recommendation.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Feedback error: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/patients/<int:patient_id>/history', methods=['GET'])
def get_patient_history(patient_id):
    """Get patient interaction history"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        interactions = Interaction.query.filter_by(patient_id=patient_id)\
            .order_by(Interaction.created_at.desc())\
            .paginate(page=page, per_page=per_page)
        
        return jsonify({
            'patient_id': patient_id,
            'total_interactions': interactions.total,
            'page': page,
            'per_page': per_page,
            'interactions': [
                {
                    'id': i.id,
                    'condition': i.condition,
                    'fused_score': i.fused_score,
                    'confidence': i.overall_confidence,
                    'created_at': i.created_at.isoformat(),
                    'recommendations_count': len(i.recommendations)
                }
                for i in interactions.items
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        total_patients = Patient.query.count()
        total_interactions = Interaction.query.count()
        total_recommendations = Recommendation.query.count()
        
        avg_confidence = db.session.query(db.func.avg(Interaction.overall_confidence)).scalar() or 0
        
        successful_interactions = Interaction.query.filter(Interaction.overall_confidence >= 0.6).count()
        success_rate = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'total_patients': total_patients,
            'total_interactions': total_interactions,
            'total_recommendations': total_recommendations,
            'avg_confidence': round(float(avg_confidence), 4),
            'success_rate': round(success_rate, 2),
            'device': 'cpu'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Get metrics error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get audit trail"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = AuditLog.query.order_by(AuditLog.created_at.desc())\
            .paginate(page=page, per_page=per_page)
        
        return jsonify({
            'total': logs.total,
            'page': page,
            'logs': [
                {
                    'action': l.action,
                    'resource_type': l.resource_type,
                    'ip_address': l.ip_address,
                    'created_at': l.created_at.isoformat()
                }
                for l in logs.items
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# GEMMA / OLLAMA CHATBOT ENDPOINTS (Naxerion-AI Integration)
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_best_model():
    """Auto-detect the best available Ollama model.
    Priority: vignan-naxerion-ai > gemma4 > gemma3 > any available model
    """
    import requests as http_requests
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    
    # Allow manual override via env var
    manual = os.environ.get('OLLAMA_MODEL')
    if manual:
        return manual
    
    try:
        resp = http_requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            
            # Priority order
            for preferred in [
                'gemma4:e4b',
                'gemma4',
                'vignan-naxerion-ai:latest',
                'vignan-naxerion-ai',
                
                
            ]:
                for m in models:
                    if m.startswith(preferred.split(':')[0]) or m == preferred:
                        return m
            
            # Fallback: any gemma model
            for m in models:
                if 'gemma' in m.lower():
                    return m
            
            # Last resort: first available model (skip cloud models)
            for m in models:
                if ':cloud' not in m:
                    return m
    except Exception:
        pass
    
    return 'gemma4:e4b'  # Default


@api_bp.route('/chatbot', methods=['POST'])
def chatbot_endpoint():
    """
    Streaming chatbot endpoint using local Ollama (Naxerion / Gemma model).
    
    Expects JSON: {"message": "...", "history": [...]}
    Returns: Streaming text/event-stream with thinking + final answer.
    
    Gemma models natively support <think>...</think> blocks.
    The frontend parses these to show a collapsible "Thinking" section.
    """
    import requests as http_requests
    from flask import Response, stream_with_context

    data = request.get_json(force=True)
    user_message = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    # Build Ollama prompt with SEDRS medical context
    system_prompt = (
        "You are SEDRS Medical AI Assistant (Naxerion-AI), a knowledgeable healthcare AI "
        "built for Vignan's Foundation for Science, Technology and Research. "
        "You help patients understand drug recommendations, side effects, and "
        "medical conditions. Always advise consulting a real doctor for serious conditions. "
        "Be concise, accurate, and empathetic.\n\n"
        "IMPORTANT: Before answering, reason step-by-step inside <think>...</think> tags. "
        "Keep your thinking brief (2-4 sentences). Then provide your final answer outside the tags."
    )

    # Build messages list for Ollama
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    MODEL_NAME = _detect_best_model()

    def generate():
        try:
            resp = http_requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": True,
                    "options": {"temperature": 0.7, "top_p": 0.9}
                },
                stream=True,
                timeout=180,
            )

            if resp.status_code != 200:
                err_text = f"Ollama returned status {resp.status_code}"
                try:
                    err_text += f": {resp.text[:200]}"
                except Exception:
                    pass
                yield f"data: {json.dumps({'token': '', 'error': err_text, 'done': True})}\n\n"
                return

            # Send model name to frontend
            yield f"data: {json.dumps({'model': MODEL_NAME, 'done': False})}\n\n"

            import json as json_mod
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json_mod.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        done = chunk.get("done", False)
                        if token:
                            yield f"data: {json_mod.dumps({'token': token, 'done': False})}\n\n"
                        if done:
                            yield f"data: {json_mod.dumps({'token': '', 'done': True})}\n\n"
                    except json_mod.JSONDecodeError:
                        continue

        except http_requests.ConnectionError:
            yield f"data: {json.dumps({'token': '[Ollama is not running. Start it with: ollama serve]', 'done': True})}\n\n"
        except http_requests.Timeout:
            yield f"data: {json.dumps({'token': '[Request timed out. The model may be loading — try again.]', 'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'[Error: {str(e)}]', 'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@api_bp.route('/chatbot/models', methods=['GET'])
def chatbot_models():
    """Check available Ollama models and return the auto-detected best model."""
    import requests as http_requests
    OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    try:
        resp = http_requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            active_model = _detect_best_model()
            return jsonify({
                'status': 'connected',
                'models': [m['name'] for m in models],
                'active_model': active_model
            })
        return jsonify({'status': 'error', 'message': f'Status {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'status': 'disconnected', 'message': str(e)}), 503
