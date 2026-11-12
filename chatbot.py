"""Interactive Chatbot for Patient Engagement"""

import json
from datetime import datetime

class MedicalChatbot:
    """Chatbot for patient interaction and data collection"""
    
    def __init__(self):
        self.conversation_history = []
        self.patient_profile = {
            'name': '',
            'age': 0,
            'conditions': [],
            'allergies': [],
            'current_medications': [],
            'feedback_history': []
        }
        self.questionnaire_state = 0
        
    def start_conversation(self):
        """Start conversation with patient"""
        greeting = "Hello! Welcome to the Personalized Drug Recommendation System. I'm here to help find the best medication for your needs."
        self._log_message('bot', greeting)
        return greeting
    
    def ask_name(self):
        """Ask for patient name"""
        question = "What is your name?"
        self._log_message('bot', question)
        return question
    
    def ask_age(self):
        """Ask for patient age"""
        question = "How old are you?"
        self._log_message('bot', question)
        return question
    
    def ask_condition(self):
        """Ask for medical condition"""
        question = "What is the primary health condition you're seeking treatment for? (e.g., pain, fever, infection, diabetes)"
        self._log_message('bot', question)
        return question
    
    def ask_allergies(self):
        """Ask about allergies"""
        question = "Do you have any known allergies to medications? Please list them, or say 'none'."
        self._log_message('bot', question)
        return question
    
    def ask_current_medications(self):
        """Ask about current medications"""
        question = "Are you currently taking any other medications? Please list them, or say 'none'."
        self._log_message('bot', question)
        return question
    
    def ask_for_review(self, drug_name):
        """Ask for review on recommended drug"""
        question = f"Please provide a review of {drug_name}. Tell me how you feel about this medication (positive/negative feedback)."
        self._log_message('bot', question)
        return question
    
    def ask_for_audio_input(self):
        """Request audio input from patient"""
        message = "Please record your feedback about the recommended medication. Speak naturally about how you feel, any side effects, and your overall experience."
        self._log_message('bot', message)
        return message
    
    def ask_for_image(self):
        """Request drug image from patient"""
        message = "Please upload an image of the medication package or pill to verify its authenticity."
        self._log_message('bot', message)
        return message
    
    def process_user_input(self, user_input, current_stage):
        """
        Process user input based on conversation stage
        
        Args:
            user_input: user's response
            current_stage: current stage in questionnaire
        
        Returns:
            updated profile and next question
        """
        self._log_message('user', user_input)
        
        if current_stage == 'name':
            self.patient_profile['name'] = user_input
            self.questionnaire_state = 1
            return self.ask_age()
        
        elif current_stage == 'age':
            try:
                self.patient_profile['age'] = int(user_input)
                self.questionnaire_state = 2
                return self.ask_condition()
            except ValueError:
                return "Please enter a valid age (numeric value)."
        
        elif current_stage == 'condition':
            self.patient_profile['conditions'] = [user_input]
            self.questionnaire_state = 3
            return self.ask_allergies()
        
        elif current_stage == 'allergies':
            if user_input.lower() != 'none':
                self.patient_profile['allergies'] = [a.strip() for a in user_input.split(',')]
            self.questionnaire_state = 4
            return self.ask_current_medications()
        
        elif current_stage == 'medications':
            if user_input.lower() != 'none':
                self.patient_profile['current_medications'] = [m.strip() for m in user_input.split(',')]
            self.questionnaire_state = 5
            
            # Summary message
            summary = f"Thank you for the information! I will analyze your condition and provide personalized recommendations."
            self._log_message('bot', summary)
            return {
                'status': 'profile_complete',
                'next_action': 'sentiment_analysis',
                'profile': self.patient_profile,
                'message': summary
            }
        
        return "I didn't understand. Please try again."
    
    def collect_feedback(self, drug_name, user_feedback):
        """Collect patient feedback on recommendation"""
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'drug_name': drug_name,
            'feedback': user_feedback,
            'satisfaction': self._extract_satisfaction(user_feedback)
        }
        self.patient_profile['feedback_history'].append(feedback_entry)
        
        acknowledgment = f"Thank you for your feedback on {drug_name}. This helps us improve our recommendations."
        self._log_message('bot', acknowledgment)
        return acknowledgment
    
    def _extract_satisfaction(self, feedback):
        """Extract satisfaction level from feedback text"""
        positive_words = ['good', 'great', 'excellent', 'helpful', 'works', 'better', 'improved', 'happy']
        negative_words = ['bad', 'poor', 'terrible', 'ineffective', 'worse', 'side effects', 'unhappy', 'disappointed']
        
        feedback_lower = feedback.lower()
        
        positive_score = sum(1 for word in positive_words if word in feedback_lower)
        negative_score = sum(1 for word in negative_words if word in feedback_lower)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _log_message(self, sender, message):
        """Log conversation message"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'sender': sender,
            'message': message
        })
    
    def get_conversation_history(self):
        """Get conversation history"""
        return self.conversation_history
    
    def export_patient_profile(self):
        """Export patient profile as JSON"""
        return json.dumps(self.patient_profile, indent=2, default=str)
    
    def reset_conversation(self):
        """Reset conversation for new patient"""
        self.conversation_history = []
        self.patient_profile = {
            'name': '',
            'age': 0,
            'conditions': [],
            'allergies': [],
            'current_medications': [],
            'feedback_history': []
        }
        self.questionnaire_state = 0

class ConversationManager:
    """Manages multiple conversations and sessions"""
    
    def __init__(self):
        self.sessions = {}
        self.session_counter = 0
    
    def create_session(self):
        """Create new conversation session"""
        session_id = f"session_{self.session_counter}"
        self.sessions[session_id] = MedicalChatbot()
        self.session_counter += 1
        return session_id
    
    def get_session(self, session_id):
        """Get conversation session"""
        return self.sessions.get(session_id)
    
    def end_session(self, session_id):
        """End conversation session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_all_sessions(self):
        """Get all active sessions"""
        return self.sessions
