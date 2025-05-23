# Radio Workflow Automation System

A comprehensive web-based application for automating audio file processing, organization, and metadata management for radio stations.

## 🎯 Overview

This system automates the tedious daily tasks of processing audio files for radio broadcast, saving stations 2-3 hours of manual work per day. It handles file format conversion, audio normalization, intelligent file naming, and metadata management.

### Key Features

- **Intelligent File Processing**: Automatically recognizes show names and broadcast dates from filenames
- **Audio Normalization**: Ensures consistent volume levels across all content
- **Format Conversion**: Supports WAV, MP3, AIFF, FLAC, and M4A formats
- **Show Management**: Organize content by radio shows with custom processing settings
- **Web Interface**: User-friendly interface accessible from any browser
- **Batch Processing**: Handle multiple files at once
- **Processing History**: Track all processed files with detailed logs

## 📋 Requirements

- Python 3.8 or higher
- FFmpeg (for audio processing)
- 4GB RAM minimum
- 10GB+ free disk space for file storage

## 🚀 Quick Start Guide

### Step 1: Install Python

If you don't have Python installed:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Mac**: Install via Homebrew: `brew install python3`
- **Linux**: Use your package manager: `sudo apt-get install python3`

### Step 2: Install FFmpeg

FFmpeg is required for audio processing:

**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

### Step 3: Set Up the Application

1. **Create a project folder** (e.g., `radio-automation`)
2. **Save all the provided files** in the correct folder structure:

```
radio-automation/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── audio_processor.py
│   ├── pattern_matcher.py
│   └── utils.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── shows.html
│   ├── add_show.html
│   ├── edit_show.html
│   ├── history.html
│   ├── settings.html
│   ├── 404.html
│   └── 500.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── uploads/
├── processed/
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

3. **Open a terminal/command prompt** in the project folder

4. **Create a virtual environment** (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

5. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python run.py
```

The application will start and display:
```
* Running on http://127.0.0.1:5000
```

Open your web browser and go to: **http://localhost:5000**

## 📖 User Guide

### First Time Setup

1. **Access the Dashboard**: Open http://localhost:5000 in your browser
2. **Add Your First Show**:
   - Click "Shows" in the navigation
   - Click "Add New Show"
   - Enter show details (e.g., "Focus On The Family")
   - Add aliases (e.g., "FOF", "FOTF")
   - Configure audio settings
   - Click "Create Show"

### Processing Audio Files

1. **Go to Upload Page**: Click "Upload Files" in the navigation
2. **Select Files**: 
   - Drag and drop audio files onto the upload area
   - Or click "Browse Files" to select files
3. **Configure Settings**:
   - Choose output format (WAV recommended for radio)
   - Enable/disable normalization
   - Adjust other settings as needed
4. **Process Files**: Click "Process Files"
5. **Download Results**: Go to "History" to download processed files

### File Naming Convention

The system expects files named like: `ShowName_MMDDYY.ext`

Examples:
- `FocusOnTheFamily_102324.wav` → Focus On The Family, Oct 23, 2024
- `AIG_010125.mp3` → Answers In Genesis, Jan 1, 2025

### Understanding Show Aliases

Aliases help the system recognize abbreviated show names:
- If your files are named `FOF_102324.wav`
- Add "FOF" as an alias for "Focus On The Family"
- The system will automatically match and organize files

## 🔧 Configuration

### Basic Settings

Edit `config.py` to customize:
- File size limits
- Allowed file formats
- Default audio settings
- Storage locations

### Advanced Configuration

For production deployment:
1. Change `SECRET_KEY` in `config.py`
2. Switch to PostgreSQL database
3. Configure proper file storage paths
4. Set up automatic cleanup schedules

## 🐛 Troubleshooting

### Common Issues

**"FFmpeg not found" error**
- Ensure FFmpeg is installed and in your system PATH
- Test by running `ffmpeg -version` in terminal

**"No module named 'flask'" error**
- Activate your virtual environment
- Run `pip install -r requirements.txt` again

**Files not processing**
- Check file format is supported (WAV, MP3, AIFF, FLAC, M4A)
- Ensure filename follows pattern: `ShowName_MMDDYY.ext`
- Verify the show exists in the system

**Web page not loading**
- Ensure the application is running (`python run.py`)
- Check no other application is using port 5000
- Try accessing http://127.0.0.1:5000 instead of localhost

### Getting Help

1. Check the application logs in the `logs/` folder
2. Look for error messages in the terminal
3. Verify all files are in the correct folders

## 📁 Project Structure

```
app/                    # Main application code
├── __init__.py        # Application factory
├── models.py          # Database models
├── routes.py          # Web routes/pages
├── audio_processor.py # Audio processing logic
├── pattern_matcher.py # Filename parsing
└── utils.py          # Helper functions

templates/             # HTML templates
├── base.html         # Base layout
├── index.html        # Dashboard
├── upload.html       # File upload page
├── shows.html        # Show management
└── ...               # Other pages

static/               # CSS, JavaScript, images
uploads/              # Temporary upload storage
processed/            # Processed files output
instance/             # Database file location
logs/                 # Application logs
```

## 🚦 Production Deployment

For deploying to a production server:

1. **Use a production WSGI server**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

2. **Set environment variables**:
```bash
export FLASK_CONFIG=production
export SECRET_KEY=your-secret-key-here
export DATABASE_URL=postgresql://user:pass@localhost/dbname
```

3. **Use a reverse proxy** (nginx/Apache)
4. **Set up SSL certificates** for HTTPS
5. **Configure automatic backups**
6. **Set up monitoring and alerts**

## 🔄 Future Features

Planned enhancements include:
- FTP integration for automatic downloads
- AI-powered promo insertion
- Multi-station support
- API for third-party integrations
- Advanced scheduling features
- Email notifications

## 📄 License

This project is proprietary software intended for radio station use.

## 🤝 Support

For support and feature requests, please contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: October 2024