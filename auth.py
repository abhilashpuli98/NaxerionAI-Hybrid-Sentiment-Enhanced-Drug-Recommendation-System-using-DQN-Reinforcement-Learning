"""Authentication and Authorization System for SEDRS"""

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, jsonify, request
import secrets
import hashlib

from app import db
from models import Patient

login_manager = LoginManager()
login_manager.login_view = 'web.login'
login_manager.login_message_category = 'info'

class AuthenticationManager:
    """Comprehensive authentication management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using werkzeug"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(hash, password)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple:
        """Validate password meets security requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(char.isupper() for char in password):
            errors.append("Password must contain uppercase letter")
        if not any(char.islower() for char in password):
            errors.append("Password must contain lowercase letter")
        if not any(char.isdigit() for char in password):
            errors.append("Password must contain digit")
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
            errors.append("Password must contain special character")
        
        return len(errors) == 0, errors

class PatientUser(UserMixin):
    """User model for Flask-Login integration"""
    
    def __init__(self, patient):
        self.id = patient.id
        self.email = patient.email
        self.patient = patient
        self.is_active = True
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    """Load user from database"""
    try:
        patient = Patient.query.get(int(user_id))
        if patient:
            return PatientUser(patient)
    except (ValueError, TypeError):
        pass
    return None

def require_auth(f):
    """Decorator for routes requiring authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(role: str):
    """Decorator for role-based access control"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check role (add role logic to Patient model if needed)
            if hasattr(current_user.patient, 'role'):
                if current_user.patient.role != role:
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_key(f):
    """Decorator for API key validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (implement based on your needs)
        valid_key = current_app.config.get('VALID_API_KEYS', [])
        if api_key not in valid_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

class SessionManager:
    """Session management and security"""
    
    @staticmethod
    def create_session(patient_id: int, ip_address: str, user_agent: str) -> dict:
        """Create secure session"""
        session_data = {
            'patient_id': patient_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=24),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'last_activity': datetime.utcnow()
        }
        return session_data
    
    @staticmethod
    def validate_session(session_data: dict) -> bool:
        """Validate session is still active"""
        if not session_data:
            return False
        
        expires_at = session_data.get('expires_at')
        if not expires_at or expires_at < datetime.utcnow():
            return False
        
        return True
    
    @staticmethod
    def update_last_activity(session_data: dict) -> dict:
        """Update last activity timestamp"""
        session_data['last_activity'] = datetime.utcnow()
        return session_data

class RateLimiter:
    """Rate limiting to prevent abuse"""
    
    def __init__(self):
        self.attempts = {}
    
    def is_rate_limited(self, identifier: str, max_attempts: int = 5, 
                       window_seconds: int = 300) -> bool:
        """Check if identifier exceeds rate limit"""
        now = datetime.utcnow()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Remove old attempts outside the window
        self.attempts[identifier] = [
            timestamp for timestamp in self.attempts[identifier]
            if (now - timestamp).total_seconds() < window_seconds
        ]
        
        if len(self.attempts[identifier]) >= max_attempts:
            return True
        
        # Record this attempt
        self.attempts[identifier].append(now)
        return False
    
    def get_remaining_attempts(self, identifier: str, max_attempts: int = 5) -> int:
        """Get remaining attempts for identifier"""
        if identifier not in self.attempts:
            return max_attempts
        
        return max(0, max_attempts - len(self.attempts[identifier]))

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_attempts: int = 5, window_seconds: int = 300):
    """Decorator for rate limiting routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr  # Use IP address as identifier
            
            if rate_limiter.is_rate_limited(identifier, max_attempts, window_seconds):
                remaining = rate_limiter.get_remaining_attempts(identifier, max_attempts)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'remaining_attempts': remaining,
                    'retry_after': window_seconds
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class CORSManager:
    """CORS (Cross-Origin Resource Sharing) management"""
    
    ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5000',
    ]
    
    ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
    
    ALLOWED_HEADERS = [
        'Content-Type',
        'Authorization',
        'X-API-Key',
        'X-Requested-With'
    ]
    
    @staticmethod
    def is_origin_allowed(origin: str) -> bool:
        """Check if origin is allowed"""
        # Allow localhost in development
        if origin in CORSManager.ALLOWED_ORIGINS:
            return True
        
        # Check environment configuration
        if current_app.config.get('ALLOW_ORIGINS'):
            return origin in current_app.config['ALLOW_ORIGINS']
        
        return False

class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        for header, value in SecurityHeaders.HEADERS.items():
            response.headers[header] = value
        return response
