import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
RECEIPTS_DIR = os.path.join(ASSETS_DIR, "receipts")
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

# Ensure receipt directory exists
os.makedirs(RECEIPTS_DIR, exist_ok=True)
