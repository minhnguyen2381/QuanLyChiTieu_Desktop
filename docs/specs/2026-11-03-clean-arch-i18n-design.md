# Refactor Clean Architecture + i18n + migrate danh mục sang key

- Ngày: 2026-11-03
- Tier: **T4** (migration sửa dữ liệu đã lưu trên Firestore)
- Baseline: commit `a2c701f` trên `main`; làm việc trên nhánh `refactor/clean-arch`

## 1. Mục tiêu

1. Tái cấu trúc app Tkinter quản lý chi tiêu (~1000 dòng) theo Clean Architecture 4 tầng, code dễ đọc, logic test được không cần Firebase.
2. i18n: tiếng Việt (mặc định) + English, đổi được trong app.
3. Danh mục lưu bằng key trung lập ngôn ngữ (`food`, `salary`...) thay cho chuỗi tiếng Việt, qua script migration có backup + dry-run.
4. Sửa các lỗi đã phát hiện (mục 7).

Ngoài phạm vi: xoá field cũ `name`/`category_name` khỏi Firestore; UI quản lý danh mục; chạy Firestore trên background thread (trừ màn hình khởi động như hiện nay); đổi định dạng ngày theo locale.

## 2. Quy tắc phụ thuộc

`presentation` → `application` → `domain`; `infrastructure` → `application` → `domain`.

- `domain` chỉ dùng stdlib.
- `application` chỉ import `domain`; giao tiếp ra ngoài qua Protocol trong `application/ports.py`.
- `presentation` không import `infrastructure`, không import `firebase_admin`.
- Chỉ `app/container.py` khởi tạo implementation cụ thể và nối dependency.

## 3. Cấu trúc thư mục

```
app/
  config.py                   # BASE_DIR, RECEIPTS_DIR, LOCALES_DIR, SETTINGS_PATH, FIREBASE_CREDENTIALS_PATH
  domain/
    entities.py               # TransactionType, TransactionItem, Transaction, InvalidTransaction
    categories.py             # DEFAULT_CATEGORIES, LEGACY_NAME_TO_KEY
    summary.py                # PeriodSummary, CategoryTotal, PeriodReport, summarize(), totals_by_category()
  application/
    ports.py                  # TransactionRepository, CategoryRepository, ReceiptStorage, ReportExporter
    transaction_service.py    # TransactionService
    report_service.py         # ReportService, NoDataError
  infrastructure/
    firestore_mapping.py      # hàm thuần dict <-> entity
    firestore_repository.py   # FirestoreTransactionRepository, FirestoreCategoryRepository
    receipt_storage.py        # LocalReceiptStorage
  presentation/
    charts.py                 # plot_category_bars() — dùng chung cho chart_view + word_exporter
    word_exporter.py          # WordReportExporter (implement ReportExporter; xuất Word = một dạng "view")
    i18n.py                   # Translator, t()
    formatters.py             # format_money(), parse_money(), category_label()
    ui_helpers.py             # reported_errors()
    loading_window.py
    main_window.py
    transaction_form.py
    transaction_detail.py
    chart_view.py
  container.py                # build_services() -> Services
locales/
  vi.json
  en.json
scripts/
  migrate_category_keys.py
tests/
  test_*.py                   # unittest
main.py                       # entry point mỏng
```

Xoá sau khi chuyển xong: `config.py` (gốc), `database/`, `services/`, `utils/`, `views/`, `.env.example`; bỏ `python-dotenv` khỏi `requirements.txt`.

## 4. Domain

```python
class TransactionType(str, Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"

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
    receipt_path: str = ""      # tương đối với BASE_DIR, ví dụ "assets/receipts/x.png"
    id: str | None = None

    @property
    def total(self) -> float: ...   # tổng amount của items
```

- `Transaction.__post_init__` raise `InvalidTransaction` nếu không có item nào, có item `category_key` rỗng, hoặc có item `amount < 0` (số tiền âm); hạng mục 0 đ được chấp nhận khi đọc dữ liệu cũ, còn form vẫn bỏ qua dòng 0 đ khi lưu. Form lọc bỏ dòng trống trước khi tạo entity.
- `summary.py`:
  - `summarize(transactions) -> PeriodSummary(inflow, outflow, balance)`
  - `totals_by_category(transactions, type) -> list[CategoryTotal(category_key, total)]`, sắp giảm dần theo `total`.
- `categories.py`:
  - `DEFAULT_CATEGORIES: dict[TransactionType, tuple[str, ...]]`
    - inflow: `salary, bonus, passive_income, sales, other`
    - outflow: `food, bills, transport, shopping, health, entertainment, other`
  - `LEGACY_NAME_TO_KEY`: `Lương→salary, Thưởng→bonus, Thu nhập thụ động→passive_income, Bán hàng→sales, Ăn uống→food, Hóa đơn→bills, Di chuyển→transport, Mua sắm→shopping, Sức khỏe→health, Giải trí→entertainment, Khác→other`
  - `legacy_name_to_key(name) -> str`: trả key nếu có trong bảng, ngược lại trả nguyên `name` (danh mục người dùng tự gõ).

