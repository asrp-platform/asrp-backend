from pydantic import BaseModel


class PermissionSchema(BaseModel):
    id: int
    action: str
    name: str

    model_config = {"from_attributes": True}
