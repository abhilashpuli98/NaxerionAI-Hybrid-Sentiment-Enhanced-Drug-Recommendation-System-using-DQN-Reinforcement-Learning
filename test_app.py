#!/usr/bin/env python3
"""Test script to diagnose app issues"""

import sys
import traceback

try:
    print("[1] Importing app...")
    from app import create_app, db
    print("[OK] App module imported")
    
    print("\n[2] Creating Flask app...")
    app = create_app()
    print("[OK] Flask app created")
    
    print("\n[3] Testing app context...")
    with app.app_context():
        print("[OK] App context available")
        
        print("\n[4] Checking database...")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"[OK] Database tables exist: {len(tables)} tables")
        print(f"     Tables: {tables}\n")
        
        print("[5] Testing a query...")
        from models import Patient
        patient_count = Patient.query.count()
        print(f"[OK] Query successful, {patient_count} patients found\n")
    
    print("[SUCCESS] All diagnostics passed!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
