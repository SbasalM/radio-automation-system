"""
Utility functions for Radio Automation System
Helper functions used throughout the application
"""

import os
import subprocess
import json
from werkzeug.utils import secure_filename
from flask import current_app
import mutagen
from mutagen.wave import WAVE
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """
    Check if a filename has an allowed audio file extension
    
    Args:
        filename: Name of the file to check
        
    Returns:
        Boolean indicating if file type is allowed
    """
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', 
                                               {'wav', 'mp3', 'aiff', 'flac', 'm4a'})
    return extension in allowed_extensions

def get_file_info(file_path):
    """
    Extract metadata and technical information from an audio file
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary with file information:
            - success: Boolean indicating if analysis was successful
            - format: File format (wav, mp3, etc.)
            - duration: Duration in seconds
            - sample_rate: Sample rate in Hz
            - bit_depth: Bit depth (if available)
            - channels: Number of channels
            - bitrate: Bitrate in kbps (for compressed formats)
            - size: File size in bytes
            - error: Error message if analysis failed
    """
    result = {
        'success': False,
        'format': None,
        'duration': None,
        'sample_rate': None,
        'bit_depth': None,
        'channels': None,
        'bitrate': None,
        'size': None,
        'error': None
    }
    
    try:
        # Get file size
        result['size'] = os.path.getsize(file_path)
        
        # Get format from extension
        extension = os.path.splitext(file_path)[1].lower().lstrip('.')
        result['format'] = extension
        
        # Try to load file with mutagen
        audio = mutagen.File(file_path)
        
        if audio is None:
            # Fall back to FFmpeg if mutagen can't read it
            return get_file_info_ffmpeg(file_path)
        
        # Get duration
        if hasattr(audio.info, 'length'):
            result['duration'] = audio.info.length
        
        # Get sample rate
        if hasattr(audio.info, 'sample_rate'):
            result['sample_rate'] = audio.info.sample_rate
        
        # Get channels
        if hasattr(audio.info, 'channels'):
            result['channels'] = audio.info.channels
        
        # Get bitrate (for compressed formats)
        if hasattr(audio.info, 'bitrate'):
            result['bitrate'] = audio.info.bitrate
        
        # Get bit depth (mainly for WAV/AIFF)
        if isinstance(audio, WAVE):
            if hasattr(audio.info, 'bits_per_sample'):
                result['bit_depth'] = audio.info.bits_per_sample
        
        result['success'] = True
        
    except Exception as e:
        logger.error(f"Error analyzing file {file_path} with mutagen: {str(e)}")
        # Try FFmpeg as fallback
        return get_file_info_ffmpeg(file_path)
    
    return result

def get_file_info_ffmpeg(file_path):
    """
    Get file information using FFmpeg/FFprobe as fallback
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary with file information
    """
    result = {
        'success': False,
        'format': None,
        'duration': None,
        'sample_rate': None,
        'bit_depth': None,
        'channels': None,
        'bitrate': None,
        'size': None,
        'error': None
    }
    
    try:
        # Get file size
        result['size'] = os.path.getsize(file_path)
        
        # Use ffprobe to get detailed information
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        output = subprocess.check_output(cmd, text=True)
        data = json.loads(output)
        
        # Extract format info
        if 'format' in data:
            format_info = data['format']
            result['duration'] = float(format_info.get('duration', 0))
            result['bitrate'] = int(format_info.get('bit_rate', 0))
            result['format'] = format_info.get('format_name', '').split(',')[0]
        
        # Extract stream info (audio stream)
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                result['sample_rate'] = int(stream.get('sample_rate', 0))
                result['channels'] = int(stream.get('channels', 0))
                
                # Try to determine bit depth
                if 'bits_per_sample' in stream:
                    result['bit_depth'] = int(stream['bits_per_sample'])
                elif 'bits_per_raw_sample' in stream:
                    result['bit_depth'] = int(stream['bits_per_raw_sample'])
                
                break
        
        result['success'] = True
        
    except subprocess.CalledProcessError as e:
        result['error'] = f"FFprobe error: {e}"
        logger.error(f"FFprobe error for {file_path}: {e}")
    except Exception as e:
        result['error'] = f"Error analyzing file: {str(e)}"
        logger.error(f"Error analyzing file {file_path}: {str(e)}")
    
    return result

