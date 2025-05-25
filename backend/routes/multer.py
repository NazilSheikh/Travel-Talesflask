# multer.py
import os
import time
from werkzeug.utils import secure_filename

# Destination folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed MIME types like multer's fileFilter
ALLOWED_MIMETYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']

def file_filter(file):
    return file.mimetype in ALLOWED_MIMETYPES

def save_file(file):
     
    if not file_filter(file):
        raise ValueError("Only images are allowed")

    ext = os.path.splitext(file.filename)[1]
    filename = f"{int(time.time() * 1000)}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filename
