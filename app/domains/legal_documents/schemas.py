from pydantic import BaseModel


class ViewLegalDocumentSchema(BaseModel):
    url: str