def format_duration(seconds):
    """
    Format duration from seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "3:45" or "1:02:30")
    """
    if seconds is None or seconds < 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def format_file_size(bytes):
    """
    Format file size from bytes to human-readable string
    
    Args:
        bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if bytes is None or bytes < 0:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    
    return f"{bytes:.1f} TB"

def ensure_directories():
    """
    Ensure all required directories exist
    Creates directories if they don't exist
    """
    directories = [
        'uploads',
        'processed',
        'logs',
        'instance',  # For SQLite database
        'static/css',
        'static/js',
        'static/images',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

def clean_old_files(directory, days=7):
    """
    Remove files older than specified number of days
    
    Args:
        directory: Directory to clean
        days: Number of days to keep files
    """
    import time
    
    now = time.time()
    cutoff = now - (days * 24 * 60 * 60)  # Convert days to seconds
    
    removed_count = 0
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
            
            # Check file age
            file_modified = os.path.getmtime(file_path)
            if file_modified < cutoff:
                os.remove(file_path)
                removed_count += 1
                logger.info(f"Removed old file: {filename}")
        
        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} old files from {directory}")
            
    except Exception as e:
        logger.error(f"Error cleaning old files from {directory}: {str(e)}")

def check_ffmpeg_installed():
    """
    Check if FFmpeg is installed and accessible
    
    Returns:
        Tuple of (is_installed, version_string)
    """
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            # Extract version from output
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        else:
            return False, None
            
    except FileNotFoundError:
        return False, None
    except Exception as e:
        logger.error(f"Error checking FFmpeg: {str(e)}")
        return False, None

def validate_processing_options(options):
    """
    Validate audio processing options
    
    Args:
        options: Dictionary of processing options
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Validate sample rate
    sample_rate = options.get('sample_rate', 44100)
    valid_sample_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88200, 96000]
    if sample_rate not in valid_sample_rates:
        errors.append(f"Invalid sample rate: {sample_rate}. Must be one of {valid_sample_rates}")
    
    # Validate bit depth
    bit_depth = options.get('bit_depth', 16)
    valid_bit_depths = [8, 16, 24, 32]
    if bit_depth not in valid_bit_depths:
        errors.append(f"Invalid bit depth: {bit_depth}. Must be one of {valid_bit_depths}")
    
    # Validate channels
    channels = options.get('channels', 2)
    if channels not in [1, 2]:
        errors.append(f"Invalid channels: {channels}. Must be 1 (mono) or 2 (stereo)")
    
    # Validate normalize level
    normalize_level = options.get('normalize_level', -1.0)
    if normalize_level > 0:
        errors.append(f"Normalize level must be negative (dB below full scale)")
    if normalize_level < -30:
        errors.append(f"Normalize level too low: {normalize_level}. Should be between -30 and 0")
    
    # Validate format
    format = options.get('format', 'wav')
    valid_formats = ['wav', 'mp3', 'aiff', 'flac', 'm4a']
    if format not in valid_formats:
        errors.append(f"Invalid format: {format}. Must be one of {valid_formats}")
    
    return len(errors) == 0, errors

def generate_unique_filename(base_name, extension, directory):
    """
    Generate a unique filename if file already exists
    
    Args:
        base_name: Base filename without extension
        extension: File extension
        directory: Directory where file will be saved
        
    Returns:
        Unique filename
    """
    filename = f"{base_name}.{extension}"
    file_path = os.path.join(directory, filename)
    
    # If file doesn't exist, return original
    if not os.path.exists(file_path):
        return filename
    
    # Add number suffix until we find a unique name
    counter = 1
    while True:
        filename = f"{base_name}_{counter}.{extension}"
        file_path = os.path.join(directory, filename)
        
        if not os.path.exists(file_path):
            return filename
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 1000:
            raise ValueError("Could not generate unique filename")