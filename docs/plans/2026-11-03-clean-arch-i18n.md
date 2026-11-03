# Clean Architecture + i18n + Category Keys — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans (inline default). Select bounded delegation or parallel waves only under task-tiering's execution-mode policy. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tái cấu trúc app Tkinter quản lý chi tiêu sang Clean Architecture 4 tầng. Kèm theo: i18n vi/en, danh mục lưu bằng key trung lập ngôn ngữ (có script migration an toàn), và sửa 9 hành vi đã liệt kê trong spec.

**Architecture:**
- `app/domain`: dataclass thuần cộng logic tính toán.
- `app/application`: service; giao tiếp ra ngoài qua Protocol.
- `app/infrastructure`: Firestore và file system.
- `app/presentation`: Tkinter, i18n, biểu đồ, xuất Word.
- `app/container.py`: nối dependency.
- Quy tắc phụ thuộc: domain không import gì ngoài stdlib; presentation không import infrastructure.

**Tech Stack:** Python 3.14 (`.venv`), Tkinter + tkcalendar, firebase-admin (Firestore), matplotlib (dùng `Figure`, không dùng pyplot), python-docx, Pillow, `unittest` (stdlib).

**Spec:** `docs/specs/2026-11-03-clean-arch-i18n-design.md`

## Global Constraints

- Mọi lệnh chạy từ thư mục gốc repo `D:\DuAn\DuAnQuanLyChiTieu` bằng `.venv/Scripts/python.exe`.
- Lệnh test: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
- Không thêm dependency mới. Bỏ `python-dotenv` và `dnspython` khỏi `requirements.txt`.
- Tên collection Firestore giữ nguyên: `transactions`, `categories`.
- Field khi ghi transaction: `type, total_amount, items[{category_key, amount, item_note}], date, general_note, image_path, contact_person` cộng `created_at` (khi add) hoặc `updated_at` (khi update).
- Khi đọc phải chấp nhận dữ liệu cũ: item có `category_name` mà không có `category_key`; category có `name` mà không có `key`. Ngày tz-aware được chuyển về naive và giữ nguyên giờ hiển thị (wall-clock).
- Key danh mục mặc định:
  - inflow: `salary, bonus, passive_income, sales, other`
  - outflow: `food, bills, transport, shopping, health, entertainment, other`
- Tiền tệ: vi hiển thị `1.500.000 đ`, en hiển thị `1,500,000 VND`. Ngày dùng `dd/mm/yyyy` cho cả hai ngôn ngữ.
- **Không có bước nào ghi lên Firestore thật ngoại trừ Task 8, và Task 8 chỉ chạy sau khi người dùng xác nhận riêng.**
- **No auto-commit:** Không có `git commit` trong task nào. Chỉ commit sau khi **mọi task hoàn tất** và **người dùng đồng ý** (hỏi một lần ở cuối).

## Spec deltas (quyết định chi tiết khi lập kế hoạch; cập nhật vào spec ở Task 7)

1. `PeriodReport` và `build_period_report()` đặt ở `app/domain/summary.py`, không ở application. Lý do: `ports.py` cần tham chiếu kiểu này mà không bị import vòng.
2. `run_safely(parent, action)` đổi thành context manager `reported_errors(parent)` để code gọi gọn hơn.
3. Domain coi `category_key` rỗng là `InvalidTransaction`.
4. Migration ghi có điều kiện `last_update_time`. Nếu một doc bị sửa giữa lúc đọc và lúc ghi, batch đó sẽ fail thay vì ghi đè; chạy lại script là xong.
5. Biểu đồ dùng `matplotlib.figure.Figure`, bỏ `pyplot` và `matplotlib.use("Agg")`, để tránh rò rỉ figure và tránh trạng thái backend toàn cục.
6. Cửa sổ chính dùng `Transaction` đã cache trong `PeriodReport` để xem, sửa và xoá, không query lại theo id.
7. (Người dùng chốt) Giao dịch tạo/sửa bằng bản mới **chỉ ghi `category_key`**. Bản app cũ đọc `item['category_name']` trực tiếp nên sẽ crash trên các doc này.

## File map

| File | Trách nhiệm |
|------|-------------|
| `app/config.py` | Đường dẫn tuyệt đối theo thư mục app |
| `app/domain/entities.py` | `TransactionType`, `TransactionItem`, `Transaction`, `InvalidTransaction` |
| `app/domain/categories.py` | Key mặc định, ánh xạ tên tiếng Việt cũ sang key |
| `app/domain/summary.py` | `PeriodSummary`, `CategoryTotal`, `PeriodReport`, các hàm tính |
| `app/application/ports.py` | 4 Protocol |
| `app/application/transaction_service.py` | Use case giao dịch |
| `app/application/report_service.py` | Use case xuất báo cáo, `NoDataError` |
| `app/infrastructure/firestore_mapping.py` | Chuyển đổi dict ↔ entity (hàm thuần) |
| `app/infrastructure/firestore_repository.py` | `connect()`, repository Firestore |
| `app/infrastructure/receipt_storage.py` | Lưu/resolve ảnh biên lai |
| `app/presentation/i18n.py` | `Translator`, `t()`, settings ngôn ngữ |
| `app/presentation/formatters.py` | Tiền, ngày, label danh mục, giữ giờ khi sửa |
| `app/presentation/charts.py` | `plot_category_bars()` dùng chung |
| `app/presentation/word_exporter.py` | `WordReportExporter` |
| `app/presentation/ui_helpers.py` | `reported_errors()`, `make_date_entry()` |
| `app/presentation/loading_window.py` | Màn hình kết nối |
| `app/presentation/main_window.py` | Cửa sổ chính + menu ngôn ngữ |
| `app/presentation/transaction_form.py` | Form thêm/sửa |
| `app/presentation/transaction_detail.py` | Xem chi tiết |
| `app/presentation/chart_view.py` | Cửa sổ biểu đồ |
| `app/container.py` | `Services`, `build_services()` |
| `locales/vi.json`, `locales/en.json` | Bản dịch |
| `scripts/migrate_category_keys.py` | Migration |
| `main.py` | Entry point |
| `tests/helpers.py` | `make_transaction`, fakes, `START`/`END` |
| `tests/test_*.py` | Test |

Mỗi package có một `__init__.py` rỗng: `app/`, `app/domain/`, `app/application/`, `app/infrastructure/`, `app/presentation/`.

---

### Task 1: Domain

**Files:**
- Create: `app/__init__.py`, `app/domain/__init__.py`, `tests/__init__.py` (rỗng; `tests/__init__.py` để package `tests` của repo không bị package trùng tên trong site-packages che)
- Create: `app/domain/entities.py`, `app/domain/categories.py`, `app/domain/summary.py`
- Test: `tests/helpers.py`, `tests/test_entities.py`, `tests/test_categories.py`, `tests/test_summary.py`

**Interfaces:**
- Produces:
  - `TransactionType` (StrEnum `INFLOW`/`OUTFLOW`)
  - `TransactionItem(category_key, amount, note="")`
  - `Transaction(type, date, items, general_note="", contact_person="", receipt_path="", id=None)` với property `.total`
  - `InvalidTransaction(ValueError)`
  - `DEFAULT_CATEGORIES`, `LEGACY_NAME_TO_KEY`, `legacy_name_to_key(name) -> str`, `is_legacy_name(name) -> bool`
  - `PeriodSummary(inflow, outflow)` với property `.balance`
  - `CategoryTotal(category_key, total)`
  - `PeriodReport(start, end, transactions, summary, inflow_by_category, outflow_by_category)`
  - `summarize(transactions)`, `totals_by_category(transactions, transaction_type)`, `build_period_report(start, end, transactions)`
  - `tests/helpers.py`: `START`, `END`, `make_transaction(type_=OUTFLOW, date=datetime(2026,11,1,9,30), items=(("food",100.0),), id=None, **fields)`

- [ ] **Step 1: Viết test**

`tests/helpers.py`:
```python
from datetime import datetime

from app.domain.entities import Transaction, TransactionItem, TransactionType

START = datetime(2026, 11, 1)
END = datetime(2026, 11, 30, 23, 59, 59)


def make_transaction(type_=TransactionType.OUTFLOW, date=datetime(2026, 11, 1, 9, 30),
                     items=(("food", 100.0),), id=None, **fields):
    return Transaction(
        type=type_,
        date=date,
        items=tuple(TransactionItem(key, amount) for key, amount in items),
        id=id,
        **fields,
    )
```

`tests/test_entities.py`:
```python
import unittest

from app.domain.entities import InvalidTransaction
from tests.helpers import make_transaction


class TransactionTest(unittest.TestCase):
    def test_total_sums_item_amounts(self):
        transaction = make_transaction(items=(("food", 100.0), ("bills", 50.5)))
        self.assertEqual(transaction.total, 150.5)

    def test_rejects_transaction_without_items(self):
        with self.assertRaises(InvalidTransaction):
            make_transaction(items=())

    def test_rejects_non_positive_amount(self):
        with self.assertRaises(InvalidTransaction):
            make_transaction(items=(("food", 0.0),))

    def test_rejects_blank_category(self):
        with self.assertRaises(InvalidTransaction):
            make_transaction(items=(("   ", 10.0),))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_categories.py`:
```python
import unicodedata
import unittest

from app.domain.categories import (
    DEFAULT_CATEGORIES, LEGACY_NAME_TO_KEY, is_legacy_name, legacy_name_to_key,
)


class LegacyNameToKeyTest(unittest.TestCase):
    def test_maps_every_seeded_vietnamese_name(self):
        # Copy nguyên văn từ database/db_manager.py (baseline a2c701f)
        seeded = {
            "Lương": "salary", "Thưởng": "bonus", "Thu nhập thụ động": "passive_income",
            "Bán hàng": "sales", "Khác": "other", "Ăn uống": "food", "Hóa đơn": "bills",
            "Di chuyển": "transport", "Mua sắm": "shopping", "Sức khỏe": "health",
            "Giải trí": "entertainment",
        }
        for name, key in seeded.items():
            self.assertEqual(legacy_name_to_key(name), key, name)

    def test_decomposed_unicode_still_matches(self):
        self.assertEqual(legacy_name_to_key(unicodedata.normalize("NFD", "Ăn uống")), "food")

    def test_unknown_name_becomes_its_own_key(self):
        self.assertEqual(legacy_name_to_key("Cà phê"), "Cà phê")
        self.assertFalse(is_legacy_name("Cà phê"))

    def test_missing_name_becomes_other(self):
        self.assertEqual(legacy_name_to_key(""), "other")
        self.assertEqual(legacy_name_to_key(None), "other")

    def test_default_keys_match_legacy_mapping(self):
        defaults = {key for keys in DEFAULT_CATEGORIES.values() for key in keys}
        self.assertEqual(defaults, set(LEGACY_NAME_TO_KEY.values()))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_summary.py`:
```python
import unittest

from app.domain.entities import TransactionType
from app.domain.summary import CategoryTotal, build_period_report, summarize, totals_by_category
from tests.helpers import END, START, make_transaction


class SummaryTest(unittest.TestCase):
    def setUp(self):
        self.transactions = [
            make_transaction(TransactionType.INFLOW, items=(("salary", 1000.0),)),
            make_transaction(TransactionType.OUTFLOW, items=(("food", 100.0), ("bills", 300.0))),
            make_transaction(TransactionType.OUTFLOW, items=(("food", 250.0),)),
        ]

    def test_summarize(self):
        summary = summarize(self.transactions)
        self.assertEqual((summary.inflow, summary.outflow, summary.balance), (1000.0, 650.0, 350.0))

    def test_summarize_empty(self):
        self.assertEqual(summarize([]).balance, 0)

    def test_totals_by_category_groups_filters_and_sorts_descending(self):
        self.assertEqual(
            totals_by_category(self.transactions, TransactionType.OUTFLOW),
            [CategoryTotal("food", 350.0), CategoryTotal("bills", 300.0)],
        )

    def test_build_period_report(self):
        report = build_period_report(START, END, self.transactions)
        self.assertEqual(report.summary.outflow, 650.0)
        self.assertEqual(report.inflow_by_category, [CategoryTotal("salary", 1000.0)])
        self.assertEqual((report.start, report.end), (START, END))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: lỗi `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implement**

`app/__init__.py`, `app/domain/__init__.py`, `tests/__init__.py`: file rỗng.

