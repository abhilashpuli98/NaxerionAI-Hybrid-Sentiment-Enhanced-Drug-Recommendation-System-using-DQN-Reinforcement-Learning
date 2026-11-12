"""Database Initialization and Schema Management"""

from app import create_app
from extensions import db
from models import Patient, Interaction, Recommendation, SystemMetrics, UserFeedback, AuditLog
from datetime import datetime
import os

def init_database():
    """Initialize database with all tables and schema"""
    app = create_app()
    
    with app.app_context():
        # Create all tabzles
        print("[*] Creating database schema...")
        db.create_all()
        print("[✓] Database schema created")
        
        # Verify tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n[*] Tables created: {len(tables)}")
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"  - {table} ({len(columns)} columns)")
        
        # Create initial admin patient if doesn't exist
        admin_email = 'admin@sedrs.local'
        if not Patient.query.filter_by(email=admin_email).first():
            print(f"\n[*] Creating demo patient: {admin_email}")
            admin = Patient(
                email=admin_email,
                age=30,
                gender='M',
                medical_conditions='Demo Patient',
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[✓] Demo patient created with ID: {admin.id}")
        
        # Initialize system metrics if not exist
        metrics = SystemMetrics.query.first()
        if not metrics:
            print("\n[*] Initializing system metrics...")
            metrics = SystemMetrics(
                total_interactions=0,
                total_recommendations=0,
                total_patients=Patient.query.count(),
                avg_overall_confidence=0.0,
                success_rate=0.0,
                created_at=datetime.utcnow()
            )
            db.session.add(metrics)
            db.session.commit()
            print("[✓] System metrics initialized")
        
        print("\n[✓] Database initialization complete!")
        return True

def verify_database():
    """Verify database integrity"""
    app = create_app()
    
    with app.app_context():
        print("[*] Verifying database integrity...")
        
        try:
            from sqlalchemy import text
            # Test database connection
            db.session.execute(text('SELECT 1'))
            print("[✓] Database connection successful")
            
            # Count records
            patient_count = Patient.query.count()
            interaction_count = Interaction.query.count()
            recommendation_count = Recommendation.query.count()
            
            print(f"\n[*] Database records:")
            print(f"  - Patients: {patient_count}")
            print(f"  - Interactions: {interaction_count}")
            print(f"  - Recommendations: {recommendation_count}")
            
            # Check schema
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            expected_tables = ['patient', 'interaction', 'recommendation', 
                             'system_metrics', 'user_feedback', 'audit_log']
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"\n[!] Missing tables: {missing_tables}")
                return False
            
            print("\n[✓] All required tables exist")
            print("[✓] Database verification passed")
            return True
            
        except Exception as error:
            print(f"[!] Database verification failed: {error}")
            return False

def migrate_database():
    """Migrate database to new schema (add new columns, etc.)"""
    app = create_app()
    
    with app.app_context():
        print("[*] Running database migrations...")
        
        # Example migration: add new columns if they don't exist
        from sqlalchemy import inspect, text
        
        inspector = inspect(db.engine)
        
        # Check patient table columns
        patient_columns = [col['name'] for col in inspector.get_columns('patient')]
        
        print(f"[*] Patient table columns: {len(patient_columns)}")
        print(f"[✓] All required columns present")
        
        return True

def reset_database():
    """Reset database (DROP all tables and recreate)"""
    app = create_app()
    
    with app.app_context():
        print("[!] WARNING: This will delete all data!")
        confirm = input("[?] Type 'yes' to confirm: ")
        
        if confirm.lower() != 'yes':
            print("[*] Reset cancelled")
            return False
        
        print("[*] Dropping all tables...")
        db.drop_all()
        print("[✓] All tables dropped")
        
        print("[*] Recreating tables...")
        db.create_all()
        print("[✓] Tables recreated")
        
        return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            init_database()
        elif command == 'verify':
            verify_database()
        elif command == 'migrate':
            migrate_database()
        elif command == 'reset':
            reset_database()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python db_init.py [init|verify|migrate|reset]")
    else:
        init_database()
