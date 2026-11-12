"""Seed script to create default admin user for SEDRS"""

import os

from app import create_app
from extensions import db
from models import Patient

def seed_admin():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = Patient.query.filter_by(email='admin@sedrs.com').first()
        if admin:
            print('Admin user already exists.')
            return

        admin = Patient(
            email='admin@sedrs.com',
            role='admin',
            age=0,
            gender='O',
            medical_conditions='N/A',
            allergies='N/A'
        )
        password = os.environ.get('SEDRS_ADMIN_PASSWORD')
        if not password:
            raise RuntimeError(
                'Set SEDRS_ADMIN_PASSWORD to a strong, unique password before seeding an admin.'
            )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()
        print(f'Admin user created: admin@sedrs.com (ID: {admin.id})')

if __name__ == '__main__':
    seed_admin()
