from dataclasses import dataclass
from pathlib import Path


@dataclass
class LegalDocument:
    filename: str
    storage_path: Path
