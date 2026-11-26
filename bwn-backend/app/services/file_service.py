
import uuid
from pathlib import Path
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = Path("uploads/businesses")
MAX_IMAGE_DIMENSION = 4096
ALLOWED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


async def save_business_image(file: UploadFile) -> str:
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image size cannot exceed 5 MB",
        )

    try:
        image = Image.open(BytesIO(content))
        if image.width > MAX_IMAGE_DIMENSION or image.height > MAX_IMAGE_DIMENSION:
            raise HTTPException(
                status_code=400,
                detail="Image dimensions cannot exceed 4096x4096",
        )
        image.verify()

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    image_format = image.format

    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG and WEBP images are allowed",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_FORMATS[image_format]
    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(content)

    return file_path.as_posix()


def delete_business_image(image_path: str | None):
    if not image_path:
        return

    upload_root = UPLOAD_DIR.resolve()
    target_path = Path(image_path).resolve()

    # Ensure the file belongs to our upload directory
    if not target_path.is_relative_to(upload_root):
        return

    if target_path.is_file():
        target_path.unlink()