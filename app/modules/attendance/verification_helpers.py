import os
import uuid
import base64
import io
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
BLOCKED_EXTENSIONS = {
    'bat', 'cmd', 'com', 'dll', 'exe', 'js', 'msi', 'ps1', 'scr', 'sh', 'vbs',
    'py', 'php', 'pl', 'rb', 'html', 'htm', 'asp', 'aspx', 'jsp'
}
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024


def validate_verification_image(file_storage, max_size=MAX_IMAGE_SIZE_BYTES):
    if not file_storage or not file_storage.filename:
        raise ValueError('No file uploaded.')

    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError('Invalid filename.')

    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    if ext not in ALLOWED_EXTENSIONS or ext in BLOCKED_EXTENSIONS:
        raise ValueError('Only JPG, JPEG, PNG, and WEBP images are allowed.')

    # Validate MIME type if available
    content_type = getattr(file_storage, 'content_type', '')
    if content_type and not content_type.startswith('image/'):
        raise ValueError('Uploaded file must be an image.')

    stream = getattr(file_storage, 'stream', None)
    if stream and hasattr(stream, 'seek') and hasattr(stream, 'tell'):
        current_position = stream.tell()
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(current_position)
        if size > max_size:
            raise ValueError('Image size must be 4 MB or less.')


def decode_base64_image(base64_data_str, default_filename='captured_image.jpg'):
    if not base64_data_str:
        return None

    if ',' in base64_data_str:
        header, base64_data_str = base64_data_str.split(',', 1)
    else:
        header = 'data:image/jpeg;base64'

    mime_type = 'image/jpeg'
    ext = 'jpg'
    if 'png' in header:
        mime_type = 'image/png'
        ext = 'png'
    elif 'webp' in header:
        mime_type = 'image/webp'
        ext = 'webp'

    filename = f"{os.path.splitext(default_filename)[0]}.{ext}"
    try:
        image_bytes = base64.b64decode(base64_data_str)
    except Exception:
        raise ValueError('Invalid base64 image data.')

    file_storage = FileStorage(
        stream=io.BytesIO(image_bytes),
        filename=filename,
        content_type=mime_type
    )
    return file_storage


def encode_verification_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    validate_verification_image(file_storage)
    try:
        file_storage.stream.seek(0)
        image_bytes = file_storage.stream.read()
        file_storage.stream.seek(0)
    except Exception:
        image_bytes = b''

    if not image_bytes:
        return None

    mime_type = getattr(file_storage, 'content_type', '') or 'image/jpeg'
    if not mime_type.startswith('image/'):
        mime_type = 'image/jpeg'

    encoded = base64.b64encode(image_bytes).decode('ascii')
    return f'data:{mime_type};base64,{encoded}'


def save_verification_image(file_storage, upload_folder, driver_id):
    if not file_storage or not file_storage.filename:
        return None

    validate_verification_image(file_storage)
    filename = secure_filename(file_storage.filename)
    driver_folder = os.path.join(upload_folder, driver_id)
    os.makedirs(driver_folder, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    storage_path = os.path.join(driver_folder, unique_name)

    try:
        from PIL import Image
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        
        max_size = 1280
        width, height = img.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            resample_filter = getattr(Image, 'Resampling', None)
            resample = resample_filter.LANCZOS if resample_filter else getattr(Image, 'ANTIALIAS', 3)
            img = img.resize((new_width, new_height), resample)
        
        img_format = img.format if img.format else 'JPEG'
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext in ['jpg', 'jpeg'] or img_format == 'JPEG':
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.save(storage_path, format='JPEG', quality=85, optimize=True)
        else:
            img.save(storage_path, format=img_format, optimize=True)
    except Exception as e:
        print(f"Pillow image optimization failed, falling back to raw save: {e}")
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass
        file_storage.save(storage_path)

    return os.path.join(driver_id, unique_name)

