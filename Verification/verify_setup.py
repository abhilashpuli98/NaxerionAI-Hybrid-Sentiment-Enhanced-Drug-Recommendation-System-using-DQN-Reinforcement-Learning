from app import create_app
from extensions import db
from models import Patient

try:
    print("Creating app...")
    app = create_app()
    print("App created.")
    
    with app.app_context():
        from sqlalchemy import text
        print("Checking database connection...")
        db.session.execute(text('SELECT 1'))
        print("Database connected.")
        
        print("Querying Patient model...")
        count = Patient.query.count()
        print(f"Patient count: {count}")
        
    print("Verification successful!")
except Exception as e:
    print(f"Verification FAILED: {e}")
    import traceback
    traceback.print_exc()
