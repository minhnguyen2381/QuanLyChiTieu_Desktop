"""Lưu ảnh biên lai vào thư mục app; trong DB chỉ lưu đường dẫn tương đối."""
import os
import shutil
from datetime import datetime

RELATIVE_DIR = "assets/receipts"


class LocalReceiptStorage:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def save(self, source_path: str) -> str:
        target_dir = os.path.join(self._base_dir, *RELATIVE_DIR.split("/"))
        os.makedirs(target_dir, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + os.path.basename(source_path)
        shutil.copy2(source_path, os.path.join(target_dir, filename))
        return f"{RELATIVE_DIR}/{filename}"

    def resolve(self, stored_path: str) -> str | None:
        if not stored_path:
            return None
        path = stored_path if os.path.isabs(stored_path) else os.path.join(self._base_dir, stored_path)
        path = os.path.normpath(path)
        return path if os.path.isfile(path) else None
