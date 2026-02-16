import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

# Default allowed extensions
ALLOWED_EXTENSIONS = {
    # Documents
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md',
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico',
    # Archives
    'zip', 'rar', '7z', 'tar', 'gz',
    # Videos
    'mp4', 'mov', 'avi', 'webm', 'mkv',
    # Audio
    'mp3', 'wav', 'ogg', 'm4a',
    # Code
    'py', 'js', 'html', 'css', 'cpp', 'c', 'java', 'ipynb', 'json', 'xml',
    # Other
    'csv', 'log', 'ini', 'conf'
}

# Image-only extensions for profile pictures
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'ico'}

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_image(filename):
    """Check if file is an allowed image type"""
    return allowed_file(filename, IMAGE_EXTENSIONS)

def get_file_size(file):
    """Get file size in bytes"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

def save_file(file, subfolder='', allowed_extensions=None):
    """Save uploaded file with unique filename - RETURNS DICTIONARY"""
    try:
        if not file or not file.filename:
            return None
        
        print(f"📁 Saving file: {file.filename}")
        print(f"📂 Subfolder: {subfolder}")
        
        # Check file extension
        if not allowed_file(file.filename, allowed_extensions):
            print(f"❌ File type not allowed: {file.filename}")
            raise ValueError(f"File type not allowed")
        
        # Secure filename and add unique ID
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Create subfolder path with date structure
        today = datetime.now().strftime('%Y/%m/%d')
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, today)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        print(f"✅ File saved to: {file_path}")
        
        # Return DICTIONARY with file info (NOT a string!)
        relative_path = os.path.join(subfolder, today, unique_filename).replace('\\', '/')
        
        file_info = {
            'file_path': relative_path,
            'file_name': filename,
            'file_size': get_file_size(file),
            'file_type': ext[1:].lower() if ext else 'unknown'
        }
        
        print(f"📦 File info: {file_info}")
        return file_info
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        import traceback
        traceback.print_exc()
        raise e

def delete_file(file_path):
    """Delete file from filesystem"""
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"✅ File deleted: {full_path}")
            return True
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
    return False

def get_file_url(file_path):
    """Get public URL for file"""
    if file_path:
        base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')
        return f"{base_url}/uploads/{file_path}"
    return None

def human_readable_size(size_bytes):
    """Convert bytes to human readable string"""
    if size_bytes == 0:
        return "0B"
    
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_name[i]}"

def get_file_extension(filename):
    """Get file extension"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def validate_file_size(file, max_size_mb=10):
    """Validate file size (in MB)"""
    file_size = get_file_size(file)
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes, file_size

def create_upload_folders():
    """Create all necessary upload folders on startup"""
    folders = [
        'assignments',
        'submissions',
        'materials',
        'profile_pics',
        'feedback',
        'temp'
    ]
    
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    for folder in folders:
        folder_path = os.path.join(base_upload_folder, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"✅ Created upload folder: {folder}")

        