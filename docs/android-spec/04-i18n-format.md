# 04 · i18n & định dạng

> Nguồn: `app/presentation/i18n.py`, `app/presentation/formatters.py`, `locales/vi.json`, `locales/en.json` (commit `5614abe`).

## Cơ chế dịch

- Hỗ trợ hai ngôn ngữ: `vi` (mặc định) và `en` (BR-16). Mỗi ngôn ngữ có một file `locales/<mã>.json` dạng `{ "key": "chuỗi" }`; hai file có cùng bộ **111 key**.
- Tra chuỗi theo thứ tự: ngôn ngữ hiện tại → `vi` → nếu vẫn không có thì trả về **chính key**. File hỏng hoặc thiếu được coi như rỗng.
- Tham số viết dạng `{amount}` và được thay bằng `str.format(**params)`.
- Ngôn ngữ đang chọn lưu ở `settings.json` (xem [01-domain-data.md](01-domain-data.md#settingsjson)).
- Đổi ngôn ngữ (UC-09) sẽ dựng lại toàn bộ cửa sổ chính bằng chuỗi mới. ⚠ As-is: cửa sổ con đang mở (form, chi tiết, biểu đồ) **giữ ngôn ngữ cũ** cho đến khi đóng.
- Hai mục trong menu ngôn ngữ (`menu.language`, `language.vi`, `language.en`) hiển thị giống nhau ở cả hai ngôn ngữ, để người dùng luôn đọc được.

## Định dạng

| Loại | Quy tắc | Ví dụ vi | Ví dụ en |
|------|---------|----------|----------|
| Tiền | Làm tròn về số nguyên (`round`), phân cách hàng nghìn, kèm đơn vị | `1.500.000 đ` | `1,500,000 VND` |
| Tiền trên biểu đồ (trục Y, nhãn trên cột) | Luôn dùng dấu `,`, không đơn vị. ⚠ As-is: không theo ngôn ngữ | `1,500,000` | `1,500,000` |
| Ngày (bảng, bộ lọc, tiêu đề biểu đồ, báo cáo) | `dd/MM/yyyy`, giống nhau cho cả hai ngôn ngữ | `04/11/2026` | `04/11/2026` |
| Ngày giờ (chi tiết giao dịch, "ngày xuất báo cáo") | `dd/MM/yyyy HH:mm:ss` | `04/11/2026 09:30:15` | như vi |
| Tên file báo cáo | `<report.file_prefix>_yyyyMMdd_HHmmss.docx` | `BaoCaoChiTieu_20261104_093015.docx` | `ExpenseReport_20261104_093015.docx` |
| Parse tiền nhập tay | Theo BR-10: bỏ mọi ký tự không phải `0-9` | `1.500.000 đ` → 1500000 | `1,500,000` → 1500000 |
| Nhãn danh mục | Theo BR-12: key mặc định thì tra `category.<key>`, key khác hiển thị nguyên văn | `food` → Ăn uống | `food` → Food & drinks |
| Nhãn loại | Ngắn `type.<type>` (bảng, báo cáo); dài `type_long.<type>` (form, chi tiết) | Thu / Khoản Thu | Income / Income |

Ô ngày (`DateEntry`) dùng mẫu `dd/mm/yyyy` cho cả hai ngôn ngữ (`app/presentation/ui_helpers.py:30-35`).

## Bảng chuỗi

Cột `strings.xml` name là tên gợi ý cho Android (thay `.` bằng `_`). Cột "Tham số" liệt kê tham số theo thứ tự xuất hiện; thứ tự này giống nhau ở vi và en (đã kiểm tra), nên có thể đánh số `%1$s`, `%2$s`… theo đúng thứ tự đó. `<br>` trong bảng là ký tự xuống dòng `\n`.

| Key | vi | en | `strings.xml` name | Tham số |
|-----|----|----|--------------------|---------|
| `dialog.error` | Lỗi | Error | `dialog_error` |  |
| `dialog.warning` | Cảnh báo | Warning | `dialog_warning` |  |
| `dialog.success` | Thành công | Success | `dialog_success` |  |
| `dialog.confirm` | Xác nhận | Confirm | `dialog_confirm` |  |
| `dialog.close` | Đóng | Close | `dialog_close` |  |
| `dialog.all_files` | Tất cả tệp | All files | `dialog_all_files` |  |
| `error.invalid_transaction` | Vui lòng nhập danh mục và số tiền hợp lệ cho ít nhất 1 hạng mục. | Please enter a category and a valid amount for at least one item. | `error_invalid_transaction` |  |
| `error.no_data` | Không có giao dịch nào trong khoảng thời gian này. | There are no transactions in this period. | `error_no_data` |  |
| `error.invalid_date` | Ngày không hợp lệ. | Invalid date. | `error_invalid_date` |  |
| `error.file` | Không đọc/ghi được tệp:<br>{detail} | Could not read/write the file:<br>{detail} | `error_file` | detail |
| `error.generic` | Đã xảy ra lỗi (vui lòng kiểm tra kết nối mạng):<br>{detail} | Something went wrong (please check your network connection):<br>{detail} | `error_generic` | detail |
| `loading.title` | Khởi động ứng dụng | Starting application | `loading_title` |  |
| `loading.connecting` | Đang kết nối đến Firebase... | Connecting to Firebase... | `loading_connecting` |  |
| `loading.reconnecting` | Đang kết nối lại... | Reconnecting... | `loading_reconnecting` |  |
| `loading.error` | Lỗi kết nối Firebase!<br>Vui lòng kiểm tra kết nối mạng hoặc file serviceAccountKey.json. | Could not connect to Firebase!<br>Please check your network connection or serviceAccountKey.json. | `loading_error` |  |
| `loading.retry` | Thử lại | Retry | `loading_retry` |  |
| `loading.exit` | Thoát | Exit | `loading_exit` |  |
| `menu.language` | Ngôn ngữ / Language | Ngôn ngữ / Language | `menu_language` |  |
| `language.vi` | Tiếng Việt | Tiếng Việt | `language_vi` |  |
| `language.en` | English | English | `language_en` |  |
| `main.title` | Phần mềm Quản lý Chi tiêu | Expense Manager | `main_title` |  |
| `main.from` | Từ ngày: | From: | `main_from` |  |
| `main.to` | Đến ngày: | To: | `main_to` |  |
| `main.filter` | Lọc | Filter | `main_filter` |  |
| `main.export_word` | Xuất Báo Cáo Word | Export Word Report | `main_export_word` |  |
| `main.add` | + Thêm Giao Dịch | + Add Transaction | `main_add` |  |
| `main.summary` | Tổng quan trong kỳ | Period overview | `main_summary` |  |
| `main.col_date` | Ngày | Date | `main_col_date` |  |
| `main.col_type` | Loại | Type | `main_col_type` |  |
| `main.col_category` | Danh mục chi tiết | Categories | `main_col_category` |  |
| `main.col_amount` | Tổng số tiền | Total | `main_col_amount` |  |
| `main.col_note` | Ghi chú chung | Note | `main_col_note` |  |
| `main.view` | Xem chi tiết | View details | `main_view` |  |
| `main.edit` | Sửa | Edit | `main_edit` |  |
| `main.delete` | Xóa | Delete | `main_delete` |  |
| `main.chart` | Xem Biểu Đồ Chi Tiêu | View Charts | `main_chart` |  |
| `main.select_first` | Vui lòng chọn một giao dịch. | Please select a transaction. | `main_select_first` |  |
| `main.confirm_delete` | Bạn có chắc chắn muốn xóa giao dịch này? | Are you sure you want to delete this transaction? | `main_confirm_delete` |  |
| `main.deleted` | Đã xóa giao dịch. | Transaction deleted. | `main_deleted` |  |
| `summary.inflow` | Tổng Thu: {amount} | Total income: {amount} | `summary_inflow` | amount |
| `summary.outflow` | Tổng Chi: {amount} | Total expense: {amount} | `summary_outflow` | amount |
| `summary.balance` | Số Dư: {amount} | Balance: {amount} | `summary_balance` | amount |
| `type.inflow` | Thu | Income | `type_inflow` |  |
| `type.outflow` | Chi | Expense | `type_outflow` |  |
| `type_long.inflow` | Khoản Thu | Income | `type_long_inflow` |  |
| `type_long.outflow` | Khoản Chi | Expense | `type_long_outflow` |  |
| `form.title_add` | Thêm Giao Dịch Mới | New Transaction | `form_title_add` |  |
| `form.title_edit` | Sửa Giao Dịch | Edit Transaction | `form_title_edit` |  |
| `form.type_frame` | Loại giao dịch | Transaction type | `form_type_frame` |  |
| `form.general_frame` | Thông tin chung | General information | `form_general_frame` |  |
| `form.date` | Ngày: | Date: | `form_date` |  |
| `form.contact` | Đối tác: | Payee: | `form_contact` |  |
| `form.note` | Ghi chú chung: | Note: | `form_note` |  |
| `form.items_frame` | Chi tiết hạng mục | Items | `form_items_frame` |  |
| `form.col_category` | Danh mục | Category | `form_col_category` |  |
| `form.col_amount` | Số tiền | Amount | `form_col_amount` |  |
| `form.col_note` | Ghi chú | Note | `form_col_note` |  |
| `form.add_item` | + Thêm hạng mục | + Add item | `form_add_item` |  |
| `form.choose_receipt` | Chọn ảnh biên lai | Choose receipt image | `form_choose_receipt` |  |
| `form.no_receipt` | Chưa chọn ảnh | No image selected | `form_no_receipt` |  |
| `form.image_files` | Tệp ảnh | Image files | `form_image_files` |  |
| `form.total` | Tổng cộng: {amount} | Total: {amount} | `form_total` | amount |
| `form.save_new` | Xác Nhận | Save | `form_save_new` |  |
| `form.save_edit` | Lưu Thay Đổi | Save changes | `form_save_edit` |  |
| `form.added` | Đã thêm giao dịch! | Transaction added! | `form_added` |  |
| `form.updated` | Đã cập nhật giao dịch! | Transaction updated! | `form_updated` |  |
| `detail.title` | Chi Tiết Giao Dịch | Transaction Details | `detail_title` |  |
| `detail.general` | Thông tin chung | General information | `detail_general` |  |
| `detail.type` | Loại giao dịch: {value} | Type: {value} | `detail_type` | value |
| `detail.date` | Ngày giờ: {value} | Date & time: {value} | `detail_date` | value |
| `detail.total` | Tổng số tiền: {value} | Total amount: {value} | `detail_total` | value |
| `detail.contact` | Đối tác: {value} | Payee: {value} | `detail_contact` | value |
| `detail.note` | Ghi chú chung: {value} | Note: {value} | `detail_note` | value |
| `detail.items` | Hạng mục chi tiết | Items | `detail_items` |  |
| `detail.receipt` | Biên lai | Receipt | `detail_receipt` |  |
| `detail.receipt_error` | Không thể tải ảnh biên lai | Could not load the receipt image | `detail_receipt_error` |  |
| `chart.window_title` | Biểu đồ Thu/Chi | Income/Expense Charts | `chart_window_title` |  |
| `chart.heading` | Thống kê giao dịch từ {start} đến {end} | Transactions from {start} to {end} | `chart_heading` | start, end |
| `chart.no_data` | Không có dữ liệu | No data | `chart_no_data` |  |
| `chart.no_data_period` | Không có dữ liệu trong khoảng thời gian này. | No data in this period. | `chart_no_data_period` |  |
| `chart.inflow_title` | Tổng Thu Theo Hạng Mục | Income by Category | `chart_inflow_title` |  |
| `chart.outflow_title` | Tổng Chi Theo Hạng Mục | Expense by Category | `chart_outflow_title` |  |
| `chart.y_label` | Số tiền (VND) | Amount (VND) | `chart_y_label` |  |
| `report.title` | BÁO CÁO QUẢN LÝ CHI TIÊU | EXPENSE REPORT | `report_title` |  |
| `report.period` | Từ ngày: {start} - Đến ngày: {end} | From: {start} - To: {end} | `report_period` | start, end |
| `report.exported_at` | Ngày xuất báo cáo: {time} | Exported at: {time} | `report_exported_at` | time |
| `report.section_overview` | 1. Tổng quan | 1. Overview | `report_section_overview` |  |
| `report.section_charts` | 2. Biểu đồ thống kê | 2. Charts | `report_section_charts` |  |
| `report.section_details` | 3. Bảng kê chi tiết | 3. Transaction details | `report_section_details` |  |
| `report.balance` | Số dư trong kỳ: {amount} | Period balance: {amount} | `report_balance` | amount |
| `report.col_date` | Ngày | Date | `report_col_date` |  |
| `report.col_type` | Loại | Type | `report_col_type` |  |
| `report.col_items` | Hạng mục chi tiết | Items | `report_col_items` |  |
| `report.col_total` | Tổng tiền | Total | `report_col_total` |  |
| `report.col_note` | Ghi chú chung | Note | `report_col_note` |  |
| `report.item_purpose` |  (Mục đích: {note}) |  (Purpose: {note}) | `report_item_purpose` | note |
| `report.file_prefix` | BaoCaoChiTieu | ExpenseReport | `report_file_prefix` |  |
| `report.file_type` | Tài liệu Word | Word Document | `report_file_type` |  |
| `report.save_title` | Chọn vị trí lưu báo cáo | Choose where to save the report | `report_save_title` |  |
| `report.exported` | Đã xuất báo cáo tại:<br>{path} | Report exported to:<br>{path} | `report_exported` | path |
| `category.salary` | Lương | Salary | `category_salary` |  |
| `category.bonus` | Thưởng | Bonus | `category_bonus` |  |
| `category.passive_income` | Thu nhập thụ động | Passive income | `category_passive_income` |  |
| `category.sales` | Bán hàng | Sales | `category_sales` |  |
| `category.other` | Khác | Other | `category_other` |  |
| `category.food` | Ăn uống | Food & drinks | `category_food` |  |
| `category.bills` | Hóa đơn | Bills | `category_bills` |  |
| `category.transport` | Di chuyển | Transport | `category_transport` |  |
| `category.shopping` | Mua sắm | Shopping | `category_shopping` |  |
| `category.health` | Sức khỏe | Health | `category_health` |  |
| `category.entertainment` | Giải trí | Entertainment | `category_entertainment` |  |

## 💡 Gợi ý Compose

- `res/values/strings.xml` chứa tiếng Việt (mặc định, khớp với fallback `vi`); `res/values-en/strings.xml` chứa tiếng Anh. Thêm `res/xml/locales_config.xml` khai báo `vi`, `en`.
- Tham số `{x}` đổi thành `%1$s`, `%2$s`… theo cột "Tham số". Ví dụ: `chart_heading` = `Thống kê giao dịch từ %1$s đến %2$s`. Gọi bằng `stringResource(R.string.chart_heading, start, end)`.
- Khi chép sang `strings.xml` phải escape: `&` thành `&amp;`, `<` thành `&lt;`, dấu nháy đơn thành `\'`. Ví dụ: `category_food` (en) = `Food &amp; drinks`.
- Tiền nên định dạng bằng code (`NumberFormat` hoặc ghép chuỗi), không đặt trong `strings.xml`. Ký hiệu `đ` / `VND` phụ thuộc ngôn ngữ đang chọn, không phụ thuộc locale máy.
- Nhãn danh mục:
  ```kotlin
  @Composable
  fun categoryLabel(key: String): String = when (key) {
      "salary" -> stringResource(R.string.category_salary)
      // ... 11 key mặc định ...
      else -> key // danh mục tự đặt: hiển thị nguyên văn (BR-12)
  }
  ```
- Đổi ngôn ngữ trong app: dùng `AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags("vi"))`. Hệ thống tự lưu lựa chọn và tạo lại Activity, nên không cần file `settings.json`.
