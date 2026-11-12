#!/usr/bin/env python3
"""Minimal database initialization without ML model loading"""

import ssl
import os
import sys
import certifi

# Set proper SSL certificate configuration
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()

# Create app and initialize database
def init_database_minimal():
    """Initialize database schema without loading ML models"""
    try:
        print("[*] Creating Flask app...")
        from app import create_app, db
        from models import Patient, SystemMetrics
        
        app = create_app()
        
        with app.app_context():
            print("[*] Database already initialized during app creation")
            print("[*] Verifying database tables...")
            
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"[✓] Found {len(tables)} tables: {', '.join(tables)}")
            
            # Initialize system metrics if empty
            if SystemMetrics.query.first() is None:
                print("[*] Initializing system metrics...")
                metrics = SystemMetrics(
                    total_interactions=0,
                    total_recommendations=0,
                    total_patients=0,
                    avg_text_accuracy=0.94,
                    avg_audio_accuracy=0.918,
                    avg_image_accuracy=0.893,
                    avg_overall_confidence=0.90,
                    response_time_ms=0.0,
                    error_count=0,
                    success_rate=0.90
                )
                db.session.add(metrics)
                db.session.commit()
                print("[✓] System metrics initialized")
            
            # Create demo admin patient if none exists
            if Patient.query.filter_by(email='admin@sedrs.local').first() is None:
                print("[*] Creating demo admin patient...")
                admin = Patient(
                    email='admin@sedrs.local',
                    age=30,
                    gender='M',
                    medical_conditions='Demonstration Account',
                    allergies='None documented',
                    current_medications='None'
                )
                db.session.add(admin)
                db.session.commit()
                print("[✓] Demo patient created: admin@sedrs.local")
            
            print("[✓] Database initialization completed successfully")
            print(f"[✓] Database file: instance/sedrs.db")
            
    except Exception as e:
        print(f"[✗] Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("[*] SEDRS Database Initialization (Minimal Mode - No ML Models)")
    init_database_minimal()
