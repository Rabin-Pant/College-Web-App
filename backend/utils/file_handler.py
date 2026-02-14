import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

# Default allowed extensions
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 
    'jpg', 'jpeg', 'png', 'gif',
    'zip', 'rar', '7z',
    'txt', 'md', 'csv',
    'mp4', 'mov', 'avi', 'webm'
}

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size(file):
    """Get file size in bytes"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

def save_file(file, subfolder='', allowed_extensions=None):
    """Save uploaded file with unique filename"""
    try:
        if not file or not file.filename:
            return None
        
        # Check file extension
        if not allowed_file(file.filename, allowed_extensions):
            raise ValueError(f"File type not allowed")
        
        # Secure filename and add unique ID
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Create subfolder path
        today = datetime.now().strftime('%Y/%m/%d')
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, today)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Return file info as DICTIONARY (not string)
        relative_path = os.path.join(subfolder, today, unique_filename).replace('\\', '/')
        
        return {
            'file_path': relative_path,
            'file_name': filename,
            'file_size': os.path.getsize(file_path),
            'file_type': ext[1:].lower() if ext else 'unknown'
        }
        
    except Exception as e:
        print(f"Error saving file: {e}")
        raise e

def delete_file(file_path):
    """Delete file from filesystem"""
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")
    return False

def get_file_url(file_path):
    """Get public URL for file"""
    if file_path:
        return f"/uploads/{file_path}"
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

def get_file_size(file):
    """Get file size in bytes"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size