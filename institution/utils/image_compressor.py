import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile

def compress_image(uploaded_file, max_size_kb=500, format="JPEG", quality=60):
    if not uploaded_file:
        return None

    ext = os.path.splitext(uploaded_file.name)[1].lower()

    # If file is PDF → return as-is (or you can later add PDF compression logic)
    if ext == ".pdf":
        return uploaded_file  

    # Otherwise, try to treat it as an image
    try:
        img = Image.open(uploaded_file)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        buffer = BytesIO()
        img.save(buffer, format=format, quality=quality, optimize=True)
        size_kb = buffer.tell() / 1024

        # Reduce quality if still too large
        while size_kb > max_size_kb and quality > 10:
            buffer = BytesIO()
            quality -= 5
            img.save(buffer, format=format, quality=quality, optimize=True)
            size_kb = buffer.tell() / 1024

        return ContentFile(buffer.getvalue(), name=uploaded_file.name)

    except Exception:
        return uploaded_file
