from contextlib import asynccontextmanager
from datetime import timedelta

from aiobotocore.session import get_session
from botocore.exceptions import ClientError as BotocoreClientError


class S3BaseStorage:
    def __init__(
        self,
        *,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
        region_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": region_name,
        }
        self.bucket_name = bucket_name
        self.session = get_session()
        self.region_name = region_name

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(
        self,
        object_name: str,
        file,
        bucket_name: str | None = None,
    ):
        bucket = bucket_name or self.bucket_name
        await self.__ensure_bucket_exists(bucket)
        async with self.get_client() as client:
            await client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file,
            )
        return {"bucket": bucket, "object_name": object_name}

    async def get_presigned_object(self, object_key: str, bucket_name: str | None = None) -> str | None:
        bucket = bucket_name or self.bucket_name
        if not await self._check_object_exists(object_key, bucket_name=bucket):
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
        bucket = bucket_name or self.bucket_name
        async with self.get_client() as client:
            from contextlib import suppress
            with suppress(client.exceptions.NoSuchBucket):
                await client.delete_object(Bucket=bucket, Key=object_key)

    async def _check_object_exists(self, object_key: str, bucket_name: str | None = None) -> bool:
        bucket = bucket_name or self.bucket_name

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
        bucket = bucket_name or self.bucket_name
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
