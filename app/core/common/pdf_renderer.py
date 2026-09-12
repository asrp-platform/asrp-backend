from typing import Annotated, Any

from fastapi import Depends
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.core.config import BASE_DIR


class PdfTemplateRenderer:
    def __init__(self):
        self.__templates_root = BASE_DIR / "app"
        self.__environment = Environment(
            loader=FileSystemLoader(self.__templates_root),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render(self, template_name: str, context: dict[str, Any]) -> bytes:
        template = self.__environment.get_template(template_name)
        html = template.render(**context)
        return HTML(string=html, base_url=str(self.__templates_root)).write_pdf()


PdfTemplateRendererDep = Annotated[PdfTemplateRenderer, Depends(PdfTemplateRenderer)]
