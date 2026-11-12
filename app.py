"""Flask Application Factory and Configuration"""

import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

import logging
from flask import Flask, has_request_context, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from extensions import db

from config import Config

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static',
                instance_relative_config=True)
    
    # Load configuration
    app.config.from_object(Config)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Use absolute path for SQLite DB inside instance folder to avoid path issues
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    else:
        db_path = os.path.join(app.instance_path, 'sedrs.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize Flask extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Setup logging
    setup_logging(app)
    
    # Import and register blueprints AFTER db initialization
    with app.app_context():
        from api_routes import api_bp
        from web_routes import web_bp
        
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(web_bp)
        
        # Error handlers
        register_error_handlers(app)
        
        # Context processor
        app.context_processor(lambda: {'now': datetime.now()})
        
        # Database initialization
        db.create_all()
    
    return app

def setup_logging(app):
    """Configure logging"""
    if not app.debug:
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.FileHandler('logs/sedrs.log')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SEDRS Application Started')

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'message': str(error)}, 400
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server error: {error}')
        return {'error': 'Internal server error', 'message': 'An error occurred'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled exception: {error}')
        return {'error': 'Error', 'message': str(error)}, 500

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
