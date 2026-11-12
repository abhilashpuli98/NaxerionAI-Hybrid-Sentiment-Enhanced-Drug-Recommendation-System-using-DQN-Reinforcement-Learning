"""Database Models for SEDRS System"""

from extensions import db
from datetime import datetime
import json

class Patient(db.Model):
    """Patient information model"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), default='patient')  # 'admin' or 'patient'
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    medical_conditions = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    interactions = db.relationship('Interaction', backref='patient', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Interaction(db.Model):
    """Patient-system interaction model"""
    __tablename__ = 'interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    condition = db.Column(db.String(255))
    text_input = db.Column(db.Text)
    audio_file = db.Column(db.String(255))
    image_file = db.Column(db.String(255))
    
    text_sentiment = db.Column(db.Float)
    text_confidence = db.Column(db.Float)
    audio_emotion = db.Column(db.String(50))
    audio_confidence = db.Column(db.Float)
    image_validity = db.Column(db.String(50))
    image_confidence = db.Column(db.Float)
    
    sentiment_label = db.Column(db.String(50))  # positive, negative, neutral
    sentiment_score = db.Column(db.Float)
    
    fused_score = db.Column(db.Float)
    overall_confidence = db.Column(db.Float)
    
    # JSON-serialized multimodal confidence vector for RL and analysis
    multimodal_confidences = db.Column(db.Text)  # JSON: {"text": [logits], "audio": [probs], "image": [probs]}
    rl_state_json = db.Column(db.Text)  # JSON: DQN state vector used for this interaction
    
    result_json = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processed_at = db.Column(db.DateTime)
    
    recommendations = db.relationship('Recommendation', backref='interaction', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'condition': self.condition,
            'text_sentiment': self.text_sentiment,
            'audio_emotion': self.audio_emotion,
            'fused_score': self.fused_score,
            'overall_confidence': self.overall_confidence,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class Recommendation(db.Model):
    """Drug recommendation model"""
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    interaction_id = db.Column(db.Integer, db.ForeignKey('interactions.id'), nullable=False)
    
    drug_id = db.Column(db.Integer)
    drug_name = db.Column(db.String(255), index=True)
    category = db.Column(db.String(100))
    score = db.Column(db.Float)
    base_rating = db.Column(db.Float)
    confidence = db.Column(db.Float)
    
    rank = db.Column(db.Integer)
    composite_score = db.Column(db.Float)   # overall recommendation score
    efficacy_score = db.Column(db.Float)    # predicted efficacy
    sentiment_score = db.Column(db.Float)   # sentiment impact on score
    side_effects = db.Column(db.Text)
    reason = db.Column(db.Text)  # "Why this drug is recommended"
    
    user_feedback = db.Column(db.Integer)  # 1-5 rating
    feedback_date = db.Column(db.DateTime)
    effectiveness = db.Column(db.String(50))  # effective, moderate, ineffective
    adverse_effects = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'drug_name': self.drug_name,
            'category': self.category,
            'score': self.score,
            'confidence': self.confidence,
            'rank': self.rank,
            'user_feedback': self.user_feedback,
            'effectiveness': self.effectiveness
        }

class SystemMetrics(db.Model):
    """System performance metrics"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    total_interactions = db.Column(db.Integer, default=0)
    total_recommendations = db.Column(db.Integer, default=0)
    total_patients = db.Column(db.Integer, default=0)
    
    avg_text_accuracy = db.Column(db.Float)
    avg_audio_accuracy = db.Column(db.Float)
    avg_image_accuracy = db.Column(db.Float)
    avg_overall_confidence = db.Column(db.Float)
    
    response_time_ms = db.Column(db.Float)
    error_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_interactions': self.total_interactions,
            'avg_overall_confidence': self.avg_overall_confidence,
            'response_time_ms': self.response_time_ms,
            'success_rate': self.success_rate
        }

class UserFeedback(db.Model):
    """User feedback on system"""
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    
    rating = db.Column(db.Integer)  # 1-5
    comment = db.Column(db.Text)
    category = db.Column(db.String(100))  # accuracy, usability, speed, etc
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'category': self.category,
            'created_at': self.created_at.isoformat()
        }

class AuditLog(db.Model):
    """Audit trail for system actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255))
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.Integer)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'resource_type': self.resource_type,
            'created_at': self.created_at.isoformat()
        }
