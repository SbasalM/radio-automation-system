"""
Flask Application Factory
This file creates and configures your Flask web application
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler

# Create database instance (but don't initialize it yet)
db = SQLAlchemy()

def create_app(config_name=None):
    """
    Application factory function
    This creates a new Flask application instance with the specified configuration
    """
    # Create Flask app instance
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize database with app
    db.init_app(app)
    
    # Register blueprints (these organize your routes)
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Initialize default shows if database is empty
        from app.models import Show, ShowAlias
        if Show.query.count() == 0:
            initialize_default_shows()
    
    # Set up logging
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Set up rotating file handler (creates new log file when size limit reached)
        file_handler = RotatingFileHandler('logs/radio_automation.log',
                                         maxBytes=10240000,  # 10MB
                                         backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Radio Automation System startup')
    
    return app

def initialize_default_shows():
    """
    Populate database with some default radio shows
    This runs only when the database is first created
    """
    from app.models import Show, ShowAlias
    
    # Default shows to add
    default_shows = [
        {
            'name': 'Answers In Genesis',
            'aliases': ['AIG', 'AnswersInGenesis', 'Answers_In_Genesis'],
            'description': 'Daily radio program from Answers In Genesis ministry',
            'default_format': 'wav',
            'normalize': True
        },
        {
            'name': 'Focus On The Family',
            'aliases': ['FOF', 'FocusOnTheFamily', 'Focus_On_The_Family', 'FOTF'],
            'description': 'Focus on the Family daily broadcast',
            'default_format': 'wav',
            'normalize': True
        },
        {
            'name': 'Adventures In Odyssey',
            'aliases': ['AIO', 'Odyssey', 'AdventuresInOdyssey'],
            'description': 'Adventures in Odyssey radio drama',
            'default_format': 'wav',
            'normalize': True
        },
        {
            'name': 'Unshackled',
            'aliases': ['UNS', 'Unshackled!'],
            'description': 'Pacific Garden Mission presents Unshackled!',
            'default_format': 'wav',
            'normalize': True
        }
    ]
    
    # Add each show to the database
    for show_data in default_shows:
        # Create the show
        show = Show(
            name=show_data['name'],
            description=show_data['description'],
            default_format=show_data['default_format'],
            normalize=show_data['normalize']
        )
        db.session.add(show)
        db.session.flush()  # Get the show ID
        
        # Add aliases for this show
        for alias in show_data['aliases']:
            show_alias = ShowAlias(
                alias=alias.lower(),  # Store aliases in lowercase for easier matching
                show_id=show.id
            )
            db.session.add(show_alias)
    
    # Save all changes to database
    db.session.commit()
    print("Default shows initialized successfully!")