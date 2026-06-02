from pathlib import Path
from uuid import uuid4

from app.core.config import BASE_DIR
from app.domains.shared.types import FileData


async def save_file(file: FileData, path: Path, filename: str | None = None) -> Path:
    if not filename:
        ext = file.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{ext}"
    filepath = BASE_DIR / path / filename

    with open(filepath, "wb") as f:
        f.write(file.content)

    return Path(path / filename)


def generate_filename(filename: str, prefix: str | None) -> str:
    if prefix is None:
        return f"{uuid4()}.{filename.split('.')[-1]}"
    return f"{prefix}/{uuid4()}.{filename.split('.')[-1]}"
