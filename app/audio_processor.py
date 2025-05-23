"""
Audio Processing Module for Radio Automation System
Handles audio file analysis, conversion, and processing
"""

import os
import subprocess
import json
from datetime import datetime
import time
from app import db
from app.models import ProcessedFile, Show
from app.pattern_matcher import parse_filename
from app.utils import get_file_info
import logging

logger = logging.getLogger(__name__)

def process_audio_file(input_path, output_format='wav', normalize=True, 
                      normalize_level=-1.0, sample_rate=44100, 
                      bit_depth=16, channels=2):
    """
    Process an audio file according to specified parameters
    
    Args:
        input_path: Path to input audio file
        output_format: Output format (wav, mp3, aiff, flac)
        normalize: Whether to normalize audio
        normalize_level: Target normalization level in dB
        sample_rate: Output sample rate in Hz
        bit_depth: Output bit depth (8, 16, 24, 32)
        channels: Output channels (1=mono, 2=stereo)
    
    Returns:
        Dictionary with success status and file information
    """
    start_time = time.time()
    
    try:
        # Get input file information
        file_info = get_file_info(input_path)
        if not file_info['success']:
            return {
                'success': False,
                'error': f"Could not analyze input file: {file_info.get('error', 'Unknown error')}"
            }
        
        # Parse filename to extract show and date
        filename = os.path.basename(input_path)
        parse_result = parse_filename(filename)
        
        # Find matching show in database
        show = None
        if parse_result['show_name']:
            # Try to find show by alias
            from app.models import ShowAlias
            alias = ShowAlias.query.filter_by(
                alias=parse_result['show_name'].lower()
            ).first()
            if alias:
                show = alias.show
                # Use show's default settings if not overridden
                if show:
                    output_format = output_format or show.default_format
                    sample_rate = sample_rate or show.sample_rate
                    bit_depth = bit_depth or show.bit_depth
                    channels = channels or show.channels
                    if normalize is None:
                        normalize = show.normalize
                    normalize_level = normalize_level or show.normalize_level
        
        # Create output filename
        base_name = os.path.splitext(filename)[0]
        if show and parse_result['date']:
            # Use standardized naming
            output_name = f"{show.name.replace(' ', '_')}_{parse_result['date'].strftime('%Y%m%d')}"
        else:
            output_name = base_name
        
        output_filename = f"{output_name}.{output_format}"
        output_path = os.path.join('processed', output_filename)
        
        # Ensure output directory exists
        os.makedirs('processed', exist_ok=True)
        
        # Build FFmpeg command
        ffmpeg_cmd = build_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            output_format=output_format,
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            channels=channels,
            normalize=normalize,
            normalize_level=normalize_level
        )
        
        # Execute FFmpeg
        logger.info(f"Processing: {filename} -> {output_filename}")
        logger.debug(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr[-1000:] if result.stderr else "Unknown FFmpeg error"
            logger.error(f"FFmpeg error: {error_msg}")
            return {
                'success': False,
                'error': f"FFmpeg processing failed: {error_msg}"
            }
        
        # Get output file information
        output_info = get_file_info(output_path)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Save to database
        processed_file = ProcessedFile(
            original_filename=filename,
            original_format=file_info['format'],
            original_size=file_info['size'],
            original_duration=file_info['duration'],
            original_sample_rate=file_info['sample_rate'],
            original_bit_depth=file_info['bit_depth'],
            original_channels=file_info['channels'],
            extracted_date=parse_result['date'],
            show_id=show.id if show else None,
            processing_time=processing_time,
            success=True,
            output_filename=output_path,
            output_format=output_format,
            output_size=output_info['size'] if output_info['success'] else None,
            normalized=normalize,
            normalize_level=normalize_level if normalize else None
        )
        
        db.session.add(processed_file)
        db.session.commit()
        
        logger.info(f"Successfully processed {filename} in {processing_time:.2f} seconds")
        
        return {
            'success': True,
            'output_path': output_path,
            'output_filename': output_filename,
            'processing_time': processing_time,
            'file_id': processed_file.id
        }
        
    except Exception as e:
        logger.error(f"Error processing {input_path}: {str(e)}")
        
        # Save failed attempt to database
        try:
            processed_file = ProcessedFile(
                original_filename=os.path.basename(input_path),
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
            db.session.add(processed_file)
            db.session.commit()
        except:
            pass
        
        return {
            'success': False,
            'error': str(e)
        }

def build_ffmpeg_command(input_path, output_path, output_format='wav',
                        sample_rate=44100, bit_depth=16, channels=2,
                        normalize=True, normalize_level=-1.0):
    """
    Build FFmpeg command for audio processing
    """
    cmd = ['ffmpeg', '-y', '-i', input_path]
    
    # Audio codec based on format
    if output_format == 'wav':
        # PCM codec for WAV
        if bit_depth == 8:
            cmd.extend(['-acodec', 'pcm_u8'])
        elif bit_depth == 16:
            cmd.extend(['-acodec', 'pcm_s16le'])
        elif bit_depth == 24:
            cmd.extend(['-acodec', 'pcm_s24le'])
        elif bit_depth == 32:
            cmd.extend(['-acodec', 'pcm_s32le'])
    elif output_format == 'mp3':
        cmd.extend(['-acodec', 'libmp3lame', '-b:a', '320k'])
    elif output_format == 'aiff':
        cmd.extend(['-acodec', 'pcm_s16be'])
    elif output_format == 'flac':
        cmd.extend(['-acodec', 'flac'])
    
    # Sample rate
    cmd.extend(['-ar', str(sample_rate)])
    
    # Channels
    cmd.extend(['-ac', str(channels)])
    
    # Normalization
    if normalize:
        # Use loudnorm filter for better normalization
        cmd.extend([
            '-af',
            f'loudnorm=I={normalize_level}:TP=-1.5:LRA=11'
        ])
    
    # Output file
    cmd.append(output_path)
    
    return cmd

def analyze_audio_levels(file_path):
    """
    Analyze audio levels using FFmpeg
    Returns peak and RMS levels
    """
    try:
        cmd = [
            'ffmpeg', '-i', file_path,
            '-af', 'astats=metadata=1:reset=1',
            '-f', 'null', '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse output for levels
        levels = {
            'peak_db': None,
            'rms_db': None
        }
        
        # Extract levels from stderr (FFmpeg outputs to stderr)
        for line in result.stderr.split('\n'):
            if 'Peak level' in line:
                try:
                    levels['peak_db'] = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
            elif 'RMS level' in line:
                try:
                    levels['rms_db'] = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
        
        return levels
        
    except Exception as e:
        logger.error(f"Error analyzing levels for {file_path}: {str(e)}")
        return None

def batch_process_files(file_paths, **processing_options):
    """
    Process multiple files with the same settings
    
    Args:
        file_paths: List of file paths to process
        **processing_options: Processing parameters (format, normalize, etc.)
    
    Returns:
        List of results for each file
    """
    results = []
    
    for file_path in file_paths:
        result = process_audio_file(file_path, **processing_options)
        results.append({
            'file': os.path.basename(file_path),
            'success': result['success'],
            'error': result.get('error'),
            'output': result.get('output_filename')
        })
    
    return results

def convert_to_broadcast_wav(input_path, output_path, metadata=None):
    """
    Convert audio to Broadcast WAV format with cart chunk metadata
    Used for radio automation systems like iMediaTouch
    
    Args:
        input_path: Input audio file
        output_path: Output BWF file path
        metadata: Dictionary with cart chunk fields (title, artist, etc.)
    """
    # This is a placeholder for BWF conversion
    # In production, you would use a library like `wave` or `soundfile`
    # to write proper cart chunks
    
    # For now, use standard WAV conversion
    return build_ffmpeg_command(
        input_path=input_path,
        output_path=output_path,
        output_format='wav',
        bit_depth=16,
        sample_rate=44100
    )

def validate_audio_file(file_path):
    """
    Validate that a file is a valid audio file
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Use FFmpeg to probe the file
        cmd = ['ffmpeg', '-i', file_path, '-f', 'null', '-']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, None
        else:
            # Check for common errors
            stderr = result.stderr.lower()
            if 'invalid data' in stderr:
                return False, "Invalid or corrupted audio file"
            elif 'no such file' in stderr:
                return False, "File not found"
            else:
                return False, "Not a valid audio file"
                
    except Exception as e:
        return False, f"Validation error: {str(e)}"