`app/domain/entities.py`:
```python
"""Thực thể nghiệp vụ: giao dịch thu/chi gồm nhiều hạng mục."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TransactionType(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class InvalidTransaction(ValueError):
    """Giao dịch không hợp lệ: không có hạng mục, thiếu danh mục hoặc số tiền <= 0."""


@dataclass(frozen=True)
class TransactionItem:
    category_key: str
    amount: float
    note: str = ""


@dataclass(frozen=True)
class Transaction:
    type: TransactionType
    date: datetime
    items: tuple[TransactionItem, ...]
    general_note: str = ""
    contact_person: str = ""
    receipt_path: str = ""  # tương đối với thư mục app, vd "assets/receipts/x.png"
    id: str | None = None

    def __post_init__(self):
        if not self.items:
            raise InvalidTransaction("A transaction needs at least one item")
        for item in self.items:
            if not item.category_key.strip():
                raise InvalidTransaction("Every item needs a category")
            if item.amount <= 0:
                raise InvalidTransaction("Item amounts must be positive")

    @property
    def total(self) -> float:
        return sum(item.amount for item in self.items)
```

`app/domain/categories.py`:
```python
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
```

`app/domain/summary.py`:
```python
"""Tính toán tổng hợp cho một kỳ: tổng thu/chi và tổng theo danh mục."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from app.domain.entities import Transaction, TransactionType


@dataclass(frozen=True)
class PeriodSummary:
    inflow: float
    outflow: float

    @property
    def balance(self) -> float:
        return self.inflow - self.outflow


@dataclass(frozen=True)
class CategoryTotal:
    category_key: str
    total: float


@dataclass(frozen=True)
class PeriodReport:
    start: datetime
    end: datetime
    transactions: list[Transaction]
    summary: PeriodSummary
    inflow_by_category: list[CategoryTotal]
    outflow_by_category: list[CategoryTotal]


def summarize(transactions: list[Transaction]) -> PeriodSummary:
    def total_of(transaction_type: TransactionType) -> float:
        return sum(t.total for t in transactions if t.type == transaction_type)

    return PeriodSummary(inflow=total_of(TransactionType.INFLOW), outflow=total_of(TransactionType.OUTFLOW))


def totals_by_category(transactions: list[Transaction], transaction_type: TransactionType) -> list[CategoryTotal]:
    totals: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.type == transaction_type:
            for item in transaction.items:
                totals[item.category_key] += item.amount
    return sorted((CategoryTotal(key, total) for key, total in totals.items()),
                  key=lambda category: category.total, reverse=True)


def build_period_report(start: datetime, end: datetime, transactions: list[Transaction]) -> PeriodReport:
    return PeriodReport(
        start=start,
        end=end,
        transactions=transactions,
        summary=summarize(transactions),
        inflow_by_category=totals_by_category(transactions, TransactionType.INFLOW),
        outflow_by_category=totals_by_category(transactions, TransactionType.OUTFLOW),
    )
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: 13 tests OK

---

### Task 2: Application (ports + services)

**Files:**
- Create: `app/application/__init__.py` (rỗng), `app/application/ports.py`, `app/application/transaction_service.py`, `app/application/report_service.py`
- Modify: `tests/helpers.py` (thêm fakes)
- Test: `tests/test_transaction_service.py`, `tests/test_report_service.py`

**Interfaces:**
- Consumes: Task 1
- Produces:
  - `TransactionRepository.list_between/get/add/update/delete`
  - `CategoryRepository.list_keys(transaction_type) -> list[str]`
  - `ReceiptStorage.save(source_path) -> str`, `ReceiptStorage.resolve(stored_path) -> str | None`
  - `ReportExporter.export(report: PeriodReport, path: str) -> None`
  - `TransactionService(transactions, categories, receipts)` gồm `.load_period(start, end) -> PeriodReport`, `.get(id)`, `.delete(id)`, `.save(transaction, new_receipt_source=None) -> str`, `.category_keys(transaction_type) -> list[str]`, `.resolve_receipt(stored_path) -> str | None`
  - `ReportService(transaction_service, exporter)` gồm `.export(start, end, path)`
  - `NoDataError(Exception)`

- [ ] **Step 1: Thêm fakes vào cuối `tests/helpers.py`**

```python
import os
from dataclasses import replace


class FakeTransactionRepository:
    def __init__(self, transactions=()):
        self.items = {t.id: t for t in transactions}
        self.list_calls = 0
        self._next_id = 1

    def list_between(self, start, end):
        self.list_calls += 1
        matching = [t for t in self.items.values() if start <= t.date <= end]
        return sorted(matching, key=lambda t: t.date, reverse=True)

    def get(self, transaction_id):
        return self.items.get(transaction_id)

    def add(self, transaction):
        new_id = f"new{self._next_id}"
        self._next_id += 1
        self.items[new_id] = replace(transaction, id=new_id)
        return new_id

    def update(self, transaction):
        self.items[transaction.id] = transaction

    def delete(self, transaction_id):
        del self.items[transaction_id]


class FakeCategoryRepository:
    def __init__(self, keys_by_type):
        self.keys_by_type = keys_by_type
        self.calls = 0

    def list_keys(self, transaction_type):
        self.calls += 1
        return list(self.keys_by_type.get(transaction_type, []))


class FakeReceiptStorage:
    def __init__(self, fail=False):
        self.fail = fail

    def save(self, source_path):
        if self.fail:
            raise OSError("disk full")
        return f"assets/receipts/{os.path.basename(source_path)}"

    def resolve(self, stored_path):
        return stored_path or None
```

- [ ] **Step 2: Viết test**

`tests/test_transaction_service.py`:
```python
import unittest

from app.application.transaction_service import TransactionService
from app.domain.entities import TransactionType
from tests.helpers import (
    END, START, FakeCategoryRepository, FakeReceiptStorage, FakeTransactionRepository, make_transaction,
)


class TransactionServiceTest(unittest.TestCase):
    def setUp(self):
        self.repository = FakeTransactionRepository([make_transaction(id="a", items=(("food", 100.0),))])
        self.categories = FakeCategoryRepository({
            TransactionType.OUTFLOW: ["food", "bills"],
            TransactionType.INFLOW: ["salary"],
        })
        self.receipts = FakeReceiptStorage()
        self.service = TransactionService(self.repository, self.categories, self.receipts)

    def test_load_period_queries_repository_once(self):
        report = self.service.load_period(START, END)
        self.assertEqual(self.repository.list_calls, 1)
        self.assertEqual(report.summary.outflow, 100.0)
        self.assertEqual([c.category_key for c in report.outflow_by_category], ["food"])

    def test_save_without_id_adds(self):
        new_id = self.service.save(make_transaction(items=(("bills", 20.0),)))
        self.assertEqual(self.repository.get(new_id).total, 20.0)
        self.assertEqual(len(self.repository.items), 2)

    def test_save_with_id_updates(self):
        returned_id = self.service.save(make_transaction(id="a", items=(("food", 999.0),)))
        self.assertEqual(returned_id, "a")
        self.assertEqual(self.repository.get("a").total, 999.0)
        self.assertEqual(len(self.repository.items), 1)

    def test_save_stores_new_receipt_before_writing(self):
        new_id = self.service.save(make_transaction(), new_receipt_source="C:/photos/bill.png")
        self.assertEqual(self.repository.get(new_id).receipt_path, "assets/receipts/bill.png")

    def test_failed_receipt_copy_writes_nothing(self):
        self.receipts.fail = True
        with self.assertRaises(OSError):
            self.service.save(make_transaction(), new_receipt_source="bill.png")
        self.assertEqual(len(self.repository.items), 1)

    def test_category_keys_are_cached_per_type(self):
        self.service.category_keys(TransactionType.OUTFLOW)
        keys = self.service.category_keys(TransactionType.OUTFLOW)
        self.service.category_keys(TransactionType.INFLOW)
        self.assertEqual(keys, ["food", "bills"])
        self.assertEqual(self.categories.calls, 2)

    def test_delete(self):
        self.service.delete("a")
        self.assertIsNone(self.service.get("a"))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_report_service.py`:
```python
import unittest

from app.application.report_service import NoDataError, ReportService
from app.application.transaction_service import TransactionService
from tests.helpers import (
    END, START, FakeCategoryRepository, FakeReceiptStorage, FakeTransactionRepository, make_transaction,
)


class RecordingExporter:
    def __init__(self):
        self.calls = []

    def export(self, report, path):
        self.calls.append((report, path))


def make_report_service(transactions, exporter):
    service = TransactionService(FakeTransactionRepository(transactions), FakeCategoryRepository({}),
                                 FakeReceiptStorage())
    return ReportService(service, exporter)


