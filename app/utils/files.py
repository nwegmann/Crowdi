from uuid import uuid4
import os, pathlib, shutil
from fastapi import UploadFile

# Absolute path to the *static* directory (one level above this utils package)
STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # create both "static" and "uploads" if missing

def save_optional_image(upload: UploadFile | None) -> str | None:
    """
    Save UploadFile to disk and return the stored file path relative to the static directory,
    or None if no file was supplied.
    """
    if not upload or not upload.filename:
        return None

    ext = os.path.splitext(upload.filename)[1].lower()
    fname = f"{uuid4().hex}{ext}"
    dest  = UPLOAD_DIR / fname

    with dest.open("wb") as buf:
        shutil.copyfileobj(upload.file, buf)

    return f"uploads/{fname}"  # relative path used by templates