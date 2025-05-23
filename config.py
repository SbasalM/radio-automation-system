"""
Configuration settings for Radio Workflow Automation System
This file contains all the settings that control how your application works
"""

import os

class Config:
    """Base configuration class with settings used across all environments"""
    
    # Secret key for session security - in production, use a random string
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    # SQLite is a simple database that stores everything in a single file
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///radio_automation.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = 'uploads'
    PROCESSED_FOLDER = 'processed'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max file size
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'aiff', 'flac', 'm4a'}
    
    # Audio processing defaults
    DEFAULT_SAMPLE_RATE = 44100  # CD quality
    DEFAULT_BIT_DEPTH = 16       # Standard for radio
    DEFAULT_CHANNELS = 2         # Stereo
    DEFAULT_NORMALIZE_LEVEL = -1.0  # dB below full scale
    
    # Date parsing configuration
    # For year interpretation in MMDDYY format
    YEAR_CUTOFF = 30  # Years 00-30 = 2000-2030, 31-99 = 1931-1999
    
    # Show name aliases - maps short names to full names
    DEFAULT_SHOW_ALIASES = {
        'AIG': 'Answers In Genesis',
        'FOF': 'Focus On The Family',
        'BBN': 'Bible Broadcasting Network',
        # Add more aliases as needed
    }
    
    # Pagination
    FILES_PER_PAGE = 25
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_FILE = 'logs/radio_automation.log'

class DevelopmentConfig(Config):
    """Development environment specific configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production environment specific configuration"""
    DEBUG = False
    TESTING = False
    
    # In production, you might want to use PostgreSQL instead of SQLite
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing environment specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory database for tests

# Dictionary to easily access configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}