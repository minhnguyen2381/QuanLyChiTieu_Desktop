"""Hiển thị/nhập liệu theo ngôn ngữ: tiền, ngày, nhãn danh mục và loại giao dịch."""
from datetime import date, datetime

from app.domain.entities import TransactionType
from app.presentation.i18n import current_language, t

DATE_FORMAT = "%d/%m/%Y"


def format_money(amount: float, language: str | None = None) -> str:
    number = f"{round(amount):,}"
    if (language or current_language()) == "vi":
        return number.replace(",", ".") + " đ"
    return number + " VND"


def parse_money(text: str) -> float:
    """VND không có phần lẻ: bỏ mọi ký tự không phải chữ số ('1.500.000 đ' -> 1500000)."""
    digits = "".join(ch for ch in str(text) if ch in "0123456789")
    return float(digits) if digits else 0.0


def format_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)


def category_label(key: str) -> str:
    """Danh mục mặc định thì dịch; danh mục người dùng tự gõ thì hiển thị nguyên văn."""
    translation_key = f"category.{key}"
    text = t(translation_key)
    return key if text == translation_key else text


def type_label(transaction_type: TransactionType) -> str:
    return t(f"type.{transaction_type.value}")


def type_long_label(transaction_type: TransactionType) -> str:
    return t(f"type_long.{transaction_type.value}")


def combine_date_keep_time(new_date: date, original: datetime | None) -> datetime:
    """Ngày lấy từ ô chọn ngày; giờ giữ theo giao dịch gốc (khi sửa) hoặc giờ hiện tại (khi thêm)."""
    time_source = original or datetime.now()
    return datetime.combine(new_date, time_source.time())
