from typing import Annotated
from uuid import uuid4

from fastapi import Depends

from app.core.common.exceptions import InvalidMimeTypeError
from app.core.storage.base_storage import BaseFileStorage
from app.core.storage.storage_factory import FileStorageDep
from app.domains.legal_documents.models import Sponsor
from app.domains.legal_documents.types import LegalDocument
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData


class LegalDocumentsService:
    def __init__(self, document: LegalDocument, file_storage: BaseFileStorage):
        self.document = document
        self.file_storage = file_storage

    async def upsert(self, file_data: FileData) -> None:
        if file_data.content_type != self.document.mime_type:
            raise InvalidMimeTypeError("Invalid file type. Only PDF allowed.")

        await self.file_storage.upload_file(
            self.document.filename,
            file_content=file_data.content,
            content_type=self.document.mime_type,
            content_disposition="inline",
        )

    async def delete(self) -> None:
        await self.file_storage.delete_file(self.document.filename)

    async def get_url(self) -> str | None:
        return await self.file_storage.get_file_url(
            self.document.filename,
            response_content_type=self.document.mime_type,
            response_content_disposition="inline",
        )


class SponsorsService:
    def __init__(self, transaction_manager, file_storage: BaseFileStorage):
        self.transaction_manager = transaction_manager
        self.file_storage = file_storage
        self.prefix = "sponsors/"

    async def get_all(self) -> list[Sponsor]:
        items, _ = await self.transaction_manager.sponsor_repository.list()
        return items

    async def get_by_id(self, sponsor_id: int) -> Sponsor | None:
        return await self.transaction_manager.sponsor_repository.get_first_by_kwargs(id=sponsor_id)

    def url_to_key(self, logo_url: str | None) -> str | None:
        return self.file_storage.extract_object_key(logo_url, allowed_prefixes=[self.prefix])

    async def key_to_url(self, logo_key: str | None) -> str | None:
        if not logo_key:
            return None
        return await self.file_storage.get_file_url(logo_key)

    async def create(self, **kwargs) -> Sponsor:
        async with self.transaction_manager:
            return await self.transaction_manager.sponsor_repository.create(**kwargs)

    async def update(self, sponsor_id: int, **kwargs) -> Sponsor:
        async with self.transaction_manager:
            return await self.transaction_manager.sponsor_repository.update(sponsor_id, **kwargs)

    async def delete(self, sponsor_id: int) -> None:
        async with self.transaction_manager:
            await self.transaction_manager.sponsor_repository.mark_as_deleted(sponsor_id)

    async def upload_logo(self, file_data: FileData) -> str:
        if not file_data.content_type.startswith("image/"):
            raise InvalidMimeTypeError("Invalid image content type")

        object_key = f"{self.prefix}{uuid4()}_{file_data.filename}"
        uploaded_file = await self.file_storage.upload_file(
            object_key=object_key,
            file_content=file_data.content,
        )
        return uploaded_file.object_key


def get_bylaws_document() -> LegalDocument:
    return LegalDocument(
        filename="legal_documents/bylaws.pdf",
        mime_type="application/pdf",
    )


def get_bylaws_service(
    document: Annotated[LegalDocument, Depends(get_bylaws_document)],
    file_storage: FileStorageDep,
) -> LegalDocumentsService:
    return LegalDocumentsService(document, file_storage)


BylawsServiceDep = Annotated[LegalDocumentsService, Depends(get_bylaws_service)]


def get_sponsors_service(file_storage: FileStorageDep, transaction_manager: TransactionManagerDep) -> SponsorsService:
    return SponsorsService(transaction_manager, file_storage)


SponsorsServiceDep = Annotated[SponsorsService, Depends(get_sponsors_service)]
