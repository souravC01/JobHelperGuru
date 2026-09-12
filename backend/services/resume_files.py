import re
from typing import Optional
from urllib.parse import quote

from backend.storage import StorageService
from backend.services.object_storage import ObjectStorageService
from backend.models import Resume


def format_content_disposition(filename: str) -> str:
    """Builds RFC 6266 and RFC 5987 compliant Content-Disposition header with UTF-8 filename*."""
    clean_ascii = re.sub(r'[^\x20-\x7E]', '_', filename)
    clean_ascii = re.sub(r'[\r\n"\\]', '_', clean_ascii).strip() or "resume.pdf"
    encoded_utf8 = quote(filename.replace('\r', '_').replace('\n', '_'), safe="")
    return f'attachment; filename="{clean_ascii}"; filename*=UTF-8\'\'{encoded_utf8}'


class ResumeFileManager:
    def __init__(self, storage: StorageService, object_storage: ObjectStorageService):
        self.storage = storage
        self.object_storage = object_storage

    def reserve_and_upload(
        self,
        user_id: str,
        filename: str,
        content_type: Optional[str],
        content_bytes: bytes,
        resume_name: Optional[str],
        text_content: str,
        max_resumes: int = 10,
        max_storage_bytes: int = 50 * 1024 * 1024,
    ) -> Resume:
        current_bytes = self.storage.get_user_upload_bytes(user_id)
        if current_bytes + len(content_bytes) > max_storage_bytes:
            raise ValueError("Maximum total storage limit of 50MB reached for resumes.")

        file_key = self.object_storage.upload_file(
            content_bytes=content_bytes,
            filename=filename,
            content_type=content_type,
            user_id=user_id,
        )

        storage_backend = "r2" if self.object_storage.is_configured else "local"
        attachment = self.storage.create_attachment(
            user_id=user_id,
            storage_backend=storage_backend,
            object_key=file_key,
            original_filename=filename,
            content_type=content_type,
            size_bytes=len(content_bytes),
        )

        final_name = resume_name.strip() if (resume_name and resume_name.strip()) else filename
        try:
            resume = self.storage.add_resume(
                name=final_name,
                content=text_content,
                file_key=file_key,
                user_id=user_id,
                attachment_id=attachment.id,
                max_resumes=max_resumes,
            )
            return resume
        except Exception:
            self.object_storage.delete_file(file_key, user_id=user_id)
            self.storage.update_attachment_deletion_state(attachment.id, "failed", user_id=user_id)
            raise

    def delete_resume(self, user_id: str, resume_id: str) -> bool:
        resume = self.storage.get_resume(resume_id, user_id=user_id)
        if not resume:
            return False

        if resume.attachment_id or resume.file_key:
            attachment = None
            if resume.attachment_id:
                attachment = self.storage.get_attachment(resume.attachment_id, user_id=user_id)
            elif resume.file_key:
                attachment = self.storage.get_attachment_by_key(resume.file_key, user_id=user_id)

            if attachment:
                self.storage.update_attachment_deletion_state(attachment.id, "pending", user_id=user_id)
                deleted = self.object_storage.delete_file(attachment.object_key, user_id=user_id)
                if not deleted:
                    self.storage.update_attachment_deletion_state(attachment.id, "failed", user_id=user_id)
                    raise RuntimeError("Failed to delete associated storage file.")
                self.storage.delete_attachment(attachment.id, user_id=user_id)
            elif resume.file_key:
                self.object_storage.delete_file(resume.file_key, user_id=user_id)

        self.storage.delete_resume(resume_id, user_id=user_id)
        return True