## 5. Application

```python
class TransactionRepository(Protocol):
    def list_between(self, start: datetime, end: datetime) -> list[Transaction]: ...  # sắp theo date giảm dần
    def get(self, transaction_id: str) -> Transaction | None: ...
    def add(self, transaction: Transaction) -> str: ...
    def update(self, transaction: Transaction) -> None: ...
    def delete(self, transaction_id: str) -> None: ...

class CategoryRepository(Protocol):
    def list_keys(self, type: TransactionType) -> list[str]: ...

class ReceiptStorage(Protocol):
    def save(self, source_path: str) -> str: ...      # trả đường dẫn tương đối; lỗi thì raise OSError
    def resolve(self, stored_path: str) -> str | None: ...  # đường dẫn tuyệt đối nếu file tồn tại

class ReportExporter(Protocol):
    def export(self, report: PeriodReport, path: str) -> None: ...  # PeriodReport import từ domain/summary.py
```

`TransactionService(transactions, categories, receipts)`:
- `load_period(start, end) -> PeriodReport(start, end, transactions, summary, inflow_by_category, outflow_by_category)`: **gọi `list_between` đúng 1 lần**.
- `get(id)`, `delete(id)`.
- `save(transaction, new_receipt_source: str | None = None) -> str`:
  - Nếu có `new_receipt_source` thì gọi `receipts.save()` trước. `OSError` được ném ra ngoài và không ghi gì vào repository.
  - `transaction.id is None` thì gọi `add`, ngược lại gọi `update`.
- `category_keys(type)`: cache theo type trong suốt vòng đời service.
- `resolve_receipt(path)`: uỷ quyền cho `receipts.resolve`.

`ReportService(transaction_service, exporter)`:
- `export(start, end, path)`: `load_period`. Không có giao dịch thì raise `NoDataError`. Lỗi ghi file (`OSError`) ném ra cho UI xử lý.

## 6. Infrastructure

### 6.1 Schema Firestore

**Hiện tại (giữ nguyên tên collection):**

- `categories/{auto}`: `{name, type}`
- `transactions/{auto}`: `{type, total_amount, items:[{category_name, amount, item_note}], date, general_note, image_path, contact_person, created_at, updated_at?}`

**Sau refactor:**

- Đọc:
  - item dùng `category_key`; nếu thiếu thì lấy `legacy_name_to_key(category_name)`.
  - category dùng `key`; nếu thiếu thì lấy `legacy_name_to_key(name)`.
- Ghi transaction: `{type, total_amount, items:[{category_key, amount, item_note}], date, general_note, image_path, contact_person}` cộng `created_at` (khi add) hoặc `updated_at` (khi update). `total_amount` vẫn ghi để giữ tương thích.
- Seed danh mục khi collection rỗng: `{key, type}`.
- `firestore_mapping.py` gồm các hàm thuần `transaction_to_document`, `transaction_from_document(id, data)`, `category_key_from_document(data)`, test được không cần Firebase.

### 6.2 LocalReceiptStorage(base_dir)

- `save(source)`: copy vào `assets/receipts/<YYYYmmdd_HHMMSS>_<tên file>`, trả `"assets/receipts/<file>"` (dùng dấu `/`).
- `resolve(stored)`: nếu rỗng thì trả `None`. Đường dẫn tuyệt đối thì dùng nguyên; đường dẫn tương đối thì join với `base_dir`. File không tồn tại thì trả `None`.

### 6.3 Rendering (nằm ở `presentation/`, vì cần `t()` và `category_label`)

- `presentation/charts.py`: `plot_category_bars(ax, totals, title, color)`. Đây là implementation duy nhất, thay cho 2 bản `_plot_bar` đang bị trùng; label và chữ "không có dữ liệu" lấy qua i18n.
- `presentation/word_exporter.py`: `WordReportExporter` implement port `ReportExporter`. Hàm dựng file `.docx` giống báo cáo hiện tại, mọi chuỗi đi qua `t()`. Biểu đồ vẽ vào `io.BytesIO`, không ghi file tạm.

## 7. Thay đổi hành vi so với baseline

