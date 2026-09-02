from pydantic import BaseModel


class UploadedImageSchema(BaseModel):
    file_url: str
    object_key: str
