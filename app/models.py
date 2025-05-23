"""
Database Models for Radio Automation System
These classes define the structure of data we store in the database
"""

from app import db
from datetime import datetime

class Show(db.Model):
    """
    Represents a radio show in the system
    Each show can have multiple aliases and processing settings
    """
    __tablename__ = 'shows'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing settings for this show
    default_format = db.Column(db.String(10), default='wav')  # wav, mp3, aiff, flac
    sample_rate = db.Column(db.Integer, default=44100)  # Hz
    bit_depth = db.Column(db.Integer, default=16)  # bits
    channels = db.Column(db.Integer, default=2)  # 1=mono, 2=stereo
    normalize = db.Column(db.Boolean, default=True)
    normalize_level = db.Column(db.Float, default=-1.0)  # dB
    
    # Output settings
    output_folder = db.Column(db.String(500))  # Custom output folder for this show
    filename_pattern = db.Column(db.String(200))  # Custom filename pattern
    
    # Relationships
    aliases = db.relationship('ShowAlias', backref='show', lazy='dynamic', 
                            cascade='all, delete-orphan')
    processed_files = db.relationship('ProcessedFile', backref='show', lazy='dynamic')
    
    def __repr__(self):
        return f'<Show {self.name}>'
    
    def get_aliases_list(self):
        """Return a list of all aliases for this show"""
        return [alias.alias for alias in self.aliases]
    
    def add_alias(self, alias_text):
        """Add a new alias for this show"""
        # Check if alias already exists
        existing = ShowAlias.query.filter_by(alias=alias_text.lower()).first()
        if existing:
            return False, "Alias already exists"
        
        new_alias = ShowAlias(alias=alias_text.lower(), show_id=self.id)
        db.session.add(new_alias)
        return True, "Alias added successfully"

class ShowAlias(db.Model):
    """
    Alternative names for shows (e.g., 'AIG' for 'Answers In Genesis')
    Used for pattern matching in filenames
    """
    __tablename__ = 'show_aliases'
    
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(100), nullable=False, unique=True, index=True)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShowAlias {self.alias} -> {self.show.name}>'

class ProcessedFile(db.Model):
    """
    Record of every file processed by the system
    Tracks original file info, processing settings, and output
    """
    __tablename__ = 'processed_files'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Original file information
    original_filename = db.Column(db.String(500), nullable=False)
    original_format = db.Column(db.String(10))
    original_size = db.Column(db.Integer)  # bytes
    original_duration = db.Column(db.Float)  # seconds
    original_sample_rate = db.Column(db.Integer)  # Hz
    original_bit_depth = db.Column(db.Integer)  # bits
    original_channels = db.Column(db.Integer)  # 1 or 2
    
    # Extracted information
    extracted_date = db.Column(db.Date)  # Date extracted from filename
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'))
    
    # Processing information
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    processing_time = db.Column(db.Float)  # seconds
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Output file information
    output_filename = db.Column(db.String(500))
    output_format = db.Column(db.String(10))
    output_size = db.Column(db.Integer)  # bytes
    normalized = db.Column(db.Boolean, default=False)
    normalize_level = db.Column(db.Float)  # dB
    
    # User who processed the file (for future multi-user support)
    processed_by = db.Column(db.String(100), default='system')
    
    def __repr__(self):
        return f'<ProcessedFile {self.original_filename}>'
    
    def get_formatted_date(self):
        """Return the extracted date in a readable format"""
        if self.extracted_date:
            return self.extracted_date.strftime('%B %d, %Y')
        return 'Unknown Date'
    
    def get_duration_string(self):
        """Return duration in MM:SS format"""
        if self.original_duration:
            minutes = int(self.original_duration // 60)
            seconds = int(self.original_duration % 60)
            return f"{minutes}:{seconds:02d}"
        return "Unknown"
    
    def get_file_size_mb(self):
        """Return file size in MB"""
        if self.original_size:
            return round(self.original_size / (1024 * 1024), 2)
        return 0

class ProcessingTemplate(db.Model):
    """
    Reusable processing templates for common tasks
    Users can save their favorite processing settings
    """
    __tablename__ = 'processing_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Processing settings
    output_format = db.Column(db.String(10), default='wav')
    sample_rate = db.Column(db.Integer, default=44100)
    bit_depth = db.Column(db.Integer, default=16)
    channels = db.Column(db.Integer, default=2)
    normalize = db.Column(db.Boolean, default=True)
    normalize_level = db.Column(db.Float, default=-1.0)
    
    # Additional processing options
    remove_dc_offset = db.Column(db.Boolean, default=False)
    fade_in_ms = db.Column(db.Integer, default=0)  # milliseconds
    fade_out_ms = db.Column(db.Integer, default=0)  # milliseconds
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProcessingTemplate {self.name}>'