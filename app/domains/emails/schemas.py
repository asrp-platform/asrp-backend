from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ViewEmailTemplateSchema(BaseModel):
    id: int
    name: str
    subject: str
    description: str
    editor_state: dict[str, Any]
    html: str

    model_config = ConfigDict(from_attributes=True)


class CreateEmailTemplateSchema(BaseModel):
    name: str
    subject: str
    description: str
    editor_state: dict[str, Any]
    html: str


class UpdateEmailTemplateSchema(BaseModel):
    name: str | None = None
    subject: str | None = None
    description: str | None = None
    editor_state: dict[str, Any] | None = None
    html: str | None = None

    @model_validator(mode="after")
    def validate_editor_state_and_html(self):
        if (self.editor_state is None) != (self.html is None):
            raise ValueError(
                "editor_state and html must be provided together"
            )
        return self


class EmailTemplateVariablesSchema(BaseModel):
    key: str
    name: str
    description: str | None = None