class ReportServiceTest(unittest.TestCase):
    def test_raises_no_data_when_period_is_empty(self):
        exporter = RecordingExporter()
        with self.assertRaises(NoDataError):
            make_report_service([], exporter).export(START, END, "out.docx")
        self.assertEqual(exporter.calls, [])

    def test_passes_period_report_to_exporter(self):
        exporter = RecordingExporter()
        make_report_service([make_transaction(id="a")], exporter).export(START, END, "out.docx")
        report, path = exporter.calls[0]
        self.assertEqual(path, "out.docx")
        self.assertEqual([t.id for t in report.transactions], ["a"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Chạy test, xác nhận FAIL**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: `ModuleNotFoundError: No module named 'app.application'`

- [ ] **Step 4: Implement**

`app/application/__init__.py`: file rỗng.

`app/application/ports.py`:
```python
"""Các cổng (Protocol) mà tầng application cần từ bên ngoài. Infrastructure/presentation implement chúng."""
from datetime import datetime
from typing import Protocol

from app.domain.entities import Transaction, TransactionType
from app.domain.summary import PeriodReport


class TransactionRepository(Protocol):
    def list_between(self, start: datetime, end: datetime) -> list[Transaction]:
        """Giao dịch trong [start, end], mới nhất trước."""

    def get(self, transaction_id: str) -> Transaction | None: ...

    def add(self, transaction: Transaction) -> str:
        """Lưu giao dịch mới, trả về id."""

    def update(self, transaction: Transaction) -> None: ...

    def delete(self, transaction_id: str) -> None: ...


class CategoryRepository(Protocol):
    def list_keys(self, transaction_type: TransactionType) -> list[str]: ...


class ReceiptStorage(Protocol):
    def save(self, source_path: str) -> str:
        """Copy ảnh vào kho, trả về đường dẫn tương đối để lưu. Lỗi -> OSError."""

    def resolve(self, stored_path: str) -> str | None:
        """Đường dẫn tuyệt đối nếu file tồn tại, ngược lại None."""


class ReportExporter(Protocol):
    def export(self, report: PeriodReport, path: str) -> None: ...
```

`app/application/transaction_service.py`:
```python
"""Use case cho giao dịch: xem theo kỳ, thêm/sửa/xoá, danh mục, ảnh biên lai."""
from dataclasses import replace
from datetime import datetime

from app.application.ports import CategoryRepository, ReceiptStorage, TransactionRepository
from app.domain.entities import Transaction, TransactionType
from app.domain.summary import PeriodReport, build_period_report


class TransactionService:
    def __init__(self, transactions: TransactionRepository, categories: CategoryRepository,
                 receipts: ReceiptStorage):
        self._transactions = transactions
        self._categories = categories
        self._receipts = receipts
        self._category_cache: dict[TransactionType, list[str]] = {}

    def load_period(self, start: datetime, end: datetime) -> PeriodReport:
        """Đọc giao dịch của kỳ đúng một lần rồi tính mọi số liệu từ đó."""
        return build_period_report(start, end, self._transactions.list_between(start, end))

    def get(self, transaction_id: str) -> Transaction | None:
        return self._transactions.get(transaction_id)

    def delete(self, transaction_id: str) -> None:
        self._transactions.delete(transaction_id)

    def save(self, transaction: Transaction, new_receipt_source: str | None = None) -> str:
        """Thêm (id None) hoặc cập nhật giao dịch. Ảnh mới được lưu trước; lỗi ảnh thì không ghi gì."""
        if new_receipt_source:
            transaction = replace(transaction, receipt_path=self._receipts.save(new_receipt_source))
        if transaction.id is None:
            return self._transactions.add(transaction)
        self._transactions.update(transaction)
        return transaction.id

    def category_keys(self, transaction_type: TransactionType) -> list[str]:
        if transaction_type not in self._category_cache:
            self._category_cache[transaction_type] = self._categories.list_keys(transaction_type)
        return self._category_cache[transaction_type]

    def resolve_receipt(self, stored_path: str) -> str | None:
        return self._receipts.resolve(stored_path)
```

`app/application/report_service.py`:
```python
"""Use case xuất báo cáo cho một kỳ."""
from datetime import datetime

from app.application.ports import ReportExporter
from app.application.transaction_service import TransactionService


class NoDataError(Exception):
    """Kỳ được chọn không có giao dịch nào để xuất."""


class ReportService:
    def __init__(self, transaction_service: TransactionService, exporter: ReportExporter):
        self._transaction_service = transaction_service
        self._exporter = exporter

    def export(self, start: datetime, end: datetime, path: str) -> None:
        report = self._transaction_service.load_period(start, end)
        if not report.transactions:
            raise NoDataError
        self._exporter.export(report, path)
```

- [ ] **Step 5: Chạy test, xác nhận PASS**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: 22 tests OK

---

### Task 3: Infrastructure (config, mapping, receipts, Firestore)

**Files:**
- Create: `app/config.py`, `app/infrastructure/__init__.py` (rỗng), `app/infrastructure/firestore_mapping.py`, `app/infrastructure/receipt_storage.py`, `app/infrastructure/firestore_repository.py`
- Test: `tests/test_firestore_mapping.py`, `tests/test_receipt_storage.py`

**Interfaces:**
- Consumes: Task 1, các Protocol ở Task 2
- Produces:
  - `app.config`: `BASE_DIR`, `LOCALES_DIR`, `SETTINGS_PATH`, `FIREBASE_CREDENTIALS_PATH`, `BACKUPS_DIR`
  - `transaction_to_document(t) -> dict`, `transaction_from_document(doc_id, data) -> Transaction`, `category_key_from_document(data) -> str`
  - `LocalReceiptStorage(base_dir)`
  - `connect(credentials_path)` (Firestore client), `FirestoreTransactionRepository(client)`, `FirestoreCategoryRepository(client)` với method `.seed_defaults_if_empty()`

- [ ] **Step 1: Viết test**

`tests/test_firestore_mapping.py`:
```python
import unittest
from datetime import datetime, timezone

from app.domain.entities import Transaction, TransactionItem, TransactionType
from app.infrastructure.firestore_mapping import (
    category_key_from_document, transaction_from_document, transaction_to_document,
)


class FirestoreMappingTest(unittest.TestCase):
    def test_round_trip(self):
        original = Transaction(
            type=TransactionType.OUTFLOW, date=datetime(2026, 11, 1, 9, 30),
            items=(TransactionItem("food", 100.0, "trưa"),), general_note="n", contact_person="c",
            receipt_path="assets/receipts/a.png", id="x",
        )
        document = transaction_to_document(original)
        self.assertEqual(document["items"], [{"category_key": "food", "amount": 100.0, "item_note": "trưa"}])
        self.assertEqual(document["total_amount"], 100.0)
        self.assertEqual(document["type"], "outflow")
        self.assertEqual(document["image_path"], "assets/receipts/a.png")
        self.assertNotIn("id", document)
        self.assertEqual(transaction_from_document("x", document), original)

    def test_reads_legacy_document_without_category_key(self):
        data = {
            "type": "outflow", "total_amount": 50.0,
            "items": [{"category_name": "Ăn uống", "amount": 50.0, "item_note": ""}],
            "date": datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc),
            "general_note": "", "image_path": None, "contact_person": "",
        }
        transaction = transaction_from_document("old", data)
        self.assertEqual(transaction.items[0].category_key, "food")
        self.assertEqual(transaction.receipt_path, "")
        self.assertEqual(transaction.date, datetime(2026, 11, 2, 8, 0))
        self.assertIsNone(transaction.date.tzinfo)

    def test_category_key_prefers_key_then_legacy_name(self):
        self.assertEqual(category_key_from_document({"key": "food", "name": "Ăn uống"}), "food")
        self.assertEqual(category_key_from_document({"name": "Giải trí"}), "entertainment")
        self.assertEqual(category_key_from_document({"name": "Cà phê"}), "Cà phê")


if __name__ == "__main__":
    unittest.main()
```

`tests/test_receipt_storage.py`:
```python
import os
import unittest
from tempfile import TemporaryDirectory

from app.infrastructure.receipt_storage import LocalReceiptStorage


class LocalReceiptStorageTest(unittest.TestCase):
    def setUp(self):
        self._base = TemporaryDirectory()
        self._sources = TemporaryDirectory()
        self.base = self._base.name
        self.storage = LocalReceiptStorage(self.base)
        self.source = os.path.join(self._sources.name, "bill.png")
        with open(self.source, "wb") as file:
            file.write(b"img")

    def tearDown(self):
        self._base.cleanup()
        self._sources.cleanup()

    def test_save_copies_file_and_returns_relative_path(self):
        stored = self.storage.save(self.source)
        self.assertTrue(stored.startswith("assets/receipts/"))
        self.assertTrue(stored.endswith("_bill.png"))
        self.assertEqual(self.storage.resolve(stored), os.path.normpath(os.path.join(self.base, stored)))

    def test_save_missing_source_raises_oserror(self):
        with self.assertRaises(OSError):
            self.storage.save(os.path.join(self.base, "missing.png"))

    def test_resolve_absolute_path(self):
        self.assertEqual(self.storage.resolve(self.source), os.path.normpath(self.source))

    def test_resolve_empty_or_missing_returns_none(self):
        self.assertIsNone(self.storage.resolve(""))
        self.assertIsNone(self.storage.resolve("assets/receipts/missing.png"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: `ModuleNotFoundError: No module named 'app.infrastructure'`

- [ ] **Step 3: Implement**

`app/config.py`:
```python
"""Đường dẫn tuyệt đối, tính theo thư mục chứa app (thư mục gốc repo, hoặc thư mục dist của Nuitka)."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(BASE_DIR, "locales")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
```

`app/infrastructure/__init__.py`: file rỗng.

`app/infrastructure/firestore_mapping.py`:
```python
"""Chuyển đổi giữa document Firestore và entity. Tên field Firestore chỉ xuất hiện ở file này."""
from datetime import datetime

from app.domain.categories import legacy_name_to_key
from app.domain.entities import Transaction, TransactionItem, TransactionType


def transaction_to_document(transaction: Transaction) -> dict:
    return {
        "type": transaction.type.value,
        "total_amount": transaction.total,  # giữ để tương thích dữ liệu cũ
        "items": [
            {"category_key": item.category_key, "amount": item.amount, "item_note": item.note}
            for item in transaction.items
        ],
        "date": transaction.date,
        "general_note": transaction.general_note,
        "image_path": transaction.receipt_path,
        "contact_person": transaction.contact_person,
    }


def transaction_from_document(doc_id: str, data: dict) -> Transaction:
    return Transaction(
        type=TransactionType(data["type"]),
        date=_as_naive(data["date"]),
        items=tuple(_item_from_document(item) for item in data.get("items", [])),
        general_note=data.get("general_note") or "",
        contact_person=data.get("contact_person") or "",
        receipt_path=data.get("image_path") or "",
        id=doc_id,
    )


def category_key_from_document(data: dict) -> str:
    return data.get("key") or legacy_name_to_key(data.get("name"))


def _item_from_document(item: dict) -> TransactionItem:
    return TransactionItem(
        category_key=item.get("category_key") or legacy_name_to_key(item.get("category_name")),
        amount=float(item.get("amount", 0)),
        note=item.get("item_note") or "",
    )


def _as_naive(value: datetime) -> datetime:
    # App luôn ghi datetime naive (giờ máy), Firestore trả về cùng giá trị nhưng gắn UTC.
    # Bỏ tzinfo để giữ nguyên giờ hiển thị như phiên bản cũ.
    return value.replace(tzinfo=None) if value.tzinfo else value
```

`app/infrastructure/receipt_storage.py`:
```python
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
```

`app/infrastructure/firestore_repository.py`:
```python
"""Repository Firestore. Không có test tự động (cần Firebase thật) — logic chuyển đổi nằm ở firestore_mapping."""
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

from app.domain.categories import DEFAULT_CATEGORIES
from app.domain.entities import Transaction, TransactionType
from app.infrastructure.firestore_mapping import (
    category_key_from_document, transaction_from_document, transaction_to_document,
)


def connect(credentials_path: str):
    """Khởi tạo Firebase (một lần) và trả về Firestore client."""
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(credentials_path))
    return firestore.client()


class FirestoreTransactionRepository:
    def __init__(self, client):
        self._collection = client.collection("transactions")

    def list_between(self, start: datetime, end: datetime) -> list[Transaction]:
        query = (
            self._collection
            .where(filter=firestore.FieldFilter("date", ">=", start))
            .where(filter=firestore.FieldFilter("date", "<=", end))
            .order_by("date", direction=firestore.Query.DESCENDING)
        )
        return [transaction_from_document(doc.id, doc.to_dict()) for doc in query.stream()]

    def get(self, transaction_id: str) -> Transaction | None:
        doc = self._collection.document(transaction_id).get()
        return transaction_from_document(doc.id, doc.to_dict()) if doc.exists else None

    def add(self, transaction: Transaction) -> str:
        document = transaction_to_document(transaction) | {"created_at": datetime.now()}
        _, reference = self._collection.add(document)
        return reference.id

    def update(self, transaction: Transaction) -> None:
        document = transaction_to_document(transaction) | {"updated_at": datetime.now()}
        self._collection.document(transaction.id).update(document)

    def delete(self, transaction_id: str) -> None:
        self._collection.document(transaction_id).delete()


class FirestoreCategoryRepository:
    def __init__(self, client):
        self._collection = client.collection("categories")

    def seed_defaults_if_empty(self) -> None:
        if self._collection.limit(1).get():
            return
        for transaction_type, keys in DEFAULT_CATEGORIES.items():
            for key in keys:
                self._collection.add({"key": key, "type": transaction_type.value})

    def list_keys(self, transaction_type: TransactionType) -> list[str]:
        query = self._collection.where(filter=firestore.FieldFilter("type", "==", transaction_type.value))
        keys = [category_key_from_document(doc.to_dict()) for doc in query.stream()]
        return list(dict.fromkeys(keys))  # bỏ trùng, giữ thứ tự
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: 29 tests OK

- [ ] **Step 5: Kiểm tra module Firestore import được, không cần kết nối**

Run: `.venv/Scripts/python.exe -c "import app.infrastructure.firestore_repository; print('ok')"`
Expected: `ok`

---

### Task 4: i18n, locales, formatters

**Files:**
- Create: `app/presentation/__init__.py` (rỗng), `app/presentation/i18n.py`, `app/presentation/formatters.py`, `locales/vi.json`, `locales/en.json`
- Test: `tests/test_i18n.py`, `tests/test_formatters.py`

**Interfaces:**
- Consumes: `app.config.LOCALES_DIR`, `app.config.SETTINGS_PATH`, Task 1
- Produces:
  - `Translator(locales_dir, language)` với `.t(key, **params)`
  - `SUPPORTED_LANGUAGES`, `load_language(path)`, `save_language(path, language)`
  - `t(key, **params)`, `current_language()`, `set_language(language, persist=True)`
  - `format_money(amount, language=None)`, `parse_money(text) -> float`, `format_date(value) -> str`
  - `category_label(key) -> str`, `type_label(transaction_type)`, `type_long_label(transaction_type)`
  - `combine_date_keep_time(new_date, original) -> datetime`

- [ ] **Step 1: Viết test**

`tests/test_i18n.py`:
```python
import json
import os
import unittest
from tempfile import TemporaryDirectory

from app.config import LOCALES_DIR
from app.domain.categories import DEFAULT_CATEGORIES
from app.presentation.i18n import Translator, load_language, save_language


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)


class TranslatorTest(unittest.TestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        write_json(os.path.join(self._dir.name, "vi.json"), {"greet": "Xin chào {name}", "only_vi": "Chỉ có vi"})
        write_json(os.path.join(self._dir.name, "en.json"), {"greet": "Hello {name}"})

    def tearDown(self):
        self._dir.cleanup()

    def test_uses_current_language_with_params(self):
        self.assertEqual(Translator(self._dir.name, "en").t("greet", name="An"), "Hello An")
        self.assertEqual(Translator(self._dir.name, "vi").t("greet", name="An"), "Xin chào An")

    def test_falls_back_to_vietnamese_then_to_key(self):
        translator = Translator(self._dir.name, "en")
        self.assertEqual(translator.t("only_vi"), "Chỉ có vi")
        self.assertEqual(translator.t("missing.key"), "missing.key")


class LanguageSettingsTest(unittest.TestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        self.path = os.path.join(self._dir.name, "settings.json")

    def tearDown(self):
        self._dir.cleanup()

    def test_save_then_load(self):
        save_language(self.path, "en")
        self.assertEqual(load_language(self.path), "en")

    def test_defaults_to_vi_for_missing_broken_or_unsupported_settings(self):
        self.assertEqual(load_language(self.path), "vi")
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("{broken")
        self.assertEqual(load_language(self.path), "vi")
        write_json(self.path, {"language": "fr"})
        self.assertEqual(load_language(self.path), "vi")


class LocaleFilesTest(unittest.TestCase):
    def load(self, language):
        with open(os.path.join(LOCALES_DIR, f"{language}.json"), encoding="utf-8") as file:
            return json.load(file)

    def test_vi_and_en_have_the_same_keys(self):
        self.assertEqual(set(self.load("vi")), set(self.load("en")))

    def test_every_default_category_has_a_translation(self):
        vi = self.load("vi")
        for keys in DEFAULT_CATEGORIES.values():
            for key in keys:
                self.assertIn(f"category.{key}", vi)


if __name__ == "__main__":
    unittest.main()
```

`tests/test_formatters.py`:
```python
import unittest
from datetime import date, datetime

from app.domain.entities import TransactionType
from app.presentation.formatters import (
    category_label, combine_date_keep_time, format_date, format_money, parse_money, type_label,
)
from app.presentation.i18n import set_language


class FormattersTest(unittest.TestCase):
    def setUp(self):
        set_language("vi", persist=False)

    def tearDown(self):
        set_language("vi", persist=False)

    def test_format_money_per_language(self):
        self.assertEqual(format_money(1500000, "vi"), "1.500.000 đ")
        self.assertEqual(format_money(1500000, "en"), "1,500,000 VND")
        self.assertEqual(format_money(-2000, "vi"), "-2.000 đ")

    def test_format_money_uses_current_language_by_default(self):
        set_language("en", persist=False)
        self.assertEqual(format_money(1000), "1,000 VND")

    def test_parse_money_accepts_both_styles(self):
        for text in ("1.500.000 đ", "1,500,000 VND", "1500000", " 1 500 000 "):
            self.assertEqual(parse_money(text), 1500000.0, text)
        self.assertEqual(parse_money(""), 0.0)
        self.assertEqual(parse_money("abc"), 0.0)

    def test_category_label_translates_known_keys_and_keeps_custom(self):
        self.assertEqual(category_label("food"), "Ăn uống")
        self.assertEqual(category_label("Cà phê"), "Cà phê")
        set_language("en", persist=False)
        self.assertEqual(category_label("food"), "Food & drinks")

    def test_type_label(self):
        self.assertEqual(type_label(TransactionType.INFLOW), "Thu")

    def test_format_date(self):
        self.assertEqual(format_date(datetime(2026, 1, 5, 10, 0)), "05/01/2026")

    def test_combine_date_keeps_original_time(self):
        result = combine_date_keep_time(date(2026, 11, 5), datetime(2026, 10, 1, 14, 25, 7))
        self.assertEqual(result, datetime(2026, 11, 5, 14, 25, 7))

    def test_combine_date_without_original_uses_given_date(self):
        self.assertEqual(combine_date_keep_time(date(2026, 11, 5), None).date(), date(2026, 11, 5))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: `ModuleNotFoundError: No module named 'app.presentation'`

- [ ] **Step 3: Implement**

`app/presentation/__init__.py`: file rỗng.

`app/presentation/i18n.py`:
```python
"""Dịch chuỗi giao diện. Tra theo thứ tự: ngôn ngữ hiện tại -> tiếng Việt -> chính key."""
import json
import os

from app.config import LOCALES_DIR, SETTINGS_PATH

SUPPORTED_LANGUAGES = ("vi", "en")
DEFAULT_LANGUAGE = "vi"


class Translator:
    def __init__(self, locales_dir: str, language: str = DEFAULT_LANGUAGE):
        self._locales_dir = locales_dir
        self._catalogs: dict[str, dict[str, str]] = {}
        self.language = language

    def t(self, key: str, **params) -> str:
        text = (self._catalog(self.language).get(key)
                or self._catalog(DEFAULT_LANGUAGE).get(key)
                or key)
        return text.format(**params) if params else text

    def _catalog(self, language: str) -> dict[str, str]:
        if language not in self._catalogs:
            try:
                with open(os.path.join(self._locales_dir, f"{language}.json"), encoding="utf-8") as file:
                    self._catalogs[language] = json.load(file)
            except (OSError, ValueError):
                self._catalogs[language] = {}
        return self._catalogs[language]


def load_language(settings_path: str) -> str:
    try:
        with open(settings_path, encoding="utf-8") as file:
            language = json.load(file).get("language")
    except (OSError, ValueError, AttributeError):
        return DEFAULT_LANGUAGE
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def save_language(settings_path: str, language: str) -> None:
    with open(settings_path, "w", encoding="utf-8") as file:
        json.dump({"language": language}, file)


_translator = Translator(LOCALES_DIR, load_language(SETTINGS_PATH))


def t(key: str, **params) -> str:
    return _translator.t(key, **params)


def current_language() -> str:
    return _translator.language


def set_language(language: str, persist: bool = True) -> None:
    _translator.language = language
    if persist:
        save_language(SETTINGS_PATH, language)
```

`app/presentation/formatters.py`:
```python
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
```

`locales/vi.json`:
```json
{
  "dialog.error": "Lỗi",
  "dialog.warning": "Cảnh báo",
  "dialog.success": "Thành công",
  "dialog.confirm": "Xác nhận",
  "dialog.close": "Đóng",
  "dialog.all_files": "Tất cả tệp",
  "error.invalid_transaction": "Vui lòng nhập danh mục và số tiền hợp lệ cho ít nhất 1 hạng mục.",
  "error.no_data": "Không có giao dịch nào trong khoảng thời gian này.",
  "error.invalid_date": "Ngày không hợp lệ.",
  "error.file": "Không đọc/ghi được tệp:\n{detail}",
  "error.generic": "Đã xảy ra lỗi (vui lòng kiểm tra kết nối mạng):\n{detail}",
  "loading.title": "Khởi động ứng dụng",
  "loading.connecting": "Đang kết nối đến Firebase...",
  "loading.reconnecting": "Đang kết nối lại...",
  "loading.error": "Lỗi kết nối Firebase!\nVui lòng kiểm tra kết nối mạng hoặc file serviceAccountKey.json.",
  "loading.retry": "Thử lại",
  "loading.exit": "Thoát",
  "menu.language": "Ngôn ngữ / Language",
  "language.vi": "Tiếng Việt",
  "language.en": "English",
  "main.title": "Phần mềm Quản lý Chi tiêu",
  "main.from": "Từ ngày:",
  "main.to": "Đến ngày:",
  "main.filter": "Lọc",
  "main.export_word": "Xuất Báo Cáo Word",
  "main.add": "+ Thêm Giao Dịch",
  "main.summary": "Tổng quan trong kỳ",
  "main.col_date": "Ngày",
  "main.col_type": "Loại",
  "main.col_category": "Danh mục chi tiết",
  "main.col_amount": "Tổng số tiền",
  "main.col_note": "Ghi chú chung",
  "main.view": "Xem chi tiết",
  "main.edit": "Sửa",
  "main.delete": "Xóa",
  "main.chart": "Xem Biểu Đồ Chi Tiêu",
  "main.select_first": "Vui lòng chọn một giao dịch.",
  "main.confirm_delete": "Bạn có chắc chắn muốn xóa giao dịch này?",
  "main.deleted": "Đã xóa giao dịch.",
  "summary.inflow": "Tổng Thu: {amount}",
  "summary.outflow": "Tổng Chi: {amount}",
  "summary.balance": "Số Dư: {amount}",
  "type.inflow": "Thu",
  "type.outflow": "Chi",
  "type_long.inflow": "Khoản Thu",
  "type_long.outflow": "Khoản Chi",
  "form.title_add": "Thêm Giao Dịch Mới",
  "form.title_edit": "Sửa Giao Dịch",
  "form.type_frame": "Loại giao dịch",
  "form.general_frame": "Thông tin chung",
  "form.date": "Ngày:",
  "form.contact": "Đối tác:",
  "form.note": "Ghi chú chung:",
  "form.items_frame": "Chi tiết hạng mục",
  "form.col_category": "Danh mục",
  "form.col_amount": "Số tiền",
  "form.col_note": "Ghi chú",
  "form.add_item": "+ Thêm hạng mục",
  "form.choose_receipt": "Chọn ảnh biên lai",
  "form.no_receipt": "Chưa chọn ảnh",
  "form.image_files": "Tệp ảnh",
  "form.total": "Tổng cộng: {amount}",
  "form.save_new": "Xác Nhận",
  "form.save_edit": "Lưu Thay Đổi",
  "form.added": "Đã thêm giao dịch!",
  "form.updated": "Đã cập nhật giao dịch!",
  "detail.title": "Chi Tiết Giao Dịch",
  "detail.general": "Thông tin chung",
  "detail.type": "Loại giao dịch: {value}",
  "detail.date": "Ngày giờ: {value}",
  "detail.total": "Tổng số tiền: {value}",
  "detail.contact": "Đối tác: {value}",
  "detail.note": "Ghi chú chung: {value}",
  "detail.items": "Hạng mục chi tiết",
  "detail.receipt": "Biên lai",
  "detail.receipt_error": "Không thể tải ảnh biên lai",
  "chart.window_title": "Biểu đồ Thu/Chi",
  "chart.heading": "Thống kê giao dịch từ {start} đến {end}",
  "chart.no_data": "Không có dữ liệu",
  "chart.no_data_period": "Không có dữ liệu trong khoảng thời gian này.",
  "chart.inflow_title": "Tổng Thu Theo Hạng Mục",
  "chart.outflow_title": "Tổng Chi Theo Hạng Mục",
  "chart.y_label": "Số tiền (VND)",
  "report.title": "BÁO CÁO QUẢN LÝ CHI TIÊU",
  "report.period": "Từ ngày: {start} - Đến ngày: {end}",
  "report.exported_at": "Ngày xuất báo cáo: {time}",
  "report.section_overview": "1. Tổng quan",
  "report.section_charts": "2. Biểu đồ thống kê",
  "report.section_details": "3. Bảng kê chi tiết",
  "report.balance": "Số dư trong kỳ: {amount}",
  "report.col_date": "Ngày",
  "report.col_type": "Loại",
  "report.col_items": "Hạng mục chi tiết",
  "report.col_total": "Tổng tiền",
  "report.col_note": "Ghi chú chung",
  "report.item_purpose": " (Mục đích: {note})",
  "report.file_prefix": "BaoCaoChiTieu",
  "report.file_type": "Tài liệu Word",
  "report.save_title": "Chọn vị trí lưu báo cáo",
  "report.exported": "Đã xuất báo cáo tại:\n{path}",
  "category.salary": "Lương",
  "category.bonus": "Thưởng",
  "category.passive_income": "Thu nhập thụ động",
  "category.sales": "Bán hàng",
  "category.other": "Khác",
  "category.food": "Ăn uống",
  "category.bills": "Hóa đơn",
  "category.transport": "Di chuyển",
  "category.shopping": "Mua sắm",
  "category.health": "Sức khỏe",
  "category.entertainment": "Giải trí"
}
```

`locales/en.json`:
```json
{
  "dialog.error": "Error",
  "dialog.warning": "Warning",
  "dialog.success": "Success",
  "dialog.confirm": "Confirm",
  "dialog.close": "Close",
  "dialog.all_files": "All files",
  "error.invalid_transaction": "Please enter a category and a valid amount for at least one item.",
  "error.no_data": "There are no transactions in this period.",
  "error.invalid_date": "Invalid date.",
  "error.file": "Could not read/write the file:\n{detail}",
  "error.generic": "Something went wrong (please check your network connection):\n{detail}",
  "loading.title": "Starting application",
  "loading.connecting": "Connecting to Firebase...",
  "loading.reconnecting": "Reconnecting...",
  "loading.error": "Could not connect to Firebase!\nPlease check your network connection or serviceAccountKey.json.",
  "loading.retry": "Retry",
  "loading.exit": "Exit",
  "menu.language": "Ngôn ngữ / Language",
  "language.vi": "Tiếng Việt",
  "language.en": "English",
  "main.title": "Expense Manager",
  "main.from": "From:",
  "main.to": "To:",
  "main.filter": "Filter",
  "main.export_word": "Export Word Report",
  "main.add": "+ Add Transaction",
  "main.summary": "Period overview",
  "main.col_date": "Date",
  "main.col_type": "Type",
  "main.col_category": "Categories",
  "main.col_amount": "Total",
  "main.col_note": "Note",
  "main.view": "View details",
  "main.edit": "Edit",
  "main.delete": "Delete",
  "main.chart": "View Charts",
  "main.select_first": "Please select a transaction.",
  "main.confirm_delete": "Are you sure you want to delete this transaction?",
  "main.deleted": "Transaction deleted.",
  "summary.inflow": "Total income: {amount}",
  "summary.outflow": "Total expense: {amount}",
  "summary.balance": "Balance: {amount}",
  "type.inflow": "Income",
  "type.outflow": "Expense",
  "type_long.inflow": "Income",
  "type_long.outflow": "Expense",
  "form.title_add": "New Transaction",
  "form.title_edit": "Edit Transaction",
  "form.type_frame": "Transaction type",
  "form.general_frame": "General information",
  "form.date": "Date:",
  "form.contact": "Payee:",
  "form.note": "Note:",
  "form.items_frame": "Items",
  "form.col_category": "Category",
  "form.col_amount": "Amount",
  "form.col_note": "Note",
  "form.add_item": "+ Add item",
  "form.choose_receipt": "Choose receipt image",
  "form.no_receipt": "No image selected",
  "form.image_files": "Image files",
  "form.total": "Total: {amount}",
  "form.save_new": "Save",
  "form.save_edit": "Save changes",
  "form.added": "Transaction added!",
  "form.updated": "Transaction updated!",
  "detail.title": "Transaction Details",
  "detail.general": "General information",
  "detail.type": "Type: {value}",
  "detail.date": "Date & time: {value}",
  "detail.total": "Total amount: {value}",
  "detail.contact": "Payee: {value}",
  "detail.note": "Note: {value}",
  "detail.items": "Items",
  "detail.receipt": "Receipt",
  "detail.receipt_error": "Could not load the receipt image",
  "chart.window_title": "Income/Expense Charts",
  "chart.heading": "Transactions from {start} to {end}",
  "chart.no_data": "No data",
  "chart.no_data_period": "No data in this period.",
  "chart.inflow_title": "Income by Category",
  "chart.outflow_title": "Expense by Category",
  "chart.y_label": "Amount (VND)",
  "report.title": "EXPENSE REPORT",
  "report.period": "From: {start} - To: {end}",
  "report.exported_at": "Exported at: {time}",
  "report.section_overview": "1. Overview",
  "report.section_charts": "2. Charts",
  "report.section_details": "3. Transaction details",
  "report.balance": "Period balance: {amount}",
  "report.col_date": "Date",
  "report.col_type": "Type",
  "report.col_items": "Items",
  "report.col_total": "Total",
  "report.col_note": "Note",
  "report.item_purpose": " (Purpose: {note})",
  "report.file_prefix": "ExpenseReport",
  "report.file_type": "Word Document",
  "report.save_title": "Choose where to save the report",
  "report.exported": "Report exported to:\n{path}",
  "category.salary": "Salary",
  "category.bonus": "Bonus",
  "category.passive_income": "Passive income",
  "category.sales": "Sales",
  "category.other": "Other",
  "category.food": "Food & drinks",
  "category.bills": "Bills",
  "category.transport": "Transport",
  "category.shopping": "Shopping",
  "category.health": "Health",
  "category.entertainment": "Entertainment"
}
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: 43 tests OK

---

### Task 5: Rendering (charts + Word exporter)

**Files:**
- Create: `app/presentation/charts.py`, `app/presentation/word_exporter.py`
- Test: `tests/test_charts.py`, `tests/test_word_exporter.py`

**Interfaces:**
- Consumes: Task 1 (`CategoryTotal`, `PeriodReport`, `build_period_report`), Task 4 (`t`, các formatter)
- Produces:
  - `plot_category_bars(ax, totals: list[CategoryTotal], title: str, color: str) -> None`
  - `WordReportExporter()` với `.export(report, path)`

- [ ] **Step 1: Viết test**

`tests/test_charts.py`:
```python
import unittest

from matplotlib.figure import Figure

from app.domain.summary import CategoryTotal
from app.presentation.charts import plot_category_bars
from app.presentation.i18n import set_language, t


class PlotCategoryBarsTest(unittest.TestCase):
    def setUp(self):
        set_language("vi", persist=False)

    def test_draws_one_bar_per_category_with_translated_labels(self):
        axes = Figure().subplots()
        plot_category_bars(axes, [CategoryTotal("food", 300.0), CategoryTotal("Cà phê", 100.0)], "T", "red")
        axes.figure.draw_without_rendering()  # tick label của trục phân loại chỉ có sau khi vẽ
        self.assertEqual(len(axes.patches), 2)
        self.assertEqual(axes.get_title(), "T")
        self.assertEqual([label.get_text() for label in axes.get_xticklabels()], ["Ăn uống", "Cà phê"])

    def test_empty_totals_show_no_data(self):
        axes = Figure().subplots()
        plot_category_bars(axes, [], "T", "red")
        self.assertFalse(axes.axison)
        self.assertEqual(axes.texts[0].get_text(), t("chart.no_data"))


if __name__ == "__main__":
    unittest.main()
```

`tests/test_word_exporter.py`:
```python
import os
import unittest
from tempfile import TemporaryDirectory

from docx import Document

from app.domain.entities import TransactionType
from app.domain.summary import build_period_report
from app.presentation.i18n import set_language
from app.presentation.word_exporter import WordReportExporter
from tests.helpers import END, START, make_transaction


class WordReportExporterTest(unittest.TestCase):
    def setUp(self):
        set_language("vi", persist=False)

    def test_exports_overview_charts_and_detail_rows(self):
        report = build_period_report(START, END, [
            make_transaction(id="a"),
            make_transaction(TransactionType.INFLOW, items=(("salary", 500.0),), id="b"),
        ])
        with TemporaryDirectory() as folder:
            path = os.path.join(folder, "report.docx")
            WordReportExporter().export(report, path)
            document = Document(path)

        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("BÁO CÁO QUẢN LÝ CHI TIÊU", text)
        self.assertIn("Tổng Thu: 500 đ", text)
        self.assertEqual(len(document.inline_shapes), 2)
        rows = document.tables[0].rows
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].cells[0].text, "Ngày")
        self.assertIn("Ăn uống", rows[1].cells[2].text + rows[2].cells[2].text)

    def test_exports_in_english(self):
        set_language("en", persist=False)
        report = build_period_report(START, END, [make_transaction(id="a")])
        with TemporaryDirectory() as folder:
            path = os.path.join(folder, "report.docx")
            WordReportExporter().export(report, path)
            document = Document(path)
        self.assertEqual(document.paragraphs[0].text, "EXPENSE REPORT")
        self.assertIn("Food & drinks", document.tables[0].rows[1].cells[2].text)
        set_language("vi", persist=False)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: `ModuleNotFoundError: No module named 'app.presentation.charts'`

- [ ] **Step 3: Implement**

`app/presentation/charts.py`:
```python
"""Biểu đồ cột tổng tiền theo danh mục — dùng chung cho cửa sổ biểu đồ và báo cáo Word."""
from matplotlib import ticker

from app.domain.summary import CategoryTotal
from app.presentation.formatters import category_label
from app.presentation.i18n import t


def plot_category_bars(axes, totals: list[CategoryTotal], title: str, color: str) -> None:
    axes.set_title(title)
    if not totals:
        axes.text(0.5, 0.5, t("chart.no_data"), ha="center", va="center")
        axes.axis("off")
        return

    values = [category.total for category in totals]
    bars = axes.bar([category_label(category.category_key) for category in totals], values, color=color)
    axes.set_ylabel(t("chart.y_label"))
    axes.set_ylim(0, max(values) * 1.2)  # chừa chỗ cho nhãn số phía trên cột
    axes.yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, _: f"{int(value):,}"))
    axes.tick_params(axis="x", rotation=45)
    for bar in bars:
        height = bar.get_height()
        axes.annotate(f"{height:,.0f}", xy=(bar.get_x() + bar.get_width() / 2, height),
                      xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
```

`app/presentation/word_exporter.py`:
```python
"""Xuất báo cáo kỳ ra file Word (implement ReportExporter)."""
import io
from datetime import datetime

from docx import Document
from docx.shared import Inches
from matplotlib.figure import Figure

from app.domain.entities import Transaction, TransactionItem
from app.domain.summary import CategoryTotal, PeriodReport, PeriodSummary
from app.presentation.charts import plot_category_bars
from app.presentation.formatters import category_label, format_date, format_money, type_label
from app.presentation.i18n import t

DETAIL_COLUMNS = ("report.col_date", "report.col_type", "report.col_items", "report.col_total", "report.col_note")


class WordReportExporter:
    def export(self, report: PeriodReport, path: str) -> None:
        document = Document()
        document.add_heading(t("report.title"), 0)
        document.add_paragraph(t("report.period", start=format_date(report.start), end=format_date(report.end)))
        document.add_paragraph(t("report.exported_at", time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        _add_overview(document, report.summary)
        _add_charts(document, report)
        _add_detail_table(document, report.transactions)
        document.save(path)


def _add_overview(document, summary: PeriodSummary) -> None:
    document.add_heading(t("report.section_overview"), level=1)
    paragraph = document.add_paragraph()
    paragraph.add_run(t("summary.inflow", amount=format_money(summary.inflow)) + "\n").bold = True
    paragraph.add_run(t("summary.outflow", amount=format_money(summary.outflow)) + "\n").bold = True
    paragraph.add_run(t("report.balance", amount=format_money(summary.balance))).bold = True


def _add_charts(document, report: PeriodReport) -> None:
    document.add_heading(t("report.section_charts"), level=1)
    for totals, title_key, color in ((report.inflow_by_category, "chart.inflow_title", "green"),
                                     (report.outflow_by_category, "chart.outflow_title", "red")):
        document.add_picture(_chart_png(totals, t(title_key), color), width=Inches(6.0))


def _add_detail_table(document, transactions: list[Transaction]) -> None:
    document.add_heading(t("report.section_details"), level=1)
    table = document.add_table(rows=1, cols=len(DETAIL_COLUMNS))
    table.style = "Table Grid"
    for cell, key in zip(table.rows[0].cells, DETAIL_COLUMNS):
        cell.text = t(key)
    for transaction in sorted(transactions, key=lambda tr: tr.date):  # báo cáo: cũ nhất trước
        cells = table.add_row().cells
        cells[0].text = format_date(transaction.date)
        cells[1].text = type_label(transaction.type)
        cells[2].text = "\n".join(_describe_item(item) for item in transaction.items)
        cells[3].text = format_money(transaction.total)
        cells[4].text = transaction.general_note


def _describe_item(item: TransactionItem) -> str:
    purpose = t("report.item_purpose", note=item.note) if item.note else ""
    return f"- {category_label(item.category_key)}{purpose}: {format_money(item.amount)}"


def _chart_png(totals: list[CategoryTotal], title: str, color: str) -> io.BytesIO:
    figure = Figure(figsize=(8, 5))
    plot_category_bars(figure.subplots(), totals, title, color)
    figure.tight_layout()
    image = io.BytesIO()
    figure.savefig(image, format="png", bbox_inches="tight")
    image.seek(0)
    return image
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: 47 tests OK

---

### Task 6: Presentation (Tkinter) + container + entry point + dọn code cũ

**Files:**
- Create: `app/presentation/ui_helpers.py`, `app/presentation/loading_window.py`, `app/presentation/main_window.py`, `app/presentation/transaction_form.py`, `app/presentation/transaction_detail.py`, `app/presentation/chart_view.py`, `app/container.py`
- Modify: `main.py` (viết lại), `build_exe.py`, `requirements.txt`
- Delete: `config.py`, `database/`, `services/`, `utils/`, `views/`, `.env.example`, `__pycache__/`

**Interfaces:**
- Consumes: Task 2, 3, 4, 5
- Produces:
  - `Services(transactions: TransactionService, reports: ReportService)`, `build_services() -> Services`
  - `reported_errors(parent)` (context manager), `make_date_entry(parent, value=None)`
  - `LoadingWindow(connect)` với thuộc tính `.result`
  - `MainWindow(services)`
  - `TransactionForm(parent, service, on_saved, transaction=None)`
  - `TransactionDetail(parent, transaction, receipt_file)`
  - `ChartView(parent, report)`

UI Tkinter không có test tự động (đã thống nhất trong spec mục 11). Logic của tầng này đã được test qua formatters, service và exporter. Task này được verify bằng import check, unittest và smoke test tay ở Step 5.

- [ ] **Step 1: Viết `app/presentation/ui_helpers.py`**

```python
"""Tiện ích dùng chung cho các cửa sổ Tkinter."""
from contextlib import contextmanager
from tkinter import messagebox

from tkcalendar import DateEntry

from app.application.report_service import NoDataError
from app.domain.entities import InvalidTransaction
from app.presentation.i18n import t


@contextmanager
def reported_errors(parent):
    """Bắt lỗi trong khối `with` và báo bằng messagebox đã dịch.

    Khi có lỗi, các dòng còn lại trong khối không chạy; chương trình tiếp tục sau khối.
    """
    try:
        yield
    except InvalidTransaction:
        messagebox.showerror(t("dialog.error"), t("error.invalid_transaction"), parent=parent)
    except NoDataError:
        messagebox.showerror(t("dialog.error"), t("error.no_data"), parent=parent)
    except (FileNotFoundError, PermissionError) as error:
        messagebox.showerror(t("dialog.error"), t("error.file", detail=error), parent=parent)
    except Exception as error:  # Firestore/mạng: báo cho người dùng thay vì chỉ in traceback
        messagebox.showerror(t("dialog.error"), t("error.generic", detail=error), parent=parent)


def make_date_entry(parent, value=None) -> DateEntry:
    entry = DateEntry(parent, width=12, background="darkblue", foreground="white", borderwidth=2,
                      date_pattern="dd/mm/yyyy")  # khớp formatters.DATE_FORMAT
    if value is not None:
        entry.set_date(value)
    return entry
```

- [ ] **Step 2: Viết các cửa sổ**

`app/presentation/loading_window.py`:
```python
"""Màn hình 'Đang kết nối...' chạy connect() ở thread nền, có Thử lại / Thoát khi lỗi."""
import threading
import tkinter as tk
from tkinter import ttk

from app.presentation.i18n import t

POLL_MS = 100


class LoadingWindow(tk.Tk):
    def __init__(self, connect):
        super().__init__()
        self._connect = connect
        self._outcome = None  # ("ok", value) | ("error", exception), ghi từ thread nền
        self.result = None

        self.title(t("loading.title"))
        self.geometry("400x150")
        self.eval("tk::PlaceWindow . center")
        self.resizable(False, False)

        self._label = ttk.Label(self, text=t("loading.connecting"), font=("Arial", 11))
        self._label.pack(expand=True, pady=(20, 5))
        self._progress = ttk.Progressbar(self, mode="indeterminate")
        self._progress.pack(fill=tk.X, padx=30, pady=(0, 20))
        self._buttons = None
        self._start()

    def _start(self):
        self._outcome = None
        self._progress.start()
        threading.Thread(target=self._run_connect, daemon=True).start()
        self.after(POLL_MS, self._poll)

    def _run_connect(self):
        try:
            self._outcome = ("ok", self._connect())
        except Exception as error:
            self._outcome = ("error", error)

    def _poll(self):
        # Tkinter không an toàn khi gọi từ thread khác, nên thread chính tự kiểm tra kết quả.
        if self._outcome is None:
            self.after(POLL_MS, self._poll)
            return
        status, value = self._outcome
        if status == "ok":
            self.result = value
            self.destroy()
        else:
            self._show_error()

    def _show_error(self):
        self._progress.stop()
        self._label.config(text=t("loading.error"), foreground="red")
        self._buttons = ttk.Frame(self)
        self._buttons.pack(pady=10)
        ttk.Button(self._buttons, text=t("loading.retry"), command=self._retry).pack(side=tk.LEFT, padx=5)
        ttk.Button(self._buttons, text=t("loading.exit"), command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _retry(self):
        self._buttons.destroy()
        self._label.config(text=t("loading.reconnecting"), foreground="black")
        self._start()
```

`app/presentation/main_window.py`:
```python
"""Cửa sổ chính: lọc theo kỳ, tổng quan, danh sách giao dịch, menu ngôn ngữ."""
import os
import tkinter as tk
from datetime import datetime, time
from tkinter import filedialog, messagebox, ttk

from app.domain.entities import Transaction
from app.domain.summary import PeriodReport
from app.presentation.chart_view import ChartView
from app.presentation.formatters import category_label, format_date, format_money, type_label
from app.presentation.i18n import SUPPORTED_LANGUAGES, current_language, set_language, t
from app.presentation.transaction_detail import TransactionDetail
from app.presentation.transaction_form import TransactionForm
from app.presentation.ui_helpers import make_date_entry, reported_errors

# (cột, độ rộng, căn lề)
COLUMNS = (("date", 100, tk.W), ("type", 80, tk.W), ("category", 300, tk.W),
           ("amount", 120, tk.E), ("note", 200, tk.W))
BOLD = ("Arial", 11, "bold")


class MainWindow(tk.Tk):
    def __init__(self, services):
        super().__init__()
        self._services = services
        self.geometry("900x600")
        now = datetime.now()
        self._start = datetime.combine(now.date().replace(day=1), time.min)
        self._end = datetime.combine(now.date(), time(23, 59, 59))
        self._report: PeriodReport | None = None
        self._build()
        self.refresh()

    # ---------- dựng giao diện (gọi lại khi đổi ngôn ngữ) ----------

    def _build(self):
        for child in self.winfo_children():
            if not isinstance(child, tk.Toplevel):  # cửa sổ con đang mở giữ nguyên
                child.destroy()
        self.title(t("main.title"))
        self._build_menu()
        self._build_filter_bar()
        self._build_summary()
        self._build_table()
        self._build_actions()

    def _build_menu(self):
        menubar = tk.Menu(self)
        language_menu = tk.Menu(menubar, tearoff=0)
        self._language = tk.StringVar(value=current_language())
        for code in SUPPORTED_LANGUAGES:
            language_menu.add_radiobutton(label=t(f"language.{code}"), value=code, variable=self._language,
                                          command=lambda c=code: self._change_language(c))
        menubar.add_cascade(label=t("menu.language"), menu=language_menu)
        self.config(menu=menubar)

    def _build_filter_bar(self):
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(bar, text=t("main.from")).pack(side=tk.LEFT, padx=5)
        self._date_from = make_date_entry(bar, self._start)
        self._date_from.pack(side=tk.LEFT, padx=5)
        ttk.Label(bar, text=t("main.to")).pack(side=tk.LEFT, padx=5)
        self._date_to = make_date_entry(bar, self._end)
        self._date_to.pack(side=tk.LEFT, padx=5)
        ttk.Button(bar, text=t("main.filter"), command=self._apply_filter).pack(side=tk.LEFT, padx=10)
        ttk.Button(bar, text=t("main.export_word"), command=self._export_report).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bar, text=t("main.add"), command=self._open_add_form).pack(side=tk.RIGHT, padx=5)

    def _build_summary(self):
        frame = ttk.LabelFrame(self, text=t("main.summary"))
        frame.pack(fill=tk.X, padx=10, pady=5)
        self._lbl_inflow = ttk.Label(frame, foreground="green", font=BOLD)
        self._lbl_outflow = ttk.Label(frame, foreground="red", font=BOLD)
        self._lbl_balance = ttk.Label(frame, font=BOLD)
        for label in (self._lbl_inflow, self._lbl_outflow, self._lbl_balance):
            label.pack(side=tk.LEFT, expand=True)
        self._show_summary(0, 0, 0)

    def _build_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._tree = ttk.Treeview(frame, columns=[name for name, _, _ in COLUMNS], show="headings")
        for name, width, anchor in COLUMNS:
            self._tree.heading(name, text=t(f"main.col_{name}"))
            self._tree.column(name, width=width, anchor=anchor)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_actions(self):
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=10, pady=5)
        for key, command in (("main.view", self._view_transaction), ("main.edit", self._edit_transaction),
                             ("main.delete", self._delete_transaction)):
            ttk.Button(bar, text=t(key), command=command).pack(side=tk.LEFT, padx=5)
        ttk.Button(bar, text=t("main.chart"), command=self._view_chart).pack(side=tk.RIGHT, padx=5)

    # ---------- dữ liệu ----------

    def refresh(self):
        with reported_errors(self):
            self._report = self._services.transactions.load_period(self._start, self._end)
            self._render()

    def _render(self):
        if self._report is None:
            return
        summary = self._report.summary
        self._show_summary(summary.inflow, summary.outflow, summary.balance)
        self._tree.delete(*self._tree.get_children())
        for transaction in self._report.transactions:
            categories = ", ".join(f"{category_label(item.category_key)} ({format_money(item.amount)})"
                                   for item in transaction.items)
            self._tree.insert("", tk.END, iid=transaction.id, values=(
                format_date(transaction.date), type_label(transaction.type), categories,
                format_money(transaction.total), transaction.general_note,
            ))

    def _show_summary(self, inflow, outflow, balance):
        self._lbl_inflow.config(text=t("summary.inflow", amount=format_money(inflow)))
        self._lbl_outflow.config(text=t("summary.outflow", amount=format_money(outflow)))
        self._lbl_balance.config(text=t("summary.balance", amount=format_money(balance)))

    def _selected_transaction(self) -> Transaction | None:
        selected = self._tree.selection()
        if not selected:
            messagebox.showwarning(t("dialog.warning"), t("main.select_first"), parent=self)
            return None
        return next(tr for tr in self._report.transactions if tr.id == selected[0])

    # ---------- hành động ----------

    def _change_language(self, code: str):
        with reported_errors(self):
            set_language(code)
        self._build()
        self._render()

    def _apply_filter(self):
        try:
            start, end = self._date_from.get_date(), self._date_to.get_date()
        except ValueError:
            messagebox.showerror(t("dialog.error"), t("error.invalid_date"), parent=self)
            return
        self._start = datetime.combine(start, time.min)
        self._end = datetime.combine(end, time(23, 59, 59))
        self.refresh()

    def _open_add_form(self):
        self.wait_window(TransactionForm(self, self._services.transactions, on_saved=self.refresh))

    def _edit_transaction(self):
        transaction = self._selected_transaction()
        if transaction:
            self.wait_window(TransactionForm(self, self._services.transactions, on_saved=self.refresh,
                                             transaction=transaction))

    def _view_transaction(self):
        transaction = self._selected_transaction()
        if transaction:
            receipt_file = self._services.transactions.resolve_receipt(transaction.receipt_path)
            TransactionDetail(self, transaction, receipt_file).grab_set()

    def _delete_transaction(self):
        transaction = self._selected_transaction()
        if not transaction or not messagebox.askyesno(t("dialog.confirm"), t("main.confirm_delete"), parent=self):
            return
        with reported_errors(self):
            self._services.transactions.delete(transaction.id)
            messagebox.showinfo(t("dialog.success"), t("main.deleted"), parent=self)
        self.refresh()

    def _view_chart(self):
        if self._report is not None:
            ChartView(self, self._report)

    def _export_report(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            initialdir=os.path.join(os.path.expanduser("~"), "Desktop"),
            initialfile=f"{t('report.file_prefix')}_{datetime.now():%Y%m%d_%H%M%S}.docx",
            defaultextension=".docx",
            filetypes=[(t("report.file_type"), "*.docx"), (t("dialog.all_files"), "*.*")],
            title=t("report.save_title"),
        )
        if not path:
            return  # người dùng huỷ
        with reported_errors(self):
            self._services.reports.export(self._start, self._end, path)
            messagebox.showinfo(t("dialog.success"), t("report.exported", path=path), parent=self)
```

`app/presentation/transaction_form.py`:
```python
"""Form thêm/sửa giao dịch gồm nhiều hạng mục."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.application.transaction_service import TransactionService
from app.domain.entities import Transaction, TransactionItem, TransactionType
from app.presentation.formatters import (
    category_label, combine_date_keep_time, format_money, parse_money, type_long_label,
)
from app.presentation.i18n import t
from app.presentation.ui_helpers import make_date_entry, reported_errors

CATEGORY_WIDTH = 15
AMOUNT_WIDTH = 15


class _ItemRow:
    """Một dòng hạng mục: danh mục, số tiền, ghi chú, nút xoá."""

    def __init__(self, parent, labels: list[str], on_change, on_remove):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, pady=2)
        self.category = ttk.Combobox(self.frame, width=CATEGORY_WIDTH)
        self.category.pack(side=tk.LEFT, padx=2)
        self.set_labels(labels)
        self.amount = tk.StringVar()
        self.amount.trace_add("write", lambda *_: on_change())
        ttk.Entry(self.frame, textvariable=self.amount, width=AMOUNT_WIDTH).pack(side=tk.LEFT, padx=2)
        self.note = ttk.Entry(self.frame, width=20)
        self.note.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(self.frame, text="X", width=2, command=lambda: on_remove(self)).pack(side=tk.LEFT, padx=2)

    def set_labels(self, labels: list[str]):
        self.category["values"] = labels
        if labels:
            self.category.set(labels[0])


class TransactionForm(tk.Toplevel):
    def __init__(self, parent, service: TransactionService, on_saved, transaction: Transaction | None = None):
        super().__init__(parent)
        self._service = service
        self._on_saved = on_saved
        self._original = transaction
        self._receipt_path = transaction.receipt_path if transaction else ""
        self._new_receipt_source: str | None = None
        self._type = tk.StringVar(value=(transaction.type if transaction else TransactionType.OUTFLOW).value)
        self._rows: list[_ItemRow] = []
        self._key_by_label: dict[str, str] = {}

        self.title(t("form.title_edit" if transaction else "form.title_add"))
        self.geometry("600x700")
        self._build()
        if transaction:
            self._fill(transaction)
        else:
            self._add_row()

    # ---------- dựng giao diện ----------

    def _build(self):
        type_frame = ttk.LabelFrame(self, text=t("form.type_frame"))
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        for transaction_type in (TransactionType.OUTFLOW, TransactionType.INFLOW):
            ttk.Radiobutton(type_frame, text=type_long_label(transaction_type), variable=self._type,
                            value=transaction_type.value, command=self._on_type_changed).pack(side=tk.LEFT, padx=10)

        general = ttk.LabelFrame(self, text=t("form.general_frame"))
        general.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(general, text=t("form.date")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self._date = make_date_entry(general)
        self._date.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(general, text=t("form.contact")).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self._contact = ttk.Entry(general, width=20)
        self._contact.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        ttk.Label(general, text=t("form.note")).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self._note = ttk.Entry(general, width=50)
        self._note.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)

        items = ttk.LabelFrame(self, text=t("form.items_frame"))
        items.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        header = ttk.Frame(items)
        header.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(header, text=t("form.col_category"), width=CATEGORY_WIDTH + 3).pack(side=tk.LEFT, padx=2)
        ttk.Label(header, text=t("form.col_amount"), width=AMOUNT_WIDTH).pack(side=tk.LEFT, padx=2)
        ttk.Label(header, text=t("form.col_note")).pack(side=tk.LEFT, padx=2)
        self._rows_frame = ttk.Frame(items)
        self._rows_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Button(items, text=t("form.add_item"), command=self._add_row).pack(anchor=tk.E, padx=5, pady=5)

        receipt = ttk.Frame(self)
        receipt.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(receipt, text=t("form.choose_receipt"), command=self._choose_receipt).pack(side=tk.LEFT)
        self._receipt_label = ttk.Label(receipt, text=t("form.no_receipt"))
        self._receipt_label.pack(side=tk.LEFT, padx=10)

        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, padx=10, pady=10)
        self._total_label = ttk.Label(bottom, font=("Arial", 12, "bold"))
        self._total_label.pack(side=tk.LEFT)
        ttk.Button(bottom, text=t("form.save_edit" if self._original else "form.save_new"),
                   command=self._save).pack(side=tk.RIGHT)
        self._update_total()

    def _fill(self, transaction: Transaction):
        self._date.set_date(transaction.date)
        self._contact.insert(0, transaction.contact_person)
        self._note.insert(0, transaction.general_note)
        if self._receipt_path:
            self._receipt_label.config(text=os.path.basename(self._receipt_path))
        for item in transaction.items:
            row = self._add_row()
            row.category.set(category_label(item.category_key))
            row.amount.set(format_money(item.amount))
            row.note.insert(0, item.note)

    # ---------- danh mục ----------

    def _category_labels(self) -> list[str]:
        keys: list[str] = []
        with reported_errors(self):
            keys = self._service.category_keys(TransactionType(self._type.get()))
        self._key_by_label = {category_label(key): key for key in keys}
        return list(self._key_by_label)

    def _category_key(self, label: str) -> str:
        """Label đang hiển thị -> key; chuỗi người dùng tự gõ thì dùng làm key luôn."""
        label = label.strip()
        return self._key_by_label.get(label, label)

    def _on_type_changed(self):
        labels = self._category_labels()
        for row in self._rows:
            row.set_labels(labels)

    # ---------- hạng mục ----------

    def _add_row(self) -> _ItemRow:
        row = _ItemRow(self._rows_frame, self._category_labels(), self._update_total, self._remove_row)
        self._rows.append(row)
        self._update_total()
        return row

    def _remove_row(self, row: _ItemRow):
        if len(self._rows) <= 1:
            return  # luôn giữ ít nhất một dòng
        row.frame.destroy()
        self._rows.remove(row)
        self._update_total()

    def _update_total(self):
        total = sum(parse_money(row.amount.get()) for row in self._rows)
        self._total_label.config(text=t("form.total", amount=format_money(total)))

    def _choose_receipt(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[(t("form.image_files"), "*.jpg *.jpeg *.png")])
        if path:
            self._new_receipt_source = path
            self._receipt_label.config(text=os.path.basename(path))

    # ---------- lưu ----------

    def _build_transaction(self) -> Transaction:
        items = tuple(
            TransactionItem(category_key=self._category_key(row.category.get()),
                            amount=parse_money(row.amount.get()),
                            note=row.note.get().strip())
            for row in self._rows
            if parse_money(row.amount.get()) > 0  # bỏ qua dòng trống
        )
        return Transaction(
            type=TransactionType(self._type.get()),
            date=combine_date_keep_time(self._date.get_date(), self._original.date if self._original else None),
            items=items,
            general_note=self._note.get().strip(),
            contact_person=self._contact.get().strip(),
            receipt_path=self._receipt_path,
            id=self._original.id if self._original else None,
        )

    def _save(self):
        with reported_errors(self):
            self._service.save(self._build_transaction(), self._new_receipt_source)
            messagebox.showinfo(t("dialog.success"), t("form.updated" if self._original else "form.added"),
                                parent=self)
            self._on_saved()
            self.destroy()
