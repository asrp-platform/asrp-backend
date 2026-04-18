from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

Password = Annotated[str, Field()]


@dataclass
class FileData:
    content: bytes
    content_type: str
    filename: str
