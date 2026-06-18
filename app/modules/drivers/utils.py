import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
BLOCKED_EXTENSIONS = {'bat', 'cmd', 'com', 'dll', 'exe', 'js', 'msi', 'ps1', 'scr', 'sh', 'vbs'}
MAX_DOCUMENT_SIZE_BYTES = 4 * 1024 * 1024


def normalize_filename(filename):
    return secure_filename(filename)


def safe_extension(filename):
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in ALLOWED_EXTENSIONS and ext not in BLOCKED_EXTENSIONS


def validate_driver_document_file(file_storage, max_size=MAX_DOCUMENT_SIZE_BYTES):
    if not file_storage or not file_storage.filename:
        return

    filename = normalize_filename(file_storage.filename)
    if not filename or not safe_extension(filename):
        raise ValueError('Only PDF, JPG, JPEG, and PNG documents are allowed.')

    stream = getattr(file_storage, 'stream', None)
    if stream and hasattr(stream, 'seek') and hasattr(stream, 'tell'):
        current_position = stream.tell()
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(current_position)
        if size > max_size:
            raise ValueError('Document file size must be 4 MB or less.')


def save_driver_document_file(file_storage, upload_folder, driver_id):
    if not file_storage or not file_storage.filename:
        return None

    validate_driver_document_file(file_storage)
    filename = normalize_filename(file_storage.filename)
    driver_folder = os.path.join(upload_folder, driver_id)
    os.makedirs(driver_folder, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    storage_path = os.path.join(driver_folder, unique_name)
    file_storage.save(storage_path)
    return os.path.join(driver_id, unique_name)
