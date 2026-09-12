import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

load_dotenv()

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
        upload_dir: Optional[Union[str, Path]] = None,
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
        self._upload_dir = Path(upload_dir or "data/uploads").resolve()

        backend_choice = (os.getenv("STORAGE_BACKEND") or "").strip().lower()

        if (
            backend_choice != "local"
            and BOTO3_AVAILABLE
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

    @property
    def upload_dir(self) -> Path:
        return self._upload_dir

    @upload_dir.setter
    def upload_dir(self, val: Union[str, Path]):
        self._upload_dir = Path(val).resolve()

    def _resolve_safe_path(self, object_key: str, user_id: Optional[str] = None) -> Optional[Path]:
        """
        Validates object_key against path traversal and enforces strict directory containment.
        If user_id is given, ensures the file does not belong to another user namespace.
        """
        if not object_key or not isinstance(object_key, str):
            return None

        # Normalize slashes and reject traversal tokens / absolute patterns
        clean_key = object_key.replace("\\", "/").strip()
        parts = clean_key.split("/")
        if ".." in parts or "." in parts or clean_key.startswith("/") or ":" in clean_key:
            return None

        try:
            target = (self._upload_dir / clean_key).resolve()
            if not target.is_relative_to(self._upload_dir):
                return None

            # Enforce user boundary if user_id is provided
            if user_id:
                user_root = (self._upload_dir / "resumes" / user_id).resolve()
                resumes_root = (self._upload_dir / "resumes").resolve()
                if target.is_relative_to(resumes_root) and not target.is_relative_to(user_root):
                    return None

            return target
        except Exception:
            return None

    def upload_file(
        self,
        content_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Uploads file binary to Cloudflare R2 or local uploads folder.
        Returns the unique storage object key.
        In R2 mode, raises RuntimeError if upload fails (no silent fallback to ephemeral disk).
        """
        ext = Path(filename).suffix
        safe_name = Path(filename).stem.replace(" ", "_")
        prefix = f"resumes/{user_id}" if user_id else "resumes"
        unique_key = f"{prefix}/{uuid.uuid4().hex}_{safe_name}{ext}"

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
                raise RuntimeError(f"Cloudflare R2 upload error for {filename}: {e}")

        # Local filesystem mode
        safe_path = self._resolve_safe_path(unique_key, user_id=user_id)
        if not safe_path:
            raise ValueError(f"Invalid object storage key generated: {unique_key}")

        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(content_bytes)
        return unique_key

    def get_file(self, object_key: str, user_id: Optional[str] = None) -> Optional[bytes]:
        """Downloads file binary from Cloudflare R2 or local filesystem."""
        if not object_key:
            return None

        if self.is_configured and self.client:
            try:
                response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
                return response["Body"].read()
            except Exception as e:
                print(f"[WARN] R2 download failed for {object_key}: {e}")

        safe_path = self._resolve_safe_path(object_key, user_id=user_id)
        if safe_path and safe_path.is_file():
            try:
                return safe_path.read_bytes()
            except Exception:
                return None

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

    def delete_file(self, object_key: str, user_id: Optional[str] = None) -> bool:
        """Deletes file from Cloudflare R2 or local disk."""
        if not object_key:
            return False

        if self.is_configured and self.client:
            try:
                self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
                return True
            except Exception as e:
                print(f"[WARN] R2 delete failed for {object_key}: {e}")
                return False

        safe_path = self._resolve_safe_path(object_key, user_id=user_id)
        if safe_path:
            if not safe_path.exists():
                return True
            if safe_path.is_file():
                try:
                    safe_path.unlink()
                    return True
                except Exception:
                    return False

        return False

