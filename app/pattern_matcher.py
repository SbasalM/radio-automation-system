"""
Pattern Matching Module for Radio Automation System
Extracts show names and dates from filenames
"""

import re
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def parse_filename(filename):
    """
    Parse a filename to extract show name and broadcast date
    
    Expected format: ShowName_MMDDYY.ext
    Examples:
        - AnswersInGenesis_100424.wav -> Answers In Genesis, Oct 4, 2024
        - FOF_123199.mp3 -> FOF (alias), Dec 31, 1999
        - AIG_010125.wav -> AIG (alias), Jan 1, 2025
    
    Args:
        filename: The filename to parse
        
    Returns:
        Dictionary with:
            - show_name: Extracted show name (may be an alias)
            - date: datetime.date object or None
            - year: Interpreted year (4 digits)
            - success: Boolean indicating if parsing was successful
            - error: Error message if parsing failed
    """
    result = {
        'show_name': None,
        'date': None,
        'year': None,
        'success': False,
        'error': None
    }
    
    try:
        # Remove file extension
        base_name = filename.rsplit('.', 1)[0]
        
        # Try different patterns
        patterns = [
            # Standard pattern: ShowName_MMDDYY
            r'^([A-Za-z]+(?:[A-Z][a-z]+)*)_(\d{6})$',
            # With spaces or underscores in show name
            r'^([A-Za-z_\s]+)_(\d{6})$',
            # With hyphens
            r'^([A-Za-z\-]+)_(\d{6})$',
            # Date with different separator
            r'^([A-Za-z]+(?:[A-Z][a-z]+)*)-(\d{6})$',
        ]
        
        match = None
        for pattern in patterns:
            match = re.match(pattern, base_name)
            if match:
                break
        
        if not match:
            result['error'] = "Filename doesn't match expected pattern (ShowName_MMDDYY)"
            return result
        
        # Extract show name and date string
        show_name_raw = match.group(1)
        date_str = match.group(2)
        
        # Process show name
        show_name = process_show_name(show_name_raw)
        result['show_name'] = show_name
        
        # Parse date (MMDDYY format)
        if len(date_str) == 6:
            month = int(date_str[0:2])
            day = int(date_str[2:4])
            year_short = int(date_str[4:6])
            
            # Interpret 2-digit year
            # 00-30 = 2000-2030, 31-99 = 1931-1999
            if year_short <= 30:
                year = 2000 + year_short
            else:
                year = 1900 + year_short
            
            result['year'] = year
            
            # Validate date
            try:
                parsed_date = date(year, month, day)
                result['date'] = parsed_date
                result['success'] = True
            except ValueError as e:
                result['error'] = f"Invalid date: {month}/{day}/{year}"
                result['success'] = False
        else:
            result['error'] = "Date must be 6 digits (MMDDYY)"
    
    except Exception as e:
        result['error'] = f"Error parsing filename: {str(e)}"
        logger.error(f"Error parsing {filename}: {str(e)}")
    
    return result

def process_show_name(raw_name):
    """
    Process raw show name extracted from filename
    Handles CamelCase, underscores, and common variations
    
    Args:
        raw_name: Raw show name string
        
    Returns:
        Processed show name suitable for matching
    """
    # First, replace underscores with spaces
    name = raw_name.replace('_', ' ')
    
    # Handle CamelCase by inserting spaces
    # But preserve common acronyms
    acronyms = ['AIG', 'FOF', 'BBN', 'AIO', 'FOTF', 'DJ', 'FM', 'AM', 'USA']
    
    # Check if entire name is an acronym
    if name.upper() in acronyms:
        return name.upper()
    
    # Insert spaces before capital letters (except at start)
    processed = ''
    for i, char in enumerate(name):
        if i > 0 and char.isupper() and name[i-1].islower():
            processed += ' '
        processed += char
    
    # Clean up multiple spaces
    processed = ' '.join(processed.split())
    
    # Standardize common variations
    standardizations = {
        'Answers In Genesis': ['AIG', 'AnswersInGenesis', 'Answers_In_Genesis'],
        'Focus On The Family': ['FOF', 'FOTF', 'FocusOnTheFamily', 'Focus_On_The_Family'],
        'Adventures In Odyssey': ['AIO', 'Odyssey', 'AdventuresInOdyssey'],
        'Bible Broadcasting Network': ['BBN', 'BibleBroadcastingNetwork'],
    }
    
    # Check if processed name matches any standardization
    for standard, variations in standardizations.items():
        if processed in variations or processed.lower() in [v.lower() for v in variations]:
            return standard
    
    return processed

