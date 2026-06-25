from contextlib import asynccontextmanager
from urllib.parse import unquote, urlsplit

from aiobotocore.session import get_session
from botocore.exceptions import ClientError as BotocoreClientError

from app.core.storage.base_storage import BaseFileStorage, UploadedFileData


class S3Storage(BaseFileStorage):
    def __init__(
        self,
        *,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        public_url: str,
        default_bucket_name: str,
        region_name: str,
        expires_in: int,
    ):
        super().__init__(expires_in=expires_in)

        self.default_bucket_name = default_bucket_name
        self.session = get_session()
        self.region_name = region_name

        self.endpoint_url = endpoint_url.rstrip("/")
        self.public_url = public_url.rstrip("/")

        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": self.endpoint_url,
            "region_name": self.region_name,
        }

        self.public_config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": self.public_url,
            "region_name": self.region_name,
        }

    @asynccontextmanager
    async def get_client(self):
        """
        Client for internal backend -> MinIO operations:
        upload, delete, list, bucket_exists, etc.
        """
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    @asynccontextmanager
    async def get_public_client(self):
        """
        Client only for generating URLs that browser can open.
        """
        async with self.session.create_client("s3", **self.public_config) as client:
            yield client

    async def upload_file(
        self,
        object_key: str,
        file_content: bytes,
        bucket_name: str | None = None,
        content_type: str | None = None,
        content_disposition: str | None = None,
    ) -> UploadedFileData:
        """
        Uploads file to S3 storage.

        Returns:
            Information about the uploaded file:
            - ``bucket``: the name of the bucket where the file was uploaded
            - ``object_key``: the object key used to store the file
        """
        bucket = bucket_name or self.default_bucket_name

        await self.__ensure_bucket_exists(bucket)

        put_object_kwargs = {
            "Bucket": bucket,
            "Key": object_key,
            "Body": file_content,
        }

        if content_type:
            put_object_kwargs["ContentType"] = content_type

        if content_disposition:
            put_object_kwargs["ContentDisposition"] = content_disposition

        async with self.get_client() as client:
            await client.put_object(**put_object_kwargs)

        return UploadedFileData(
            object_key=object_key,
            metadata={"bucket": bucket},
        )

    async def get_file_url(
        self,
        object_key: str,
        expires_in: int | None = None,
        bucket_name: str | None = None,
        response_content_type: str | None = None,
        response_content_disposition: str | None = None,
    ) -> str | None:
        expires_in = expires_in or self.expires_in
        bucket = bucket_name or self.default_bucket_name

        if not await self.check_file_exists(object_key, bucket):
            return None

        params = {
            "Bucket": bucket,
            "Key": object_key,
        }

        if response_content_type:
            params["ResponseContentType"] = response_content_type

        if response_content_disposition:
            params["ResponseContentDisposition"] = response_content_disposition

        async with self.get_public_client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in,
            )
            return url

    async def delete_file(self, object_key: str, bucket_name: str | None = None) -> None:
        bucket = bucket_name or self.default_bucket_name
        async with self.get_client() as client:
            await client.delete_object(Bucket=bucket, Key=object_key)

    async def check_file_exists(self, object_key: str, bucket_name: str | None = None) -> bool:
        bucket = bucket_name or self.default_bucket_name

        async with self.get_client() as client:
            try:
                await client.head_object(Bucket=bucket, Key=object_key)
                return True

            except BotocoreClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    return False
                raise

    async def __ensure_bucket_exists(self, bucket_name: str | None = None):
        bucket = bucket_name or self.default_bucket_name
        async with self.get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket)
            except client.exceptions.NoSuchBucket:
                await client.create_bucket(Bucket=bucket)
            except Exception:
                try:
                    await client.create_bucket(Bucket=bucket)
                except BotocoreClientError as e:
                    error_code = e.response.get("Error", {}).get("Code")
                    if error_code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                        raise

    def extract_object_key(self, url: str | None, allowed_prefixes: list[str] | None = None) -> str | None:
        if url is None:
            return None

        if "://" not in url:
            return url.lstrip("/")

        parsed = urlsplit(url)
        path = unquote(parsed.path.lstrip("/"))

        bucket_prefix = f"{self.default_bucket_name}/"
        if path.startswith(bucket_prefix):
            path = path[len(bucket_prefix) :]

        if allowed_prefixes:
            for prefix in allowed_prefixes:
                if path.startswith(prefix):
                    return path
            return None

        return path
