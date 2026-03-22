from contextlib import asynccontextmanager

from aiobotocore.session import get_session


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
                # ContentType=file.content_type,
            )
        return {"bucket": bucket, "object_name": object_name}

    async def __ensure_bucket_exists(self, bucket_name: str | None = None):
        bucket = bucket_name or self.bucket_name
        async with self.get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket)  # существует ли bucket
            except client.exceptions.NoSuchBucket:
                await client.create_bucket(Bucket=bucket)  # Если не существует, то создаем его
            except Exception:
                import botocore.exceptions

                try:
                    await client.create_bucket(Bucket=bucket)
                except botocore.exceptions.ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code")
                    if error_code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                        raise