| # | Trước | Sau |
|---|-------|-----|
| 1 | Ảnh biên lai tìm theo thư mục hiện hành (cwd), chạy từ chỗ khác hoặc từ `.exe` thì không thấy | Resolve theo `BASE_DIR`; dữ liệu cũ vẫn đọc được |
| 2 | Mỗi lần refresh query 2 lần, xuất báo cáo query 4 lần, mỗi dòng hạng mục mới query danh mục 1 lần | 1 query mỗi kỳ; danh mục được cache |
| 3 | Thông báo lỗi và `.env.example` nhắc tới MongoDB | Thông báo nói Firebase; bỏ `.env.example` |
| 4 | Sửa giao dịch thì giờ bị ghi đè bằng giờ hiện tại | Sửa thì giữ giờ gốc (ngày lấy theo DateEntry); thêm mới dùng giờ hiện tại |
| 5 | Ô ghi chú hạng mục chứa sẵn chữ "Ghi chú..." làm placeholder giả | Ô trống, phía trên có hàng tiêu đề cột |
| 6 | Copy ảnh lỗi thì vẫn lưu, không có ảnh, không báo gì | Báo lỗi, không lưu, form giữ nguyên để thử lại |
| 7 | Lỗi Firestore khi thao tác chỉ in traceback ra console | Hiện messagebox |
| 8 | Xuất báo cáo để lại file PNG tạm khi gặp lỗi | Không còn file tạm |
| 9 | Giao dịch mới lưu `category_name` (tiếng Việt) | Lưu `category_key` |

## 8. i18n

- `locales/vi.json`, `locales/en.json`: object phẳng, key dạng chấm (`main.title`, `form.save`, `category.food`, `error.no_data`...). Giá trị dùng `str.format` với tham số có tên.
- `Translator(locales_dir, language)`: `t(key, **params)`. Thứ tự tra: ngôn ngữ hiện tại → `vi` → trả chính key.
- `presentation/i18n.py` giữ một translator dùng chung; `set_language(lang)` lưu `{"language": lang}` vào `settings.json`. Không đọc được `settings.json` thì dùng `vi`.
- Menu "Ngôn ngữ / Language" trên `MainWindow`: đổi ngôn ngữ thì lưu settings và dựng lại toàn bộ widget của cửa sổ chính. Cửa sổ con đang mở giữ ngôn ngữ cũ cho tới khi đóng.
- `category_label(key)`: có `category.<key>` trong bản dịch thì dùng bản dịch, không có thì hiển thị nguyên `key` (danh mục tự gõ).
- Form danh mục: combobox hiển thị label. Khi lưu, đổi label về key bằng phép tra ngược trong danh sách hiện có; chuỗi không khớp label nào thì dùng làm key luôn (danh mục tự gõ).
- Tiền tệ:
  - `vi`: `1.000.000 đ`
  - `en`: `1,000,000 VND`
  - `parse_money` bỏ mọi ký tự không phải chữ số. VND không có phần lẻ nên `1.000`, `1,000` và `1000` đều ra `1000`.
- Ngày: `dd/mm/yyyy` cho cả hai ngôn ngữ.
- Báo cáo Word và biểu đồ dùng ngôn ngữ hiện tại.

## 9. Migration `scripts/migrate_category_keys.py`

```
python -m scripts.migrate_category_keys            # dry-run (mặc định), chỉ đọc
python -m scripts.migrate_category_keys --apply    # backup rồi ghi
```

1. Đọc toàn bộ `categories` và `transactions`.
2. `plan_migration(category_docs, transaction_docs) -> MigrationPlan`, là hàm thuần:
   - `category_updates: {doc_id: {"key": ...}}` cho các doc chưa có `key`.
   - `transaction_updates: {doc_id: {"items": [...]}}` cho các doc có ít nhất 1 item thiếu `category_key`. Mỗi item giữ mọi field cũ và được thêm `category_key`.
   - `unknown_names: set[str]` gồm các tên không có trong `LEGACY_NAME_TO_KEY`; key của chúng chính là tên đó.
3. In báo cáo: số doc sẽ sửa của mỗi collection và danh sách `unknown_names`.
4. Chỉ khi có `--apply`:
   - Ghi backup toàn bộ 2 collection ra `backups/firestore_<YYYYmmdd_HHMMSS>.json` (datetime chuyển sang ISO). Ghi backup lỗi thì thoát với mã khác 0 và không ghi gì lên Firestore.
   - Ghi bằng `WriteBatch`, mỗi batch tối đa 400 thao tác, dùng `update()` để chỉ đụng các field liệt kê.
   - In số doc đã ghi.

**Đảm bảo an toàn:**
- Chỉ **thêm** field, không xoá hay đổi field nào đã có.
- Idempotent: chạy lần 2 thì kế hoạch rỗng.
- Mỗi doc ghi kèm điều kiện `last_update_time` (thời điểm đọc): doc bị sửa sau lúc đọc thì không bị ghi đè.
- Migration chỉ thêm field nên **dữ liệu đã migrate** vẫn đọc được bằng bản cũ (baseline) vì `name`/`category_name` còn nguyên.

**Failure modes:**

