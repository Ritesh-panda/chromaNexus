import os
import shutil
import uuid
from typing import Optional
from fastapi import UploadFile
from backend.app.core.config import settings


class StorageService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        if settings.STORAGE_BACKEND == "local":
            os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file: UploadFile) -> tuple[str, str, int]:
        """
        Saves uploaded file securely into private vault storage.
        Returns: (file_id, file_path, file_size)
        """
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename or "")[1]
        stored_filename = f"{file_id}{ext}"
        target_path = os.path.join(self.upload_dir, stored_filename)

        content = await file.read()
        file_size = len(content)

        with open(target_path, "wb") as f:
            f.write(content)

        # Reset cursor
        await file.seek(0)
        return file_id, target_path, file_size

    def get_file_path(self, storage_path: str) -> Optional[str]:
        if os.path.exists(storage_path):
            return storage_path
        return None

    def delete_file(self, storage_path: str) -> bool:
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
                return True
        except Exception:
            pass
        return False


storage_service = StorageService()
