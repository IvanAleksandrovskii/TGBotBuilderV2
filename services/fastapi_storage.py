# services/fastapi_storage.py

import os
from typing import Optional, List

from fastapi import UploadFile
from fastapi_storages import FileSystemStorage

from core import log, settings


class CustomFileSystemStorage(FileSystemStorage):
    def __init__(self, root_path: str, allowed_extensions: Optional[List[str]] = None):
        self.root_path = root_path
        self.allowed_extensions = allowed_extensions or []
        super().__init__(self.root_path)

    # async def put(self, file: UploadFile) -> str:  # TODO: Implement or remove
    #     if not self._check_extension(file.filename):
    #         raise ValueError(f"File extension not allowed. Allowed extensions: {', '.join(self.allowed_extensions)}")

    #     os.makedirs(self.root_path, exist_ok=True)
    #     full_path = os.path.join(self.root_path, file.filename)

    #     content = await file.read()
    #     with open(full_path, "wb") as f:
    #         f.write(content)

    #     return file.filename

    def delete(self, name: str) -> None:
        
        if name.startswith("media/"):
            name = name[6:]
        
        if name.startswith("quiz/"):
            name = name[5:]
        
        full_path = os.path.join(self.root_path, name)
        if os.path.exists(full_path):
            os.remove(full_path)

    def _check_extension(self, filename: str) -> bool:
        if not self.allowed_extensions:
            return True
        return any(filename.lower().endswith(ext.lower()) for ext in self.allowed_extensions)


# Define allowed extensions for each type of file
ALLOWED_IMAGE_EXTENSIONS = settings.media.allowed_image_extensions

main_storage_location = settings.media.root[4:]

quiz_storage_location = settings.media.quiz_media[4:]

main_storage = CustomFileSystemStorage(main_storage_location, ALLOWED_IMAGE_EXTENSIONS)  # TODO: Fix Allowed media ext not working, 
# maybe del all mechanics cause in fact can dens almost all media 

quiz_storage = CustomFileSystemStorage(quiz_storage_location, ALLOWED_IMAGE_EXTENSIONS)

log.info("Initialized all storage instances")
