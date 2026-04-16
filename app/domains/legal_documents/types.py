from dataclasses import dataclass


@dataclass
class LegalDocument:
    filename: str
    mime_type: str
