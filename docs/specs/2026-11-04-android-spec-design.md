# Bộ spec chuyển giao sang Android (Jetpack Compose)

- Ngày: 2026-11-04
- Tier: **T3** (tài liệu là hợp đồng mà project Android dùng để code; nhiều file)
- Baseline: commit `5614abe` trên `main`; làm việc trên nhánh `docs/android-spec`
- Loại việc: `content` — không sửa code app

## 1. Mục tiêu

Trích xuất toàn bộ hành vi của app desktop "Quản lý Chi tiêu" (Python/Tkinter + Firestore) thành một bộ spec để
một project Android viết bằng Jetpack Compose làm lại app tương đương, **dùng chung database Firestore** với bản desktop.

Bộ spec phải đủ để người hoặc AI agent bên Android code mà **không cần đọc mã Python**: UI, mọi thao tác click,
use case, rẽ nhánh (luồng thay thế / lỗi), sequence diagram, hợp đồng dữ liệu, chuỗi i18n.

Ngoài phạm vi: viết code Android; sửa app desktop; tính năng mà as-is không có (quản lý danh mục, xoá ảnh biên lai,
tìm kiếm, nhiều người dùng); wireframe đề xuất cho mobile (chỉ có gợi ý bằng chữ).

## 2. Quyết định đã chốt

| # | Quyết định | Hệ quả |
|---|------------|--------|
| Q1 | Android **dùng chung Firestore** với desktop | Schema hiện tại (gồm field legacy, `total_amount`, quy ước giờ) là hợp đồng cứng |
| Q2 | Mức bám: **as-is + gợi ý Compose** | Mô tả đúng hành vi hiện tại; gợi ý Android nằm trong khối riêng, không trộn |
| Q3 | Cấu trúc: **tách file theo chủ đề** (phương án A) | README + 5 file `.md` + một file `.drawio` nhiều trang + PNG |
| Q4 | Công cụ diagram: draw.io (desktop đã cài tại `C:\Users\Lecoo\AppData\Local\Programs\draw.io\draw.io.exe`) | Xuất PNG từng trang bằng CLI; không có draw.io MCP trong phiên |

## 3. Cấu trúc sản phẩm

```
docs/android-spec/
├─ README.md               # tổng quan, thuật ngữ, kiến trúc hiện tại, mục lục, thứ tự đọc
├─ 01-domain-data.md       # entity, BR, hợp đồng Firestore, legacy, quy ước giờ, receipts, migration
├─ 02-screens.md           # SCR-01..05: wireframe, thành phần, bảng sự kiện, trạng thái; định dạng báo cáo
├─ 03-use-cases.md         # UC-01..09: luồng chính/thay thế/lỗi, Given/When/Then, activity + sequence
├─ 04-i18n-format.md       # bảng 111 key vi/en, fallback, định dạng tiền/ngày, parse tiền
├─ 05-android-mapping.md   # ràng buộc C1–C4, quyết định mở D1–D5, ánh xạ Compose, ngoài phạm vi
└─ diagrams/
   ├─ spec.drawio          # một file, nhiều trang (mục 6)
   └─ png/<tên-trang>.png  # xuất từng trang, được chèn vào các file .md
```

## 4. Quy ước viết

- Tiếng Việt; tên field / key / code giữ nguyên tiếng Anh.
- ID để trích dẫn: màn hình `SCR-01..05`, use case `UC-01..09`, quy tắc nghiệp vụ `BR-xx`, ràng buộc `C1..C4`,
  quyết định mở `D1..D5`, nhánh trong UC `A1..` (thay thế) / `E1..` (lỗi). Thông báo trích bằng key i18n (`main.select_first`).
- Hành vi lạ nhưng có thật ghi đúng như hiện tại, đánh dấu **⚠ As-is** + khuyến nghị; không âm thầm "sửa" trong spec.
- Gợi ý Android đặt trong khối **💡 Gợi ý Compose** ở cuối mỗi phần.
- Mỗi diagram có bản chữ tương đương trong `.md` (bước đánh số, bảng) — agent chỉ đọc chữ không bị thiếu thông tin.
- Wireframe đánh số ①②③ khớp với cột "#" trong bảng sự kiện của màn hình đó.

## 5. Nội dung từng file

**README.md** — mục đích, phạm vi, thuật ngữ (giao dịch, hạng mục, kỳ, danh mục/key, biên lai), kiến trúc 4 tầng
hiện tại (diagram `architecture-current`), mục lục, thứ tự đọc khi code Android (01 → 04 → 02 → 03 → 05).

**01-domain-data.md**
- Entity: `TransactionType`, `TransactionItem`, `Transaction` (+ `total`), `PeriodSummary` (+ `balance`), `CategoryTotal`, `PeriodReport`.
- BR: validate giao dịch (≥1 hạng mục, danh mục không rỗng, tiền không âm); tổng; tổng theo danh mục sắp giảm dần;
  kỳ lọc `[start 00:00:00, end 23:59:59]`; danh sách mới nhất trước; mặc định kỳ = đầu tháng → hôm nay.
