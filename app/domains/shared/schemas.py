from pydantic import BaseModel


class UploadedImageSchema(BaseModel):
    path: str
