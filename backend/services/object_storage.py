import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    import boto3
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class ObjectStorageService:
    """
    Cloudflare R2 Object Storage Service (S3-compatible).
    Stores binary assets such as uploaded resume PDFs and Word documents.
    Gracefully falls back to local file storage if R2 credentials are not set.
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.account_id = account_id or os.getenv("R2_ACCOUNT_ID")
        self.access_key_id = access_key_id or os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("R2_BUCKET_NAME", "jobhelperguru-resumes")

        # Derive endpoint URL if not explicitly given
        if endpoint_url:
            self.endpoint_url = endpoint_url
        elif self.account_id:
            self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        else:
            self.endpoint_url = os.getenv("R2_ENDPOINT_URL")

        self.client = None
        self.is_configured = False

        if (
            BOTO3_AVAILABLE
            and self.access_key_id
            and self.secret_access_key
            and self.endpoint_url
        ):
            try:
                self.client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    config=Config(signature_version="s3v4"),
                    region_name="auto",
                )
                self.is_configured = True
            except Exception as e:
                print(f"[WARN] Failed to initialize Cloudflare R2 client: {e}")
                self.is_configured = False

    def upload_file(
        self,
        content_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Uploads file binary to Cloudflare R2 or local uploads folder.
        Returns the unique storage object key.
        """
        ext = Path(filename).suffix
        safe_name = Path(filename).stem.replace(" ", "_")
        unique_key = f"resumes/{uuid.uuid4().hex}_{safe_name}{ext}"

        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        if self.is_configured and self.client:
            try:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=unique_key,
                    Body=content_bytes,
                    ContentType=content_type,
                )
                return unique_key
            except Exception as e:
                print(f"[ERROR] Cloudflare R2 upload error for {filename}: {e}")

        # Local filesystem fallback
        local_dir = Path("data/uploads/resumes")
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / Path(unique_key).name
        local_path.write_bytes(content_bytes)
        return unique_key

    def get_file(self, object_key: str) -> Optional[bytes]:
        """Downloads file binary from Cloudflare R2 or local filesystem."""
        if not object_key:
            return None

        if self.is_configured and self.client:
            try:
                response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
                return response["Body"].read()
            except Exception as e:
                print(f"[WARN] R2 download failed for {object_key}: {e}")

        local_path = Path("data/uploads/resumes") / Path(object_key).name
        if local_path.exists():
            return local_path.read_bytes()

        return None

    def generate_download_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generates a secure presigned download URL for direct browser access.
        Expires in 1 hour by default.
        """
        if not object_key:
            return None

        if self.is_configured and self.client:
            try:
                return self.client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key},
                    ExpiresIn=expires_in,
                )
            except Exception as e:
                print(f"[WARN] Failed to generate presigned URL for {object_key}: {e}")

        return None

    def delete_file(self, object_key: str) -> bool:
        """Deletes file from Cloudflare R2 or local disk."""
        if not object_key:
            return False

        if self.is_configured and self.client:
            try:
                self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
                return True
            except Exception as e:
                print(f"[WARN] R2 delete failed for {object_key}: {e}")

        local_path = Path("data/uploads/resumes") / Path(object_key).name
        if local_path.exists():
            local_path.unlink()
            return True

        return False