- Hợp đồng Firestore: collection `transactions` (field, kiểu, ai ghi, `created_at`/`updated_at`, `total_amount` để tương thích),
  `categories` (`key`, `type`; legacy `name`), item legacy `category_name`; bảng tên tiếng Việt cũ → key; seed khi rỗng;
  đọc danh mục bỏ trùng giữ thứ tự; truy vấn kỳ (`date >= start`, `date <= end`, `order by date desc`).
- Quy ước giờ (đã kiểm chứng trong `google/cloud/_helpers`): desktop ghi datetime naive giờ máy, thư viện gắn UTC.
- Ảnh biên lai: copy vào `assets/receipts/` với tiền tố `YYYYmmdd_HHMMSS_`, lưu đường dẫn tương đối vào `image_path`.
- Script `scripts/migrate_category_keys.py`: chỉ thêm field, có dry-run + backup.
- Diagram: `data-model`.

**02-screens.md** — với mỗi SCR: wireframe; bảng thành phần (tên, loại, nhãn i18n, mặc định); bảng sự kiện
(# · thao tác · điều kiện · kết quả / thông báo); trạng thái (loading, rỗng, lỗi); modal hay không, kích thước cửa sổ.
Kèm sơ đồ `navigation`, các hộp thoại dùng chung, và cấu trúc nội dung báo cáo Word.

| SCR | Màn hình | Nguồn |
|-----|----------|-------|
| SCR-01 | Loading / kết nối | `presentation/loading_window.py` |
| SCR-02 | Main (lọc, tổng quan, bảng, hành động, menu ngôn ngữ, hộp thoại lưu file) | `presentation/main_window.py` |
| SCR-03 | Form Thêm / Sửa giao dịch | `presentation/transaction_form.py` |
| SCR-04 | Chi tiết giao dịch | `presentation/transaction_detail.py` |
| SCR-05 | Biểu đồ | `presentation/chart_view.py`, `presentation/charts.py` |
| — | Báo cáo Word | `presentation/word_exporter.py` |

**03-use-cases.md** — sơ đồ `use-cases`; mỗi UC: tác nhân, tiền điều kiện, kích hoạt, luồng chính, A*/E*, hậu điều kiện,
tiêu chí nghiệm thu Given/When/Then; activity + sequence (theo mục 6).

| UC | Tên |
|----|-----|
| UC-01 | Khởi động & kết nối (Thử lại / Thoát; seed danh mục) |
| UC-02 | Xem / lọc giao dịch theo kỳ |
| UC-03 | Thêm giao dịch |
| UC-04 | Sửa giao dịch |
| UC-05 | Xem chi tiết giao dịch |
| UC-06 | Xoá giao dịch |
| UC-07 | Xem biểu đồ |
| UC-08 | Xuất báo cáo |
| UC-09 | Đổi ngôn ngữ |

**04-i18n-format.md** — bảng đủ mọi key trong `locales/vi.json` (111 key) với cột vi, en, tên gợi ý trong `strings.xml`;
fallback ngôn ngữ hiện tại → vi → key; nhãn danh mục (key mặc định thì dịch, tự gõ thì nguyên văn);
tiền (vi `1.500.000 đ`, en `1,500,000 VND`, làm tròn); ngày `dd/MM/yyyy` (chi tiết: `dd/MM/yyyy HH:mm:ss`);
`parse_money` bỏ mọi ký tự không phải chữ số.

**05-android-mapping.md** — mục 7 dưới đây, cộng diagram `architecture-android`.

## 6. Danh sách diagram (`diagrams/spec.drawio`)

| # | Trang | Loại | Nội dung | Chèn vào |
|---|-------|------|----------|----------|
| 1 | `architecture-current` | Kiến trúc | 4 tầng + Firestore + ổ đĩa (receipts, `settings.json`, `locales`) + file Word | README |
| 2 | `architecture-android` | Kiến trúc (gợi ý) | Compose UI → ViewModel → UseCase → Repository → Firestore SDK / DataStore / storage | 05 |
| 3 | `data-model` | Document/ER | `transactions` + `items[]`, `categories`, `settings.json`, thư mục receipts; legacy đánh dấu | 01 |
| 4 | `navigation` | Sơ đồ màn hình | SCR-01→02→03/04/05, hộp thoại, menu | 02 |
| 5–9 | `wf-scr01` … `wf-scr05` | Wireframe as-is | Bố cục desktop, đánh số ①②③ | 02 |
| 10 | `use-cases` | UML use case | Người dùng → UC-01..09 | 03 |
| 11–18 | `act-uc01`, `act-uc02`, `act-uc03-04`, `act-uc05`, `act-uc06`, `act-uc07`, `act-uc08`, `act-uc09` | Activity | Rẽ nhánh; lỗi tô đỏ, thay thế tô vàng | 03 |
| 19–24 | `seq-uc01`, `seq-uc02`, `seq-uc03-04`, `seq-uc05`, `seq-uc06`, `seq-uc08` | UML sequence | Luồng có I/O; nét đứt = trả về / exception | 03 |

UC-07 và UC-09 không có sequence: không có I/O đáng kể (UC-07 dùng report đã nạp; UC-09 ghi một file nhỏ).
Xuất PNG: `draw.io.exe -x -f png -p <chỉ số trang> -o diagrams/png/<tên-trang>.png diagrams/spec.drawio`.

## 7. Nội dung `05-android-mapping.md`

**Ràng buộc bắt buộc**
- **C1** Không nhúng `serviceAccountKey.json` vào APK; dùng Firebase client SDK. Admin SDK của desktop bỏ qua
  Security Rules, nên bật rules cho Android không ảnh hưởng desktop.
- **C2** Quy ước giờ: Timestamp lưu có giờ UTC = giờ hiển thị (wall-clock). Áp cho `date`, `created_at`, `updated_at`
  và hai mốc truy vấn kỳ.
- **C3** Ghi đúng schema hiện tại (cả `total_amount`); đọc chấp nhận dạng legacy (`category_name`, `name`).
- **C4** Không có khoá: hai app cùng sửa thì bản ghi sau thắng. Code Android ghi vào Firestore dùng chung là **T4**
  ở project bên kia.

**Quyết định mở** (ghi lựa chọn + khuyến nghị)

| ID | Vấn đề | Khuyến nghị |
|----|--------|-------------|
| D1 | Xác thực | Firebase Auth (Google/email) + rules chỉ cho UID trong allowlist; dữ liệu không có `userId` — một sổ chung |
| D2 | Ảnh biên lai | Lưu bộ nhớ trong app, cùng định dạng `assets/receipts/...`; ảnh của máy kia không có thì ẩn mục biên lai (như as-is khi file thiếu). Firebase Storage là task riêng |
| D3 | Xuất báo cáo | PDF (`PdfDocument`) + SAF `CreateDocument` / share, giữ cấu trúc nội dung báo cáo Word |
| D4 | Offline | Giữ offline persistence mặc định; SCR-01 thành màn khởi tạo / kiểm tra Auth |
| D5 | Cache danh mục | Giữ cache theo phiên như as-is |

**Ánh xạ gợi ý**: `Tk`/`Toplevel` → Navigation Compose destination (modal → Dialog / full-screen);
`Treeview` + chọn dòng → `LazyColumn` card (tap = chi tiết, Sửa/Xoá qua menu hoặc swipe); `messagebox` → `AlertDialog`
(lỗi, xác nhận) / `Snackbar` (thành công); `DateEntry` → M3 `DatePicker`; `Combobox` gõ được → `ExposedDropdownMenuBox`
editable; `filedialog` ảnh → Photo Picker; matplotlib → Compose `Canvas` / Vico; `settings.json` →
`AppCompatDelegate.setApplicationLocales`; `locales/*.json` → `values/strings.xml` (vi mặc định) + `values-en/`;
`threading` + poll → coroutine + `StateFlow` trong ViewModel.

**Ngoài phạm vi** (as-is không có): quản lý danh mục, xoá ảnh biên lai, tìm kiếm, nhiều người dùng.

## 8. Tiêu chí nghiệm thu bộ spec

1. Mọi handler UI trong `app/presentation/*.py` (nút, menu, radio, combobox, ô tiền, chọn file, hộp thoại) xuất hiện
   trong đúng một dòng của một bảng sự kiện SCR.
2. Mọi key trong `locales/vi.json` có trong bảng của `04-i18n-format.md`, giá trị vi/en khớp file nguồn.
3. Mọi nhánh `except` / `if` có hiệu ứng người dùng thấy được trong presentation + application được phản ánh thành
   A* hoặc E* của một UC.
4. Mọi field Firestore đọc/ghi trong `infrastructure/firestore_mapping.py` và `firestore_repository.py` có trong `01-domain-data.md`.
5. Mỗi UC có luồng chính, ≥1 tiêu chí Given/When/Then, và tham chiếu tới diagram tương ứng.
6. `spec.drawio` mở được, có đủ 24 trang đúng tên ở mục 6; mỗi trang có PNG tương ứng; mọi link ảnh trong `.md` trỏ tới file có thật.
7. Không còn "TBD"/"TODO"; các ID (SCR/UC/BR/C/D) được tham chiếu đều có định nghĩa.

## 9. Rủi ro

- Wireframe vẽ tay có thể lệch bố cục thật → lấy kích thước / thứ tự widget từ code (`pack`/`grid`), không đoán.
- File `.drawio` lớn khó review bằng diff → kiểm tra bằng cách xuất PNG và xem lại từng trang.
