"""Đường dẫn tuyệt đối, tính theo thư mục chứa app (thư mục gốc repo, hoặc thư mục dist của Nuitka)."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(BASE_DIR, "locales")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