def extract_date_from_string(text):
    """
    Try to extract a date from a string using various formats
    
    Args:
        text: String that might contain a date
        
    Returns:
        datetime.date object or None
    """
    # Common date patterns to try
    date_patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%m-%d-%Y'),  # MM/DD/YYYY or MM-DD-YYYY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})', '%m-%d-%y'),  # MM/DD/YY or MM-DD-YY
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y-%m-%d'),  # YYYY-MM-DD
        (r'(\d{8})', '%Y%m%d'),  # YYYYMMDD
        (r'(\d{6})', '%m%d%y'),  # MMDDYY
    ]
    
    for pattern, date_format in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                date_str = match.group(0)
                parsed_date = datetime.strptime(date_str, date_format).date()
                return parsed_date
            except ValueError:
                continue
    
    return None

def suggest_filename(show_name, broadcast_date, format='wav'):
    """
    Generate a standardized filename for a show
    
    Args:
        show_name: Name of the show
        broadcast_date: Date of broadcast (datetime.date object)
        format: File extension
        
    Returns:
        Suggested filename
    """
    # Convert show name to filename-friendly format
    safe_name = show_name.replace(' ', '')  # Remove spaces for CamelCase
    
    # Format date as MMDDYY
    date_str = broadcast_date.strftime('%m%d%y')
    
    return f"{safe_name}_{date_str}.{format}"

def find_show_by_pattern(filename, shows_list):
    """
    Try to find a matching show from a list based on filename
    
    Args:
        filename: Filename to match
        shows_list: List of Show objects with aliases
        
    Returns:
        Matched Show object or None
    """
    # Parse filename
    parse_result = parse_filename(filename)
    
    if not parse_result['show_name']:
        return None
    
    extracted_name = parse_result['show_name'].lower()
    
    # Check each show and its aliases
    for show in shows_list:
        # Check main name
        if show.name.lower() == extracted_name:
            return show
        
        # Check aliases
        for alias in show.get_aliases_list():
            if alias.lower() == extracted_name:
                return show
    
    # Try fuzzy matching if no exact match
    # This could be enhanced with more sophisticated matching
    for show in shows_list:
        if extracted_name in show.name.lower() or show.name.lower() in extracted_name:
            return show
    
    return None

def validate_pattern(pattern):
    """
    Validate a filename pattern for consistency
    
    Args:
        pattern: Filename pattern to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for required components
    if '_' not in pattern:
        return False, "Pattern must contain underscore separator"
    
    parts = pattern.split('_')
    if len(parts) != 2:
        return False, "Pattern must have exactly one underscore"
    
    show_part, date_part = parts
    
    # Validate show name part
    if not show_part or not re.match(r'^[A-Za-z]+$', show_part):
        return False, "Show name must contain only letters"
    
    # Validate date part (without extension)
    date_only = date_part.split('.')[0]
    if not re.match(r'^\d{6}$', date_only):
        return False, "Date must be exactly 6 digits (MMDDYY)"
    
    return True, None

# Compile common patterns for better performance
COMPILED_PATTERNS = {
    'standard': re.compile(r'^([A-Za-z]+(?:[A-Z][a-z]+)*)_(\d{6})$'),
    'with_spaces': re.compile(r'^([A-Za-z_\s]+)_(\d{6})$'),
    'with_hyphens': re.compile(r'^([A-Za-z\-]+)_(\d{6})$'),
}