| Tình huống | Hệ quả | Xử lý |
|---|---|---|
| Mất mạng giữa các batch | Một phần doc đã có key, phần còn lại chưa | App vẫn đúng nhờ fallback khi đọc; chạy lại `--apply` để bù phần thiếu |
| App đang mở và thêm giao dịch trong lúc migrate | Giao dịch mới đã có `category_key` từ đầu, hoặc là doc cũ chưa được quét | Vô hại; chạy lại là đủ. Hướng dẫn ghi rõ: đóng app trước khi chạy |
| `Khác` xuất hiện ở cả thu và chi | Cả hai đều thành `other` | Phân biệt bằng `type` |
| Tên tự gõ có khoảng trắng hoặc dấu | Key = nguyên chuỗi | Hiển thị nguyên văn |
| Item thiếu cả `category_name` | Không suy ra được key | Map thành `other`, liệt kê trong báo cáo dưới dạng `<missing>` |
| Doc bị sửa giữa lúc đọc và lúc ghi | Batch đó fail, không ghi đè | Chạy lại |

**Rollback:** migration chỉ thêm field nên **dữ liệu đã migrate** vẫn đọc được bằng bản cũ. Nhưng giao dịch mà bản mới tạo hoặc sửa chỉ có `category_key`, và bản cũ (đọc `item['category_name']` trực tiếp) sẽ crash trên những doc này. Vì vậy: **sau khi bản mới đã ghi dữ liệu thì KHÔNG quay về bản cũ**; nếu buộc phải quay về thì restore thủ công từ file backup JSON, chấp nhận mất các thay đổi sau thời điểm backup. Không viết script restore.

**Cổng an toàn:**
1. Dry-run trên dữ liệu thật.
2. Review độc lập (code + kết quả dry-run).
3. Người dùng xác nhận riêng.
4. Mới chạy `--apply`.

## 10. Xử lý lỗi ở presentation

- `with reported_errors(parent):` (context manager):
  - Bắt `InvalidTransaction` và `NoDataError`, hiện thông báo đã dịch tương ứng.
  - Bắt `OSError` và mọi `Exception` khác, hiện `error.generic` kèm chi tiết.
  - Khi có lỗi, các dòng còn lại trong khối `with` không chạy; chương trình tiếp tục sau khối.
- Màn hình khởi động giữ hành vi kết nối ở background thread và có nút Thử lại / Thoát. Thông báo được dịch và nói Firebase.

## 11. Test

Dùng `python -m unittest discover -s tests`, chỉ stdlib, không thêm dependency.

| File | Nội dung |
|---|---|
| `test_entities.py` | `total`, validation (`InvalidTransaction`) |
| `test_summary.py` | `summarize`, `totals_by_category` (gộp, sắp xếp, lọc theo type) |
| `test_categories.py` | `legacy_name_to_key` (tên đã biết, tên lạ) |
| `test_transaction_service.py` | fake in-memory: `load_period` gọi repo 1 lần; add/update; lưu ảnh trước khi ghi; ảnh lỗi thì không ghi; cache danh mục |
| `test_report_service.py` | `NoDataError`; exporter nhận đúng `PeriodReport` |
| `test_firestore_mapping.py` | round-trip; doc cũ chỉ có `category_name`; category chỉ có `name` |
| `test_receipt_storage.py` | save vào thư mục tạm; resolve tương đối/tuyệt đối/không tồn tại/rỗng |
| `test_formatters.py` | `format_money`/`parse_money` cho vi/en; `category_label` fallback |
| `test_i18n.py` | fallback en→vi→key; tham số; `vi.json` và `en.json` có cùng bộ key |
| `test_migration_plan.py` | tên đã biết/lạ; idempotent; giữ field cũ; item thiếu tên; `Khác` thu/chi |

Logic giữ giờ khi sửa giao dịch đặt trong hàm thuần `combine_date_keep_time(new_date, original)` ở `presentation/formatters.py` và có test riêng.

**Smoke test thủ công:**
1. Khởi động app.
2. Thêm, sửa, xoá, xem chi tiết giao dịch có ảnh.
3. Lọc theo ngày, xem biểu đồ.
4. Xuất Word ở cả vi và en.
5. Đổi ngôn ngữ.
6. Build Nuitka bằng `build_exe.py` và chạy thử file `.exe`.
7. Chạy dry-run migration.

## 12. Thứ tự thực hiện

1. Domain + test.
2. Application + test (dùng fake).
3. Infrastructure + test (mapping, receipt storage).
4. i18n, locales, formatters + test; charts, word exporter.
5. Presentation, container, `main.py`; xoá code cũ; cập nhật `requirements.txt` và `build_exe.py` (thêm `--include-data-dir=locales=locales`).
6. Script migration + test `plan_migration`; chạy dry-run trên dữ liệu thật.
7. Review độc lập bắt buộc.
8. Người dùng xác nhận, rồi chạy `--apply`.
