from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta

from aiobotocore.session import get_session
from botocore.exceptions import ClientError as BotocoreClientError


@dataclass
class S3UploadedFileData:
    bucket: str
    object_key: str


class S3BaseStorage:
    def __init__(
        self,
        *,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        default_bucket_name: str,
        region_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": region_name,
        }
        self.default_bucket_name = default_bucket_name
        self.session = get_session()
        self.region_name = region_name

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(
        self,
        object_key: str,
        file: bytes,
        bucket_name: str | None = None,
    ) -> S3UploadedFileData:
        """
        Uploads file to S3 storage

        Returns:
            A dictionay with information about the uploaded file
            - ``bucket``: the name of the bucket where the filw was uploaded
            - ``object_name``: the object key used to store the file
        """
        bucket = bucket_name or self.default_bucket_name
        await self.__ensure_bucket_exists(bucket)
        async with self.get_client() as client:
            await client.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=file,
            )
        return S3UploadedFileData(bucket=bucket, object_key=object_key)

    async def get_presigned_object(self, object_key: str, bucket_name: str | None = None) -> str | None:
        bucket = bucket_name or self.default_bucket_name
        if not await self._check_object_exists(object_key):
            return None

        async with self.get_client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": object_key,
                },
                ExpiresIn=int(timedelta(hours=1).total_seconds()),
            )
            return url

    async def delete_object(self, object_key: str, bucket_name: str | None = None) -> None:
        bucket = bucket_name or self.default_bucket_name
        async with self.get_client() as client:
            await client.delete_object(Bucket=bucket, Key=object_key)

    async def _check_object_exists(self, object_key: str, bucket_name: str | None = None) -> bool:
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
                await client.head_bucket(Bucket=bucket)  # существует ли bucket
            except client.exceptions.NoSuchBucket:
                await client.create_bucket(Bucket=bucket)  # Если не существует, то создаем его
            except Exception:
                try:
                    await client.create_bucket(Bucket=bucket)
                except BotocoreClientError as e:
                    error_code = e.response.get("Error", {}).get("Code")
                    if error_code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                        raise
