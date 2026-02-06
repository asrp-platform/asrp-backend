from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import BASE_DIR


async def save_file(file: UploadFile, path: Path, filename: str | None = None) -> Path:
    if not filename:
        ext = file.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
    filepath = BASE_DIR / path / filename

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return Path(path / filename)
