"""Input Validation and Sanitization for SEDRS"""

import re
import json
from typing import Dict, Any, List, Tuple, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

class ValidationError(Exception):
    """Custom validation exception"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class SEDRSValidator:
    """Comprehensive validation system for SEDRS"""
    
    # Configuration
    MAX_EMAIL_LENGTH = 255
    MAX_TEXT_LENGTH = 10000
    MAX_CONDITION_LENGTH = 500
    MAX_FILENAME_LENGTH = 255
    
    ALLOWED_AUDIO_EXT = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}
    ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email or len(email) > SEDRSValidator.MAX_EMAIL_LENGTH:
            return False, "Invalid email length"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_age(age: int) -> Tuple[bool, Optional[str]]:
        """Validate patient age"""
        if not isinstance(age, int):
            return False, "Age must be integer"
        if age < 0 or age > 150:
            return False, "Age must be between 0 and 150"
        return True, None
    
    @staticmethod
    def validate_gender(gender: str) -> Tuple[bool, Optional[str]]:
        """Validate gender field"""
        valid_genders = {'M', 'F', 'O', 'Prefer not to say'}
        if gender not in valid_genders:
            return False, f"Gender must be one of {valid_genders}"
        return True, None
    
    @staticmethod
    def validate_text_input(text: str, max_length: int = None) -> Tuple[bool, Optional[str]]:
        """Validate text input"""
        if max_length is None:
            max_length = SEDRSValidator.MAX_TEXT_LENGTH
        
        if not text or not isinstance(text, str):
            return False, "Text must be non-empty string"
        
        if len(text) > max_length:
            return False, f"Text exceeds maximum length of {max_length}"
        
        # Check for XSS attempts
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=', 'onclick=']
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in dangerous_patterns):
            return False, "Text contains dangerous content"
        
        return True, None
    
    @staticmethod
    def validate_condition(condition: str) -> Tuple[bool, Optional[str]]:
        """Validate medical condition input"""
        if not condition or len(condition) > SEDRSValidator.MAX_CONDITION_LENGTH:
            return False, "Invalid condition length"
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', condition):
            return False, "Condition must contain letters"
        
        return True, None
    
    @staticmethod
    def validate_audio_file(file: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validate audio file"""
        if not file or file.filename == '':
            return False, "No audio file provided"
        
        filename = secure_filename(file.filename)
        if len(filename) > SEDRSValidator.MAX_FILENAME_LENGTH:
            return False, "Filename too long"
        
        # Check extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in SEDRSValidator.ALLOWED_AUDIO_EXT:
            return False, f"Audio format not allowed. Allowed: {SEDRSValidator.ALLOWED_AUDIO_EXT}"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to start
        
        if file_size > SEDRSValidator.MAX_AUDIO_SIZE:
            return False, f"Audio file exceeds {SEDRSValidator.MAX_AUDIO_SIZE / 1024 / 1024}MB limit"
        
        if file_size == 0:
            return False, "Audio file is empty"
        
        return True, None
    
    @staticmethod
    def validate_image_file(file: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validate image file"""
        if not file or file.filename == '':
            return False, "No image file provided"
        
        filename = secure_filename(file.filename)
        if len(filename) > SEDRSValidator.MAX_FILENAME_LENGTH:
            return False, "Filename too long"
        
        # Check extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in SEDRSValidator.ALLOWED_IMAGE_EXT:
            return False, f"Image format not allowed. Allowed: {SEDRSValidator.ALLOWED_IMAGE_EXT}"
        
        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > SEDRSValidator.MAX_IMAGE_SIZE:
            return False, f"Image exceeds {SEDRSValidator.MAX_IMAGE_SIZE / 1024 / 1024}MB limit"
        
        if file_size == 0:
            return False, "Image file is empty"
        
        return True, None
    
    @staticmethod
    def validate_patient_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Comprehensive patient data validation"""
        errors = []
        
        # Email validation
        if 'email' in data:
            valid, error = SEDRSValidator.validate_email(data['email'])
            if not valid:
                errors.append(f"Email: {error}")
        else:
            errors.append("Email: Required field")
        
        # Age validation
        if 'age' in data and data['age'] is not None:
            valid, error = SEDRSValidator.validate_age(data['age'])
            if not valid:
                errors.append(f"Age: {error}")
        
        # Gender validation
        if 'gender' in data and data['gender']:
            valid, error = SEDRSValidator.validate_gender(data['gender'])
            if not valid:
                errors.append(f"Gender: {error}")
        
        # Medical conditions
        if 'medical_conditions' in data and data['medical_conditions']:
            valid, error = SEDRSValidator.validate_text_input(data['medical_conditions'], 1000)
            if not valid:
                errors.append(f"Medical conditions: {error}")
        
        # Allergies
        if 'allergies' in data and data['allergies']:
            valid, error = SEDRSValidator.validate_text_input(data['allergies'], 1000)
            if not valid:
                errors.append(f"Allergies: {error}")
        
        # Current medications
        if 'current_medications' in data and data['current_medications']:
            valid, error = SEDRSValidator.validate_text_input(data['current_medications'], 1000)
            if not valid:
                errors.append(f"Current medications: {error}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_analysis_input(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate analysis input data"""
        errors = []
        
        # Condition
        if 'condition' not in data or not data['condition']:
            errors.append("Condition: Required field")
        else:
            valid, error = SEDRSValidator.validate_condition(data['condition'])
            if not valid:
                errors.append(f"Condition: {error}")
        
        # Text input (optional)
        if 'text_input' in data and data['text_input']:
            valid, error = SEDRSValidator.validate_text_input(data['text_input'])
            if not valid:
                errors.append(f"Text input: {error}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_feedback_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate feedback submission"""
        errors = []
        
        # Rating
        if 'rating' not in data:
            errors.append("Rating: Required field")
        else:
            try:
                rating = int(data['rating'])
                if rating < 1 or rating > 5:
                    errors.append("Rating: Must be between 1 and 5")
            except (ValueError, TypeError):
                errors.append("Rating: Must be integer")
        
        # Effectiveness
        if 'effectiveness' in data and data['effectiveness']:
            valid_values = {'Not Effective', 'Somewhat Effective', 'Very Effective'}
            if data['effectiveness'] not in valid_values:
                errors.append(f"Effectiveness: Must be one of {valid_values}")
        
        # Adverse effects
        if 'adverse_effects' in data and data['adverse_effects']:
            valid, error = SEDRSValidator.validate_text_input(data['adverse_effects'])
            if not valid:
                errors.append(f"Adverse effects: {error}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security"""
        return secure_filename(filename)
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input"""
        # Remove null bytes
        text = text.replace('\x00', '')
        # Remove control characters except newline, tab, carriage return
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        return text.strip()


class JSONValidator:
    """JSON validation for API responses"""
    
    @staticmethod
    def validate_json(data: Any) -> bool:
        """Check if data is valid JSON serializable"""
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_response_structure(response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate standard response structure"""
        required_keys = {'status', 'data'}
        
        if not isinstance(response, dict):
            return False, "Response must be dictionary"
        
        if not all(key in response for key in required_keys):
            return False, f"Response missing required keys: {required_keys}"
        
        if response['status'] not in {'success', 'error', 'warning'}:
            return False, "Status must be success, error, or warning"
        
        return True, None
