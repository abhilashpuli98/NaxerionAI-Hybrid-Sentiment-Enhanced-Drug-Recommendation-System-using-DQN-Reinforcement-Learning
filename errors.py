"""Error Handling and Logging System for SEDRS"""

import logging
import json
from datetime import datetime
from flask import jsonify, request, current_app
from functools import wraps
import traceback

# Configure logging
def setup_logging(log_file='sedrs.log'):
    """Setup comprehensive logging system"""
    logger = logging.getLogger('sedrs')
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging('logs/sedrs.log')

class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(ApplicationError):
    """Validation error (400)"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 400, details)

class AuthenticationError(ApplicationError):
    """Authentication error (401)"""
    def __init__(self, message: str = "Authentication required", details: dict = None):
        super().__init__(message, 401, details)

class AuthorizationError(ApplicationError):
    """Authorization error (403)"""
    def __init__(self, message: str = "Insufficient permissions", details: dict = None):
        super().__init__(message, 403, details)

class NotFoundError(ApplicationError):
    """Resource not found error (404)"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, 404)

class ConflictError(ApplicationError):
    """Resource conflict error (409)"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 409, details)

class RateLimitError(ApplicationError):
    """Rate limit exceeded error (429)"""
    def __init__(self, retry_after: int = 300, details: dict = None):
        super().__init__("Rate limit exceeded", 429, details)
        self.retry_after = retry_after

class ServerError(ApplicationError):
    """Server error (500)"""
    def __init__(self, message: str = "Internal server error", details: dict = None):
        super().__init__(message, 500, details)

def error_response(error: ApplicationError) -> dict:
    """Convert error to JSON response"""
    return {
        'status': 'error',
        'code': error.status_code,
        'message': error.message,
        'timestamp': datetime.utcnow().isoformat(),
        'details': error.details if error.details else None
    }

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        logger.warning(f"Application error: {error.message}", extra={'details': error.details})
        response = error_response(error)
        return jsonify(response), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        logger.warning(f"Bad request: {error}")
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Bad request',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        logger.warning("Unauthorized access attempt")
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Unauthorized',
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        logger.warning("Forbidden access attempt")
        return jsonify({
            'status': 'error',
            'code': 403,
            'message': 'Forbidden',
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': 'Not found',
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        logger.warning(f"Method not allowed: {request.method} {request.path}")
        return jsonify({
            'status': 'error',
            'code': 405,
            'message': 'Method not allowed',
            'timestamp': datetime.utcnow().isoformat()
        }), 405
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        logger.warning(f"Rate limit exceeded for {request.remote_addr}")
        response = jsonify({
            'status': 'error',
            'code': 429,
            'message': 'Rate limit exceeded',
            'timestamp': datetime.utcnow().isoformat()
        })
        response.status_code = 429
        response.headers['Retry-After'] = '300'
        return response
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {error}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        db.session.rollback()
        logger.error(f"Unhandled exception: {error}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def log_request(f):
    """Decorator to log incoming requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_data = {
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.is_json:
                request_data['body'] = request.get_json(silent=True)
        
        logger.debug(f"Incoming request: {json.dumps(request_data)}")
        
        try:
            result = f(*args, **kwargs)
            logger.debug(f"Request completed: {request.path}")
            return result
        except Exception as error:
            logger.error(f"Request error: {request.path} - {error}")
            raise
    
    return decorated_function

def log_response(status_code: int = 200):
    """Decorator to log outgoing responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            if isinstance(response, tuple):
                data, code = response[0], response[1] if len(response) > 1 else 200
            else:
                data = response
                code = status_code
            
            logger.debug(f"Response: {request.path} - Status: {code}")
            return response
        
        return decorated_function
    return decorator

class RequestValidationError(ValidationError):
    """Invalid request format"""
    pass

def validate_json_request(f):
    """Decorator to validate JSON request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            raise ValidationError("Content-Type must be application/json")
        
        try:
            data = request.get_json()
            if not data:
                raise ValidationError("Request body cannot be empty")
        except Exception as error:
            logger.warning(f"Invalid JSON: {error}")
            raise ValidationError(f"Invalid JSON format: {str(error)}")
        
        return f(*args, **kwargs)
    return decorated_function

def catch_errors(f):
    """Generic error catching decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ApplicationError as error:
            logger.warning(f"Application error in {f.__name__}: {error.message}")
            return jsonify(error_response(error)), error.status_code
        except Exception as error:
            logger.error(f"Unexpected error in {f.__name__}: {str(error)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'code': 500,
                'message': 'Internal server error',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    return decorated_function
