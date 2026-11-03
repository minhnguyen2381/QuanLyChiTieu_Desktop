import shutil
import os
from datetime import datetime
from config import RECEIPTS_DIR

def format_currency(amount):
    """Format float/int to VND currency string."""
    try:
        return f"{int(amount):,}".replace(",", ".") + " đ"
    except (ValueError, TypeError):
        return "0 đ"

def parse_currency_to_float(currency_str):
    """Parse formatted currency string back to float."""
    try:
        clean_str = str(currency_str).replace(".", "").replace(",", "").replace("đ", "").strip()
        return float(clean_str)
    except ValueError:
        return 0.0

def save_receipt_image(source_path):
    """Copy image to local assets/receipts folder and return relative path."""
    if not source_path or not os.path.exists(source_path):
        return None
        
    filename = os.path.basename(source_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
    new_filename = f"{timestamp}{filename}"
    
    destination_path = os.path.join(RECEIPTS_DIR, new_filename)
    
    try:
        shutil.copy2(source_path, destination_path)
        # return relative path to save in DB
        return f"assets/receipts/{new_filename}"
    except Exception as e:
        print(f"Error copying image: {e}")
        return None
