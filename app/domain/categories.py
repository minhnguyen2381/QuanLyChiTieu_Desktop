"""Danh mục: key trung lập ngôn ngữ + ánh xạ từ tên tiếng Việt cũ trong Firestore."""
import unicodedata

from app.domain.entities import TransactionType

OTHER = "other"

DEFAULT_CATEGORIES: dict[TransactionType, tuple[str, ...]] = {
    TransactionType.INFLOW: ("salary", "bonus", "passive_income", "sales", OTHER),
    TransactionType.OUTFLOW: ("food", "bills", "transport", "shopping", "health", "entertainment", OTHER),
}


def _normalize(name: str) -> str:
    return unicodedata.normalize("NFC", name.strip())


# Tên do phiên bản cũ seed vào Firestore -> key mới.
LEGACY_NAME_TO_KEY: dict[str, str] = {
    _normalize(name): key
    for name, key in {
        "Lương": "salary",
        "Thưởng": "bonus",
        "Thu nhập thụ động": "passive_income",
        "Bán hàng": "sales",
        "Khác": OTHER,
        "Ăn uống": "food",
        "Hóa đơn": "bills",
        "Di chuyển": "transport",
        "Mua sắm": "shopping",
        "Sức khỏe": "health",
        "Giải trí": "entertainment",
    }.items()
}


def is_legacy_name(name: str) -> bool:
    return bool(name) and _normalize(name) in LEGACY_NAME_TO_KEY


def legacy_name_to_key(name: str | None) -> str:
    """Tên cũ đã biết -> key; tên người dùng tự gõ giữ nguyên làm key; thiếu tên -> 'other'."""
    if not name or not name.strip():
        return OTHER
    return LEGACY_NAME_TO_KEY.get(_normalize(name), name)
