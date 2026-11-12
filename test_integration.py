"""Integration Testing Suite for SEDRS"""

import unittest
import json
from datetime import datetime
from app import create_app, db
from models import Patient, Interaction, Recommendation
from validators import SEDRSValidator
import tempfile
import os

class SEDRSTestCase(unittest.TestCase):
    """Base test case for SEDRS"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self.add_test_data()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def add_test_data(self):
        """Add test data to database"""
        test_patient = Patient(
            email='test@example.com',
            age=30,
            gender='M',
            medical_conditions='Test condition',
            created_at=datetime.utcnow()
        )
        db.session.add(test_patient)
        db.session.commit()
        self.test_patient_id = test_patient.id

class PatientAPITests(SEDRSTestCase):
    """Test patient API endpoints"""
    
    def test_create_patient(self):
        """Test patient creation"""
        data = {
            'email': 'newpatient@example.com',
            'age': 25,
            'gender': 'F',
            'medical_conditions': 'Test'
        }
        
        response = self.client.post('/api/patients', 
                                   json=data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        result = json.loads(response.data)
        self.assertEqual(result['email'], 'newpatient@example.com')
    
    def test_get_patient(self):
        """Test getting patient details"""
        response = self.client.get(f'/api/patients/{self.test_patient_id}')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['email'], 'test@example.com')
    
    def test_get_nonexistent_patient(self):
        """Test getting nonexistent patient"""
        response = self.client.get('/api/patients/99999')
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_patient(self):
        """Test patient update"""
        data = {
            'age': 35,
            'allergies': 'Updated allergies'
        }
        
        response = self.client.put(f'/api/patients/{self.test_patient_id}',
                                  json=data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['age'], 35)

class ValidationTests(unittest.TestCase):
    """Test input validation"""
    
    def test_email_validation_valid(self):
        """Test valid email validation"""
        valid, error = SEDRSValidator.validate_email('test@example.com')
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_email_validation_invalid(self):
        """Test invalid email validation"""
        valid, error = SEDRSValidator.validate_email('invalid-email')
        self.assertFalse(valid)
        self.assertIsNotNone(error)
    
    def test_age_validation_valid(self):
        """Test valid age"""
        valid, error = SEDRSValidator.validate_age(30)
        self.assertTrue(valid)
    
    def test_age_validation_invalid(self):
        """Test invalid age"""
        valid, error = SEDRSValidator.validate_age(200)
        self.assertFalse(valid)
    
    def test_gender_validation(self):
        """Test gender validation"""
        valid, error = SEDRSValidator.validate_gender('M')
        self.assertTrue(valid)
        
        valid, error = SEDRSValidator.validate_gender('Invalid')
        self.assertFalse(valid)
    
    def test_text_validation_xss(self):
        """Test XSS detection in text"""
        dangerous_text = 'Hello <script>alert("xss")</script>'
        valid, error = SEDRSValidator.validate_text_input(dangerous_text)
        self.assertFalse(valid)
    
    def test_condition_validation(self):
        """Test condition validation"""
        valid, error = SEDRSValidator.validate_condition('Hypertension')
        self.assertTrue(valid)
        
        valid, error = SEDRSValidator.validate_condition('123')
        self.assertFalse(valid)
    
    def test_patient_data_validation_complete(self):
        """Test complete patient data validation"""
        data = {
            'email': 'test@example.com',
            'age': 30,
            'gender': 'M',
            'medical_conditions': 'Test condition'
        }
        
        valid, errors = SEDRSValidator.validate_patient_data(data)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
    
    def test_patient_data_validation_missing_email(self):
        """Test patient validation with missing email"""
        data = {
            'age': 30,
            'gender': 'M'
        }
        
        valid, errors = SEDRSValidator.validate_patient_data(data)
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)

class AnalysisTests(SEDRSTestCase):
    """Test analysis functionality"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['status'], 'operational')
    
    def test_analysis_input_validation(self):
        """Test analysis input validation"""
        data = {
            'patient_id': self.test_patient_id,
            'condition': 'Migraine',
            'text_input': 'I have been experiencing migraines'
        }
        
        valid, errors = SEDRSValidator.validate_analysis_input(data)
        self.assertTrue(valid)
    
    def test_get_metrics(self):
        """Test system metrics endpoint"""
        response = self.client.get('/api/metrics')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertIn('total_patients', result)

class DatabaseTests(SEDRSTestCase):
    """Test database operations"""
    
    def test_patient_creation(self):
        """Test patient model"""
        with self.app.app_context():
            patient = Patient(
                email='dbtest@example.com',
                age=40,
                gender='F'
            )
            
            db.session.add(patient)
            db.session.commit()
            
            retrieved = Patient.query.filter_by(email='dbtest@example.com').first()
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.age, 40)
    
    def test_patient_relationships(self):
        """Test patient-interaction relationships"""
        with self.app.app_context():
            patient = Patient.query.first()
            
            interaction = Interaction(
                patient_id=patient.id,
                condition='Test',
                text_sentiment=0.8,  # Use float instead of string
                text_confidence=0.9,
                overall_confidence=0.9,
                created_at=datetime.utcnow()
            )
            
            db.session.add(interaction)
            db.session.commit()
            
            retrieved_patient = Patient.query.get(patient.id)
            self.assertEqual(len(retrieved_patient.interactions), 1)
            self.assertEqual(retrieved_patient.interactions[0].condition, 'Test')

class DataIntegrityTests(SEDRSTestCase):
    """Test data integrity constraints"""
    
    def test_duplicate_email_prevention(self):
        """Test duplicate email prevention"""
        # This test would require unique constraint on email
        # If not implemented in the model, it should be added
        
        with self.app.app_context():
            # Try to create duplicate email (should fail or be handled)
            patient1 = Patient(
                email='unique@example.com',
                age=30,
                gender='M',
                created_at=datetime.utcnow()
            )
            db.session.add(patient1)
            db.session.commit()
            
            # Attempting to create duplicate
            patient2 = Patient(
                email='unique@example.com',
                age=25,
                gender='F',
                created_at=datetime.utcnow()
            )
            db.session.add(patient2)
            
            # This should raise an integrity error
            with self.assertRaises(Exception):
                db.session.commit()
            
            db.session.rollback()

class PerformanceTests(SEDRSTestCase):
    """Test system performance"""
    
    def test_large_query_handling(self):
        """Test handling of large data queries"""
        with self.app.app_context():
            # Create multiple patients
            for i in range(100):
                patient = Patient(
                    email=f'perf_test_{i}@example.com',
                    age=20 + i,
                    gender='M' if i % 2 == 0 else 'F',
                    created_at=datetime.utcnow()
                )
                db.session.add(patient)
            
            db.session.commit()
            
            # Query all patients
            patients = Patient.query.all()
            self.assertEqual(len(patients), 101)  # 100 + 1 from setUp

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(PatientAPITests))
    suite.addTests(loader.loadTestsFromTestCase(ValidationTests))
    suite.addTests(loader.loadTestsFromTestCase(AnalysisTests))
    suite.addTests(loader.loadTestsFromTestCase(DatabaseTests))
    suite.addTests(loader.loadTestsFromTestCase(DataIntegrityTests))
    suite.addTests(loader.loadTestsFromTestCase(PerformanceTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