```

`app/presentation/transaction_detail.py`:
```python
"""Cửa sổ xem chi tiết một giao dịch."""
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from app.domain.entities import Transaction, TransactionType
from app.presentation.formatters import category_label, format_money, type_long_label
from app.presentation.i18n import t


class TransactionDetail(tk.Toplevel):
    def __init__(self, parent, transaction: Transaction, receipt_file: str | None):
        super().__init__(parent)
        self.title(t("detail.title"))
        self.geometry("500x600")
        self._build_info(transaction)
        self._build_items(transaction)
        if receipt_file:
            self._build_receipt(receipt_file)
        ttk.Button(self, text=t("dialog.close"), command=self.destroy).pack(pady=10)

    def _build_info(self, transaction: Transaction):
        frame = ttk.LabelFrame(self, text=t("detail.general"))
        frame.pack(fill=tk.X, padx=10, pady=10)
        total_color = "blue" if transaction.type == TransactionType.INFLOW else "red"
        rows = (
            (t("detail.type", value=type_long_label(transaction.type)), {"font": ("Arial", 10, "bold")}),
            (t("detail.date", value=transaction.date.strftime("%d/%m/%Y %H:%M:%S")), {}),
            (t("detail.total", value=format_money(transaction.total)),
             {"foreground": total_color, "font": ("Arial", 11, "bold")}),
            (t("detail.contact", value=transaction.contact_person), {}),
            (t("detail.note", value=transaction.general_note), {}),
        )
        for row, (text, style) in enumerate(rows):
            ttk.Label(frame, text=text, **style).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)

    def _build_items(self, transaction: Transaction):
        frame = ttk.LabelFrame(self, text=t("detail.items"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree = ttk.Treeview(frame, columns=("category", "amount", "note"), show="headings", height=5)
        for name, key, width, anchor in (("category", "form.col_category", 120, tk.W),
                                         ("amount", "form.col_amount", 100, tk.E),
                                         ("note", "form.col_note", 200, tk.W)):
            tree.heading(name, text=t(key))
            tree.column(name, width=width, anchor=anchor)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for item in transaction.items:
            tree.insert("", tk.END, values=(category_label(item.category_key), format_money(item.amount), item.note))

    def _build_receipt(self, receipt_file: str):
        frame = ttk.LabelFrame(self, text=t("detail.receipt"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        try:
            image = Image.open(receipt_file)
            image.thumbnail((400, 200))
            photo = ImageTk.PhotoImage(image)
        except OSError:
            ttk.Label(frame, text=t("detail.receipt_error")).pack(padx=5, pady=5)
            return
        label = ttk.Label(frame, image=photo)
        label.image = photo  # giữ tham chiếu để Tk không thu hồi ảnh
        label.pack(padx=5, pady=5)
```

`app/presentation/chart_view.py`:
```python
"""Cửa sổ biểu đồ thu/chi theo danh mục cho kỳ đang xem."""
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.domain.summary import PeriodReport
from app.presentation.charts import plot_category_bars
from app.presentation.formatters import format_date
from app.presentation.i18n import t


class ChartView(tk.Toplevel):
    def __init__(self, parent, report: PeriodReport):
        super().__init__(parent)
        self.title(t("chart.window_title"))
        self.geometry("1000x800")
        try:
            self.state("zoomed")
        except tk.TclError:
            pass  # 'zoomed' chỉ có trên Windows
        self.transient(parent)
        self.grab_set()

        heading = t("chart.heading", start=format_date(report.start), end=format_date(report.end))
        ttk.Label(self, text=heading, font=("Arial", 14, "bold")).pack(pady=10)
        if report.inflow_by_category or report.outflow_by_category:
            self._draw(report)
        else:
            ttk.Label(self, text=t("chart.no_data_period"), font=("Arial", 12)).pack(pady=20)
        ttk.Button(self, text=t("dialog.close"), command=self.destroy).pack(pady=10)

    def _draw(self, report: PeriodReport):
        figure = Figure(figsize=(10, 8))
        inflow_axes, outflow_axes = figure.subplots(2, 1)
        plot_category_bars(inflow_axes, report.inflow_by_category, t("chart.inflow_title"), "green")
        plot_category_bars(outflow_axes, report.outflow_by_category, t("chart.outflow_title"), "red")
        figure.tight_layout(pad=5.0, h_pad=6.0)
        canvas = FigureCanvasTkAgg(figure, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
```

- [ ] **Step 3: Container, entry point, build, requirements**

`app/container.py`:
```python
"""Composition root: nơi duy nhất biết implementation cụ thể (Firestore, ổ đĩa, Word)."""
from dataclasses import dataclass

from app.application.report_service import ReportService
from app.application.transaction_service import TransactionService
from app.config import BASE_DIR, FIREBASE_CREDENTIALS_PATH
from app.infrastructure.firestore_repository import (
    FirestoreCategoryRepository, FirestoreTransactionRepository, connect,
)
from app.infrastructure.receipt_storage import LocalReceiptStorage
from app.presentation.word_exporter import WordReportExporter


@dataclass(frozen=True)
class Services:
    transactions: TransactionService
    reports: ReportService


def build_services() -> Services:
    """Kết nối Firebase và nối dependency. Chạy ở thread nền của màn hình khởi động."""
    client = connect(FIREBASE_CREDENTIALS_PATH)
    categories = FirestoreCategoryRepository(client)
    categories.seed_defaults_if_empty()
    transactions = TransactionService(FirestoreTransactionRepository(client), categories,
                                      LocalReceiptStorage(BASE_DIR))
    return Services(transactions=transactions, reports=ReportService(transactions, WordReportExporter()))
```

`main.py` (thay toàn bộ):
```python
from app.container import build_services
from app.presentation.loading_window import LoadingWindow
from app.presentation.main_window import MainWindow


def main():
    loading = LoadingWindow(connect=build_services)
    loading.mainloop()
    if loading.result is not None:
        MainWindow(loading.result).mainloop()


if __name__ == "__main__":
    main()
```

`build_exe.py`: thay khối `command` và bỏ khối `.env.example`:
```python
    command = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--windows-disable-console",
        "--output-dir=build_output",
        "--include-data-dir=locales=locales",
        "main.py",
    ]
```
Xoá 2 dòng `if os.path.exists(".env.example"): ...` và dòng `import os` (không còn dùng).

`requirements.txt` (thay toàn bộ):
```
tkcalendar
python-docx
pillow
matplotlib
nuitka
certifi
firebase-admin
```

Xoá code cũ:
```bash
git rm -r -q config.py database services utils views .env.example
rm -rf __pycache__ database services utils views
```

- [ ] **Step 4: Verify tự động**

Run:
```bash
.venv/Scripts/python.exe -m unittest discover -s tests -t . -v
.venv/Scripts/python.exe -c "import main, app.presentation.main_window, app.container; print('imports ok')"
grep -rn "import firebase\|from firebase\|google.cloud" app/presentation app/domain app/application || echo "dependency rule ok"
grep -rln "^from app.infrastructure\|^import app.infrastructure" app/presentation app/domain app/application || echo "no inward infra imports"
```
Expected:
- 47 tests OK
- `imports ok`
- `dependency rule ok`
- `no inward infra imports`

- [ ] **Step 5: Smoke test thủ công (người dùng chạy, vì cần Firebase thật và GUI)**

Run: `.venv/Scripts/python.exe main.py`

Checklist:
1. Màn hình kết nối hiện ra, sau đó cửa sổ chính hiện tổng thu/chi và danh sách của tháng hiện tại.
2. Thêm một giao dịch chi gồm 2 hạng mục và có ảnh biên lai, rồi xem chi tiết: ảnh hiển thị đúng.
3. Sửa giao dịch đó: giờ trong phần chi tiết giữ nguyên như trước khi sửa.
4. Menu Ngôn ngữ → English: toàn bộ cửa sổ chính chuyển sang tiếng Anh, tên danh mục hiển thị "Food & drinks"... Mở form: combobox hiển thị label tiếng Anh. Lưu xong, chuyển lại tiếng Việt: danh mục vẫn đúng.
5. Xem biểu đồ; xuất Word ở cả vi và en, mở file ra kiểm tra.
6. Xoá giao dịch thử.
7. Tắt app rồi mở lại: ngôn ngữ đã chọn vẫn được giữ.

---

### Task 7: Script migration + cập nhật spec

**Files:**
- Create: `scripts/__init__.py` (rỗng), `scripts/migrate_category_keys.py`
- Modify: `docs/specs/2026-11-03-clean-arch-i18n-design.md` (áp dụng mục "Spec deltas")
- Test: `tests/test_migration_plan.py`

**Interfaces:**
- Consumes: `legacy_name_to_key`, `is_legacy_name`, `app.config`, `connect()`
- Produces:
  - `plan_migration(category_docs: dict[str, dict], transaction_docs: dict[str, dict]) -> MigrationPlan`
  - `MigrationPlan.category_updates`, `MigrationPlan.transaction_updates`, `MigrationPlan.unknown_names`, `MigrationPlan.is_empty`
  - `write_backup(category_docs, transaction_docs, backups_dir) -> str`
  - `MISSING_NAME`

- [ ] **Step 1: Viết test**

`tests/test_migration_plan.py`:
```python
import json
import unittest
from datetime import datetime, timezone
from tempfile import TemporaryDirectory

from scripts.migrate_category_keys import MISSING_NAME, plan_migration, write_backup


class PlanMigrationTest(unittest.TestCase):
    def test_adds_key_only_to_categories_without_one(self):
        plan = plan_migration({
            "c1": {"name": "Ăn uống", "type": "outflow"},
            "c2": {"key": "food", "name": "Ăn uống", "type": "outflow"},
        }, {})
        self.assertEqual(plan.category_updates, {"c1": {"key": "food"}})

    def test_other_maps_the_same_for_inflow_and_outflow(self):
        plan = plan_migration({"c1": {"name": "Khác", "type": "inflow"},
                               "c2": {"name": "Khác", "type": "outflow"}}, {})
        self.assertEqual(plan.category_updates, {"c1": {"key": "other"}, "c2": {"key": "other"}})

    def test_adds_category_key_and_keeps_old_item_fields(self):
        plan = plan_migration({}, {"t1": {"items": [{"category_name": "Lương", "amount": 10.0, "item_note": "x"}]}})
        self.assertEqual(plan.transaction_updates, {"t1": {"items": [
            {"category_name": "Lương", "amount": 10.0, "item_note": "x", "category_key": "salary"},
        ]}})

    def test_reports_unknown_and_missing_names(self):
        plan = plan_migration({}, {"t1": {"items": [{"category_name": "Cà phê", "amount": 1.0}, {"amount": 2.0}]}})
        keys = [item["category_key"] for item in plan.transaction_updates["t1"]["items"]]
        self.assertEqual(keys, ["Cà phê", "other"])
        self.assertEqual(plan.unknown_names, {"Cà phê", MISSING_NAME})

    def test_partially_migrated_transaction_only_fills_missing_keys(self):
        plan = plan_migration({}, {"t1": {"items": [
            {"category_name": "Ăn uống", "category_key": "food", "amount": 1.0},
            {"category_name": "Thưởng", "amount": 2.0},
        ]}})
        keys = [item["category_key"] for item in plan.transaction_updates["t1"]["items"]]
        self.assertEqual(keys, ["food", "bonus"])

    def test_is_idempotent(self):
        categories = {"c1": {"name": "Lương", "type": "inflow"}}
        transactions = {"t1": {"items": [{"category_name": "Lương", "amount": 10.0}]}, "t2": {"items": []}}
        first = plan_migration(categories, transactions)
        self.assertFalse(first.is_empty)
        migrated_categories = {i: {**d, **first.category_updates.get(i, {})} for i, d in categories.items()}
        migrated_transactions = {i: {**d, **first.transaction_updates.get(i, {})} for i, d in transactions.items()}
        self.assertTrue(plan_migration(migrated_categories, migrated_transactions).is_empty)


class WriteBackupTest(unittest.TestCase):
    def test_backup_contains_both_collections_with_iso_dates(self):
        with TemporaryDirectory() as folder:
            path = write_backup({"c1": {"name": "Lương"}},
                                {"t1": {"date": datetime(2026, 1, 2, tzinfo=timezone.utc)}}, folder)
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
        self.assertEqual(data["categories"], {"c1": {"name": "Lương"}})
        self.assertTrue(data["transactions"]["t1"]["date"].startswith("2026-01-02"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test, xác nhận FAIL**

Run: `.venv/Scripts/python.exe -m unittest tests.test_migration_plan -v`
Expected: `ModuleNotFoundError: No module named 'scripts.migrate_category_keys'`

- [ ] **Step 3: Implement `scripts/migrate_category_keys.py`**

```python
"""Thêm key danh mục cho dữ liệu cũ trên Firestore.

    python -m scripts.migrate_category_keys            # dry-run: chỉ đọc và báo cáo
    python -m scripts.migrate_category_keys --apply    # backup ra backups/ rồi ghi

Chỉ THÊM field (`key` cho categories, `category_key` cho từng item), không xoá field cũ,
nên phiên bản app cũ vẫn chạy được. Chạy lại nhiều lần an toàn. Hãy đóng app trước khi chạy.
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime

from app.config import BACKUPS_DIR, FIREBASE_CREDENTIALS_PATH
from app.domain.categories import is_legacy_name, legacy_name_to_key

MISSING_NAME = "<missing>"
BATCH_LIMIT = 400  # Firestore cho tối đa 500 thao tác mỗi batch


@dataclass
class MigrationPlan:
    category_updates: dict[str, dict] = field(default_factory=dict)
    transaction_updates: dict[str, dict] = field(default_factory=dict)
    unknown_names: set[str] = field(default_factory=set)

    @property
    def is_empty(self) -> bool:
        return not self.category_updates and not self.transaction_updates


def plan_migration(category_docs: dict[str, dict], transaction_docs: dict[str, dict]) -> MigrationPlan:
    """Hàm thuần: tính các field cần thêm, không đụng tới Firestore."""
    plan = MigrationPlan()

    def key_for(name: str | None) -> str:
        if not name:
            plan.unknown_names.add(MISSING_NAME)
        elif not is_legacy_name(name):
            plan.unknown_names.add(name)
        return legacy_name_to_key(name)

    for doc_id, data in category_docs.items():
        if not data.get("key"):
            plan.category_updates[doc_id] = {"key": key_for(data.get("name"))}

    for doc_id, data in transaction_docs.items():
        items = data.get("items", [])
        if all(item.get("category_key") for item in items):
            continue
        plan.transaction_updates[doc_id] = {"items": [
            item if item.get("category_key") else {**item, "category_key": key_for(item.get("category_name"))}
            for item in items
        ]}
    return plan


def write_backup(category_docs: dict, transaction_docs: dict, backups_dir: str) -> str:
    os.makedirs(backups_dir, exist_ok=True)
    path = os.path.join(backups_dir, f"firestore_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump({"categories": category_docs, "transactions": transaction_docs}, file,
                  ensure_ascii=False, indent=2, default=_json_default)
    return path


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Không backup được kiểu {type(value).__name__}")


def _read_collection(client, name: str) -> tuple[dict[str, dict], dict[str, object]]:
    """Trả về (dữ liệu theo id, update_time theo id)."""
    docs, update_times = {}, {}
    for snapshot in client.collection(name).stream():
        docs[snapshot.id] = snapshot.to_dict()
        update_times[snapshot.id] = snapshot.update_time
    return docs, update_times


def _apply(client, collection: str, updates: dict[str, dict], update_times: dict[str, object]) -> int:
    """Ghi theo batch; mỗi doc kèm điều kiện 'chưa bị sửa từ lúc đọc' để không ghi đè thay đổi mới."""
    doc_ids = list(updates)
    for start in range(0, len(doc_ids), BATCH_LIMIT):
        batch = client.batch()
        for doc_id in doc_ids[start:start + BATCH_LIMIT]:
            option = client.write_option(last_update_time=update_times[doc_id])
            batch.update(client.collection(collection).document(doc_id), updates[doc_id], option=option)
        batch.commit()
    return len(doc_ids)


def _print_report(plan: MigrationPlan, category_count: int, transaction_count: int) -> None:
    print(f"categories:   {len(plan.category_updates)}/{category_count} doc cần thêm 'key'")
    print(f"transactions: {len(plan.transaction_updates)}/{transaction_count} doc cần thêm 'category_key'")
    if plan.unknown_names:
        print("Tên danh mục không có trong bảng ánh xạ (sẽ dùng nguyên tên làm key):")
        for name in sorted(plan.unknown_names):
            print(f"  - {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="backup rồi ghi lên Firestore (mặc định: dry-run)")
    args = parser.parse_args(argv)

    from app.infrastructure.firestore_repository import connect  # import chậm: test không cần Firebase
    client = connect(FIREBASE_CREDENTIALS_PATH)
    category_docs, category_times = _read_collection(client, "categories")
    transaction_docs, transaction_times = _read_collection(client, "transactions")
    plan = plan_migration(category_docs, transaction_docs)
    _print_report(plan, len(category_docs), len(transaction_docs))

    if not args.apply:
        print("\nDry-run: chưa ghi gì. Chạy lại với --apply để ghi.")
        return 0
    if plan.is_empty:
        print("\nKhông có gì cần migrate.")
        return 0

    try:
        backup_path = write_backup(category_docs, transaction_docs, BACKUPS_DIR)
    except (OSError, TypeError) as error:
        print(f"\nBackup thất bại, dừng lại, chưa ghi gì: {error}", file=sys.stderr)
        return 1
    print(f"\nĐã backup: {backup_path}")

    written = _apply(client, "categories", plan.category_updates, category_times)
    written += _apply(client, "transactions", plan.transaction_updates, transaction_times)
    print(f"Đã ghi {written} doc. Chạy lại (không --apply) để kiểm tra: kết quả phải là 0 doc cần sửa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Chạy test, xác nhận PASS**

Run: `.venv/Scripts/python.exe -m unittest discover -s tests -t . -v`
Expected: 54 tests OK

- [ ] **Step 5: Cập nhật spec theo "Spec deltas"**

Sửa trong `docs/specs/2026-11-03-clean-arch-i18n-design.md`:
- Mục 3: chuyển `PeriodReport` sang `domain/summary.py`; đổi `run_safely()` thành `reported_errors()`.
- Mục 4: thêm luật "`category_key` rỗng → `InvalidTransaction`".
- Mục 5: `ReportExporter` import `PeriodReport` từ domain.
- Mục 9: thêm `last_update_time` precondition vào phần đảm bảo an toàn, và thêm dòng vào bảng failure modes: "Doc bị sửa giữa lúc đọc và lúc ghi → batch đó fail, không ghi đè → chạy lại".
- Mục 10: đổi `run_safely(parent, action, error_key)` thành `with reported_errors(parent):`.
- Mục 9, đoạn "**Rollback:**" và câu "Code cũ (baseline) vẫn chạy trên dữ liệu đã migrate..." trong "Đảm bảo an toàn": thay bằng ý sau. "Migration chỉ thêm field nên **dữ liệu đã migrate** vẫn đọc được bằng bản cũ. Nhưng giao dịch mà bản mới tạo hoặc sửa chỉ có `category_key`, và bản cũ (đọc `item['category_name']` trực tiếp) sẽ crash trên những doc này. Vì vậy: **sau khi bản mới đã ghi dữ liệu thì KHÔNG quay về bản cũ**; nếu buộc phải quay về thì restore từ file backup, chấp nhận mất các thay đổi sau thời điểm backup." (Spec delta 7.)

- [ ] **Step 6: Dry-run trên Firestore thật (CHỈ ĐỌC)**

Run: `.venv/Scripts/python.exe -m scripts.migrate_category_keys`
Expected: in số doc cần sửa và danh sách tên lạ, kết thúc bằng "Dry-run: chưa ghi gì". Lưu output này để đưa vào review ở Task 8.

---

### Task 8: Review độc lập bắt buộc → xác nhận → `--apply`

- [ ] **Step 1:** Gọi skill `requesting-code-review` cho diff `a2c701f..HEAD` (cả phần working tree), kèm spec, plan và output dry-run. Review tập trung vào:
  - Tương thích schema (đọc/ghi).
  - Tính an toàn của migration (chỉ thêm field, idempotent, điều kiện `last_update_time`, backup chạy trước khi ghi).
  - Quy tắc phụ thuộc giữa các tầng.
  - Bảng thay đổi hành vi ở mục 7 của spec.
- [ ] **Step 2:** Sửa các finding hợp lệ, chạy lại toàn bộ test.
- [ ] **Step 3:** Gọi `verification-before-completion`: chạy lại test, import check, và để người dùng xác nhận đã làm xong smoke test.
- [ ] **Step 4: Cổng xác nhận.** Cho người dùng xem output dry-run cùng lệnh sẽ chạy, và **chờ người dùng đồng ý rõ ràng**.
- [ ] **Step 5:** Chạy `.venv/Scripts/python.exe -m scripts.migrate_category_keys --apply`, sau đó chạy lại dry-run. Expected: `0/N doc cần thêm` cho cả hai collection.
- [ ] **Step 6:** Hỏi người dùng có muốn commit không. Chỉ commit khi họ đồng ý.

## Thứ tự & phụ thuộc

Các task phải làm tuần tự: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Mỗi task import code của task trước, nên không có task nào chạy song song được. Toàn bộ làm inline.
