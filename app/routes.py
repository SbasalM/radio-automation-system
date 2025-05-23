"""
Web Routes for Radio Automation System
These functions handle web page requests and form submissions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models import Show, ShowAlias, ProcessedFile, ProcessingTemplate
from app.audio_processor import process_audio_file
from app.pattern_matcher import parse_filename
from app.utils import allowed_file, get_file_info
import os
from datetime import datetime
import time

# Create a blueprint (a way to organize routes)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """
    Home page - shows system overview and recent activity
    """
    # Get statistics for dashboard
    total_shows = Show.query.count()
    total_files = ProcessedFile.query.count()
    recent_files = ProcessedFile.query.order_by(
        ProcessedFile.processed_at.desc()
    ).limit(5).all()
    
    # Calculate success rate
    successful_files = ProcessedFile.query.filter_by(success=True).count()
    success_rate = (successful_files / total_files * 100) if total_files > 0 else 0
    
    return render_template('index.html',
                         total_shows=total_shows,
                         total_files=total_files,
                         recent_files=recent_files,
                         success_rate=round(success_rate, 1))

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    File upload page - handles single and multiple file uploads
    """
    if request.method == 'POST':
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        # Get processing options from form
        normalize = request.form.get('normalize', 'on') == 'on'
        output_format = request.form.get('format', 'wav')
        
        processed_count = 0
        error_count = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Save uploaded file
                upload_path = os.path.join('uploads', filename)
                file.save(upload_path)
                
                try:
                    # Process the file
                    result = process_audio_file(
                        upload_path,
                        output_format=output_format,
                        normalize=normalize
                    )
                    
                    if result['success']:
                        processed_count += 1
                        flash(f'Successfully processed: {filename}', 'success')
                    else:
                        error_count += 1
                        flash(f'Error processing {filename}: {result["error"]}', 'error')
                        
                except Exception as e:
                    error_count += 1
                    flash(f'Error processing {filename}: {str(e)}', 'error')
            else:
                error_count += 1
                flash(f'Invalid file type: {file.filename}', 'error')
        
        # Summary message
        if processed_count > 0:
            flash(f'Successfully processed {processed_count} file(s)', 'info')
        if error_count > 0:
            flash(f'{error_count} file(s) had errors', 'warning')
            
        return redirect(url_for('main.history'))
    
    # GET request - show upload form
    return render_template('upload.html')

@main_bp.route('/shows')
def shows():
    """
    Show management page - list all radio shows
    """
    all_shows = Show.query.order_by(Show.name).all()
    return render_template('shows.html', shows=all_shows)

@main_bp.route('/shows/add', methods=['GET', 'POST'])
def add_show():
    """
    Add a new radio show
    """
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        aliases = request.form.get('aliases', '').strip()
        
        # Validate
        if not name:
            flash('Show name is required', 'error')
            return redirect(request.url)
        
        # Check if show already exists
        existing = Show.query.filter_by(name=name).first()
        if existing:
            flash('A show with this name already exists', 'error')
            return redirect(request.url)
        
        # Create new show
        show = Show(
            name=name,
            description=description,
            default_format=request.form.get('format', 'wav'),
            sample_rate=int(request.form.get('sample_rate', 44100)),
            bit_depth=int(request.form.get('bit_depth', 16)),
            channels=int(request.form.get('channels', 2)),
            normalize=request.form.get('normalize', 'on') == 'on',
            normalize_level=float(request.form.get('normalize_level', -1.0))
        )
        
        db.session.add(show)
        db.session.flush()  # Get the show ID
        
        # Add aliases
        if aliases:
            for alias in aliases.split(','):
                alias = alias.strip()
                if alias:
                    show_alias = ShowAlias(
                        alias=alias.lower(),
                        show_id=show.id
                    )
                    db.session.add(show_alias)
        
        db.session.commit()
        flash(f'Show "{name}" added successfully!', 'success')
        return redirect(url_for('main.shows'))
    
    # GET request - show form
    return render_template('add_show.html')

@main_bp.route('/shows/<int:show_id>/edit', methods=['GET', 'POST'])
def edit_show(show_id):
    """
    Edit an existing show
    """
    show = Show.query.get_or_404(show_id)
    
    if request.method == 'POST':
        # Update show details
        show.name = request.form.get('name', show.name).strip()
        show.description = request.form.get('description', '').strip()
        show.default_format = request.form.get('format', 'wav')
        show.sample_rate = int(request.form.get('sample_rate', 44100))
        show.bit_depth = int(request.form.get('bit_depth', 16))
        show.channels = int(request.form.get('channels', 2))
        show.normalize = request.form.get('normalize', 'on') == 'on'
        show.normalize_level = float(request.form.get('normalize_level', -1.0))
        
        db.session.commit()
        flash(f'Show "{show.name}" updated successfully!', 'success')
        return redirect(url_for('main.shows'))
    
    # GET request - show form with current values
    return render_template('edit_show.html', show=show)

@main_bp.route('/shows/<int:show_id>/delete', methods=['POST'])
def delete_show(show_id):
    """
    Delete a show (with confirmation)
    """
    show = Show.query.get_or_404(show_id)
    
    # Check if show has processed files
    if show.processed_files.count() > 0:
        flash(f'Cannot delete "{show.name}" - it has processed files. '
              'Consider deactivating it instead.', 'error')
        return redirect(url_for('main.shows'))
    
    db.session.delete(show)
    db.session.commit()
    flash(f'Show "{show.name}" deleted successfully!', 'success')
    return redirect(url_for('main.shows'))

@main_bp.route('/history')
def history():
    """
    File processing history page
    """
    # Get page number from query string
    page = request.args.get('page', 1, type=int)
    per_page = 25  # Files per page
    
    # Query with pagination
    pagination = ProcessedFile.query.order_by(
        ProcessedFile.processed_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    files = pagination.items
    
    return render_template('history.html', 
                         files=files,
                         pagination=pagination)

@main_bp.route('/settings')
def settings():
    """
    System settings page
    """
    templates = ProcessingTemplate.query.all()
    return render_template('settings.html', templates=templates)

@main_bp.route('/api/parse-filename', methods=['POST'])
def api_parse_filename():
    """
    API endpoint to parse filename and return extracted information
    Used for real-time feedback in the upload form
    """
    data = request.get_json()
    filename = data.get('filename', '')
    
    result = parse_filename(filename)
    
    return jsonify(result)

@main_bp.route('/api/file-info/<int:file_id>')
def api_file_info(file_id):
    """
    API endpoint to get detailed file information
    """
    file = ProcessedFile.query.get_or_404(file_id)
    
    return jsonify({
        'id': file.id,
        'original_filename': file.original_filename,
        'show_name': file.show.name if file.show else 'Unknown',
        'date': file.get_formatted_date(),
        'duration': file.get_duration_string(),
        'size_mb': file.get_file_size_mb(),
        'format': file.original_format,
        'sample_rate': file.original_sample_rate,
        'bit_depth': file.original_bit_depth,
        'channels': file.original_channels,
        'processed_at': file.processed_at.strftime('%Y-%m-%d %H:%M:%S'),
        'success': file.success,
        'error_message': file.error_message
    })

@main_bp.route('/download/<int:file_id>')
def download_file(file_id):
    """
    Download a processed file
    """
    file = ProcessedFile.query.get_or_404(file_id)
    
    if not file.output_filename or not os.path.exists(file.output_filename):
        flash('Processed file not found', 'error')
        return redirect(url_for('main.history'))
    
    return send_file(file.output_filename, as_attachment=True)

# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500