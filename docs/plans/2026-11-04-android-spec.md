# Bộ spec chuyển giao Android (Compose) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans (inline default). Select bounded delegation or parallel waves only under task-tiering's execution-mode policy. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Viết bộ tài liệu `docs/android-spec/` (README + 5 file `.md` + `diagrams/spec.drawio` 24 trang + PNG) mô tả đầy đủ app desktop để làm lại bằng Jetpack Compose, dùng chung Firestore.

**Architecture:** Nội dung `.md` viết tay từ việc đọc code (nguồn ghi ở từng task). Diagram sinh bằng một script Python dùng một lần, đặt trong scratchpad (không commit), ghi ra `spec.drawio` dạng XML không nén rồi gọi draw.io CLI để xuất PNG từng trang. Một script kiểm tra (cũng trong scratchpad) làm acceptance check tự động cho các tiêu chí đo được ở mục 8 của spec.

**Tech Stack:** Markdown; draw.io desktop CLI `C:\Users\Lecoo\AppData\Local\Programs\draw.io\draw.io.exe`; Python `.venv/Scripts/python.exe -I` (chỉ stdlib) cho script sinh diagram, sinh bảng i18n và kiểm tra.

**Spec:** `docs/specs/2026-11-04-android-spec-design.md`

## Global Constraints

- Mọi lệnh chạy từ gốc repo `D:\DuAn\DuAnQuanLyChiTieu`. Biến `SP` = scratchpad `C:\Users\Lecoo\AppData\Local\Temp\claude\2627e66dd68f5ef1\4d5f477f-884d-4a5e-8b6c-c0be6aadd0d8\scratchpad`.
- Không sửa bất kỳ file nào trong `app/`, `locales/`, `scripts/`, `tests/`.
- Tiếng Việt; tên field / key / code giữ nguyên tiếng Anh.
- ID: `SCR-01..05`, `UC-01..09`, `BR-01..`, `C1..C4`, `D1..D5`; nhánh trong UC `A1..` / `E1..`. Định nghĩa ID = dòng tiêu đề chứa ID, hoặc ô đầu của dòng bảng (chữ đậm trong câu văn không tính).
- Hành vi lạ ghi đúng như code, đánh dấu `⚠ As-is` + khuyến nghị. Gợi ý Android chỉ nằm trong khối `💡 Gợi ý Compose`.
- Mỗi diagram có bản chữ tương đương trong `.md`. Wireframe đánh số ①②③ khớp cột `#` trong bảng sự kiện.
- Ảnh chèn bằng đường dẫn tương đối `diagrams/png/<tên-trang>.png`.
- 24 trang theo đúng thứ tự: `architecture-current, architecture-android, data-model, navigation, wf-scr01, wf-scr02, wf-scr03, wf-scr04, wf-scr05, use-cases, act-uc01, act-uc02, act-uc03-04, act-uc05, act-uc06, act-uc07, act-uc08, act-uc09, seq-uc01, seq-uc02, seq-uc03-04, seq-uc05, seq-uc06, seq-uc08`.
- Số key i18n: 111 (vi và en cùng bộ key).
- **No auto-commit:** Do not include `git commit` / "Step N: Commit" in any task. Commit only after **all tasks are complete** and the **user agrees** (ask once at the end).

---

### Task 1: Acceptance checker

**Files:**
- Create: `$SP/check_spec.py`

**Interfaces:**
- Produces: `python -I $SP/check_spec.py <repo_root>` → in từng vấn đề, exit 1; hoặc in `OK`, exit 0. Các task sau dùng lệnh này làm acceptance check.

- [ ] **Step 1: Viết script kiểm tra**

```python
"""Acceptance check cho docs/android-spec (tiêu chí mục 8 của spec). Chạy: python -I check_spec.py <repo_root>"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(sys.argv[1])
SPEC = ROOT / "docs" / "android-spec"
FILES = ["README.md", "01-domain-data.md", "02-screens.md", "03-use-cases.md", "04-i18n-format.md",
         "05-android-mapping.md"]
PAGES = ["architecture-current", "architecture-android", "data-model", "navigation",
         "wf-scr01", "wf-scr02", "wf-scr03", "wf-scr04", "wf-scr05", "use-cases",
         "act-uc01", "act-uc02", "act-uc03-04", "act-uc05", "act-uc06", "act-uc07", "act-uc08", "act-uc09",
         "seq-uc01", "seq-uc02", "seq-uc03-04", "seq-uc05", "seq-uc06", "seq-uc08"]
# Phần tử tương tác + thông báo phải có trong bảng sự kiện (02-screens.md)
UI_KEYS = ["loading.retry", "loading.exit", "loading.error", "loading.reconnecting", "menu.language",
           "language.vi", "language.en", "main.from", "main.to", "main.filter", "main.export_word", "main.add",
           "main.view", "main.edit", "main.delete", "main.chart", "main.select_first", "main.confirm_delete",
           "main.deleted", "form.type_frame", "form.date", "form.contact", "form.note", "form.add_item",
           "form.choose_receipt", "form.image_files", "form.save_new", "form.save_edit", "form.added",
           "form.updated", "form.total", "dialog.close", "report.save_title", "report.exported",
           "chart.no_data_period", "chart.no_data", "detail.receipt_error"]
ERROR_KEYS = ["error.invalid_transaction", "error.no_data", "error.invalid_date", "error.file", "error.generic",
              "loading.error"]
FIELDS = ["transactions", "categories", "type", "total_amount", "items", "category_key", "amount", "item_note",
          "date", "general_note", "image_path", "contact_person", "created_at", "updated_at", "category_name",
          "key", "name", "language"]
problems: list[str] = []


def cell(value: str) -> str:
    """Cách hiển thị một chuỗi i18n trong ô bảng Markdown (dùng chung với script sinh bảng)."""
    return value.replace("|", "\\|").replace("\n", "<br>")


docs = {}
for name in FILES:
    path = SPEC / name
    if path.is_file():
        docs[name] = path.read_text(encoding="utf-8")
    else:
        problems.append(f"thiếu file {name}")
alltext = "\n".join(docs.values())

# Tiêu chí 2: i18n
vi = json.loads((ROOT / "locales" / "vi.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "locales" / "en.json").read_text(encoding="utf-8"))
rows = {m.group(1): line for line in docs.get("04-i18n-format.md", "").splitlines()
        if (m := re.match(r"\|\s*`([a-z_]+\.[a-z0-9_]+)`\s*\|", line))}
for key in vi:
    if key not in rows:
        problems.append(f"i18n thiếu key {key}")
    elif cell(vi[key]) not in rows[key] or cell(en[key]) not in rows[key]:
        problems.append(f"i18n sai giá trị {key}")

# Tiêu chí 1 + 3: phần tử UI và nhánh lỗi
screens, usecases = docs.get("02-screens.md", ""), docs.get("03-use-cases.md", "")
problems += [f"02-screens thiếu `{k}`" for k in UI_KEYS if f"`{k}`" not in screens]
problems += [f"03-use-cases thiếu `{k}`" for k in ERROR_KEYS if f"`{k}`" not in usecases]

# Tiêu chí 4: field Firestore
domain = docs.get("01-domain-data.md", "")
problems += [f"01-domain-data thiếu field `{f}`" for f in FIELDS if f"`{f}`" not in domain]

# Tiêu chí 5: mỗi UC có heading, Given/When/Then, ảnh diagram
for n in range(1, 10):
    uc = f"UC-0{n}"
    match = re.search(rf"^## {uc}\b.*?(?=^## UC-0|\Z)", usecases, re.S | re.M)
    if not match:
        problems.append(f"thiếu mục ## {uc}")
        continue
    body = match.group(0)
    if not all(w in body for w in ("Given", "When", "Then")):
        problems.append(f"{uc} thiếu Given/When/Then")
    if "diagrams/png/act-uc0" not in body:
        problems.append(f"{uc} thiếu ảnh activity")

# Tiêu chí 6: drawio + PNG + link ảnh
drawio = SPEC / "diagrams" / "spec.drawio"
if drawio.is_file():
    names = [d.get("name") for d in ET.parse(drawio).getroot().iter("diagram")]
    if names != PAGES:
        problems.append(f"trang drawio sai: {names}")
else:
    problems.append("thiếu diagrams/spec.drawio")
for page in PAGES:
    if not (SPEC / "diagrams" / "png" / f"{page}.png").is_file():
        problems.append(f"thiếu png {page}")
    if f"diagrams/png/{page}.png" not in alltext:
        problems.append(f"không file .md nào chèn {page}.png")
for name, text in docs.items():
    for link in re.findall(r"\]\(([^)#\s]+)", text):
        if not link.startswith("http") and not (SPEC / link).exists():
            problems.append(f"{name}: link hỏng {link}")

# Tiêu chí 7: placeholder + ID có định nghĩa
for word in ("TBD", "TODO"):
    if word in alltext:
        problems.append(f"còn chữ {word}")
for ref in sorted(set(re.findall(r"\b(?:SCR-0\d|UC-0\d|BR-\d\d|[CD][1-9])\b", alltext))):
    defined = re.search(rf"(^#+ .*\b{ref}\b)|(^\|\s*\**{ref}\**\s*\|)", alltext, re.M)
    if not defined:
        problems.append(f"ID {ref} được dùng nhưng không có định nghĩa")

print("\n".join(problems) if problems else "OK")
sys.exit(1 if problems else 0)
```

- [ ] **Step 2: Chạy để xác nhận script bắt được lỗi khi chưa có gì**

Run: `.venv/Scripts/python.exe -I "$SP/check_spec.py" .`
Expected: exit 1, liệt kê `thiếu file README.md` … và `thiếu diagrams/spec.drawio`.

---

### Task 2: Script sinh diagram + xuất PNG

> **Cập nhật sau Step 1 (theo skill `drawio:drawio`, đã thử với draw.io 31.3.2):** 19 trang không phải wireframe viết bằng
> **Mermaid** (`$SP/diagrams/<tên-trang>.mmd`) rồi chuyển bằng `draw.io.exe -x -f xml --uncompressed -o <x>.drawio <x>.mmd`
> (layout tự động, shape gốc, sửa được). Chỉ 5 trang `wf-scr*` dựng bằng XML qua `drawio_kit`. Bỏ `node()` và `sequence()`.
> `build_spec(order, mmd_dir, xml_pages, out)` ghép từng `<diagram>` vào `spec.drawio`, đặt `name`/`id` = tên trang.
> Màu: `classDef err fill:#f8cecc,stroke:#b85450` (lỗi), `classDef alt fill:#fff2cc,stroke:#d6b656` (thay thế).

**Files:**
- Create: `$SP/drawio_kit.py` (thư viện nhỏ), `$SP/gen_diagrams.py` (định nghĩa 24 trang; các task 3, 5, 6, 7 thêm trang vào đây)
- Create: `docs/android-spec/diagrams/spec.drawio`, `docs/android-spec/diagrams/png/*.png` (sinh ra)

**Interfaces:**
- Produces (trong `drawio_kit.py`):
  - `Page(name)`; `page.vertex(x, y, w, h, value, style) -> str`; `page.edge(src, dst, value="", style=EDGE) -> str`; `page.line(x1, y1, x2, y2, value="", style=MSG) -> str`
  - `node(page, col, row, text, style=PROC, w=180, h=60) -> str` — lưới activity: `x = 40 + col*240`, `y = 40 + row*100`, căn giữa ô.
  - `sequence(page, participants: list[str], steps: list[tuple]) -> None` — bước: `("msg", a, b, text)`, `("ret", a, b, text)`, `("self", a, text)`, `("note", a, text)`, `("frame", label, first_step_index, last_step_index)`.
  - Wireframe: `window(page, x, y, w, h, title) -> (cx, cy)` (toạ độ góc trong vùng nội dung), `button`, `entry`, `label`, `group`, `table(page, x, y, columns: list[tuple[str, int]], rows: list[list[str]])`, `callout(page, n, x, y)`.
  - Style: `PROC, DECISION, START, END, ERROR, ALT, EDGE, MSG, RET, LIFELINE, FRAME, ACTOR, USECASE, NOTE, CALLOUT, BOX, DB, FOLDER`.
  - `build(pages: list[Page], out_path)`; `export(out_path, png_dir, names)` gọi draw.io CLI với chỉ số trang bắt đầu từ 1.

- [ ] **Step 1: Đọc skill `drawio:drawio`** để lấy quy ước của skill (style, cách xuất). Nếu skill khác với các mục dưới, theo skill và cập nhật interface ở trên.

- [ ] **Step 2: Viết `drawio_kit.py`**

```python
"""Bộ dựng file .drawio không nén + xuất PNG bằng draw.io desktop. Dùng một lần, không commit."""
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

DRAWIO = r"C:\Users\Lecoo\AppData\Local\Programs\draw.io\draw.io.exe"
_BASE = "whiteSpace=wrap;html=1;"
PROC = "rounded=1;" + _BASE + "fillColor=#dae8fc;strokeColor=#6c8ebf;"
DECISION = "rhombus;" + _BASE + "fillColor=#ffffff;"
START = "ellipse;html=1;fillColor=#000000;strokeColor=#000000;"
END = "ellipse;shape=doubleEllipse;html=1;fillColor=#000000;strokeColor=#000000;"
ERROR = "rounded=1;" + _BASE + "fillColor=#f8cecc;strokeColor=#b85450;"
ALT = "rounded=1;" + _BASE + "fillColor=#fff2cc;strokeColor=#d6b656;"
BOX = "rounded=0;" + _BASE + "fillColor=#f5f5f5;strokeColor=#666666;"
DB = "shape=cylinder3;" + _BASE + "size=10;fillColor=#d5e8d4;strokeColor=#82b366;"
FOLDER = "shape=folder;" + _BASE + "tabWidth=40;tabHeight=14;fillColor=#ffe6cc;strokeColor=#d79b00;"
NOTE = "shape=note;" + _BASE + "size=14;fillColor=#f5f5f5;align=left;spacingLeft=6;"
EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;"
MSG = "html=1;endArrow=block;endFill=1;verticalAlign=bottom;"
RET = "html=1;endArrow=open;dashed=1;verticalAlign=bottom;"
LIFELINE = "shape=umlLifeline;perimeter=lifelinePerimeter;" + _BASE + "container=0;collapsible=0;size=40;"
FRAME = "shape=umlFrame;" + _BASE + "width=160;height=24;fillColor=none;"
ACTOR = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;"
USECASE = "ellipse;" + _BASE
CALLOUT = "ellipse;html=1;fillColor=#e51400;fontColor=#ffffff;strokeColor=none;fontStyle=1;fontSize=11;"
W_WINDOW = "rounded=0;html=1;fillColor=#ffffff;strokeColor=#333333;"
W_TITLE = "rounded=0;html=1;fillColor=#e6e6e6;strokeColor=#333333;align=left;spacingLeft=8;fontStyle=1;"
W_BUTTON = "rounded=1;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
W_ENTRY = "rounded=0;html=1;fillColor=#ffffff;strokeColor=#999999;align=left;spacingLeft=4;"
W_GROUP = "rounded=0;html=1;fillColor=none;strokeColor=#999999;verticalAlign=top;align=left;spacingLeft=8;"
W_TEXT = "text;html=1;align=left;verticalAlign=middle;"


class Page:
    def __init__(self, name: str):
        self.name, self.cells, self._n = name, [], 0

    def _id(self) -> str:
        self._n += 1
        return f"{self.name}-{self._n}"

    def vertex(self, x, y, w, h, value, style) -> str:
        cid = self._id()
        self.cells.append(f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} vertex="1" '
                          f'parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def edge(self, src, dst, value="", style=EDGE) -> str:
        cid = self._id()
        self.cells.append(f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} edge="1" '
                          f'parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>')
        return cid

    def line(self, x1, y1, x2, y2, value="", style=MSG) -> str:
        cid = self._id()
        self.cells.append(f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} edge="1" '
                          f'parent="1"><mxGeometry relative="1" as="geometry">'
                          f'<mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" as="targetPoint"/>'
                          f'</mxGeometry></mxCell>')
        return cid

    def xml(self) -> str:
        return (f'<diagram id="{self.name}" name="{self.name}"><mxGraphModel grid="1" gridSize="10" page="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(self.cells)}</root>'
                f'</mxGraphModel></diagram>')


def node(page, col, row, text, style=PROC, w=180, h=60) -> str:
    if style in (START, END):
        w = h = 30
    elif style == DECISION:
        w, h = 160, 80
    return page.vertex(40 + col * 240 + (180 - w) / 2, 40 + row * 100 + (60 - h) / 2, w, h, text, style)


def sequence(page, participants, steps, gap=200, step_h=46) -> None:
    xs = {name: 40 + i * gap + 70 for i, name in enumerate(participants)}
    height = 90 + step_h * (len(steps) + 1)
    for name, cx in xs.items():
        page.vertex(cx - 70, 20, 140, height, name, LIFELINE)
    ys = []
    for i, step in enumerate(steps):
        y = 90 + step_h * i
        ys.append(y)
        kind = step[0]
        if kind in ("msg", "ret"):
            _, a, b, text = step
            page.line(xs[a], y, xs[b], y, text, MSG if kind == "msg" else RET)
        elif kind == "self":
            _, a, text = step
            page.line(xs[a], y, xs[a] + 40, y + 20, text, MSG + "edgeStyle=orthogonalEdgeStyle;")
        elif kind == "note":
            _, a, text = step
            page.vertex(xs[a] + 8, y - 16, 220, 34, text, NOTE)
    for step in steps:
        if step[0] == "frame":
            _, label, first, last = step
            left, right = min(xs.values()) - 90, max(xs.values()) + 90
            page.vertex(left, ys[first] - 30, right - left, ys[last] - ys[first] + 46, label, FRAME)


def window(page, x, y, w, h, title):
    page.vertex(x, y, w, h, "", W_WINDOW)
    page.vertex(x, y, w, 28, title, W_TITLE)
    return x + 10, y + 38


def button(page, x, y, text, w=110, h=28):
    return page.vertex(x, y, w, h, text, W_BUTTON)


def entry(page, x, y, text="", w=140, h=26):
    return page.vertex(x, y, w, h, text, W_ENTRY)


def label(page, x, y, text, w=140, h=26, extra=""):
    return page.vertex(x, y, w, h, text, W_TEXT + extra)


def group(page, x, y, w, h, title):
    return page.vertex(x, y, w, h, title, W_GROUP)


def table(page, x, y, columns, rows, row_h=24):
    cx = x
    for title, width in columns:
        page.vertex(cx, y, width, row_h, f"<b>{title}</b>", BOX)
        for r, row in enumerate(rows):
            col = [c[0] for c in columns].index(title)
            page.vertex(cx, y + row_h * (r + 1), width, row_h, row[col], W_ENTRY)
        cx += width


def callout(page, n, x, y):
    return page.vertex(x, y, 22, 22, str(n), CALLOUT)


def build(pages, out_path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    body = "".join(p.xml() for p in pages)
    Path(out_path).write_text(f'<mxfile host="drawio" compressed="false">{body}</mxfile>', encoding="utf-8")


def export(out_path, png_dir, names) -> None:
    Path(png_dir).mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(names, start=1):  # draw.io CLI: --page-index bắt đầu từ 1
        subprocess.run([DRAWIO, "-x", "-f", "png", "-p", str(index), "-b", "10",
                        "-o", str(Path(png_dir) / f"{name}.png"), str(out_path)], check=True)
```

- [ ] **Step 3: Viết `gen_diagrams.py` với 2 trang thử** (`architecture-current` sơ bộ và một trang `act-uc06` ngắn) để kiểm chứng pipeline:

```python
"""Sinh docs/android-spec/diagrams/spec.drawio và PNG. Chạy: python -I gen_diagrams.py <repo_root> [--export]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from drawio_kit import *  # noqa: E402,F403

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(sys.argv[1])
OUT = ROOT / "docs" / "android-spec" / "diagrams" / "spec.drawio"
PNG = OUT.parent / "png"
PAGES = []  # mỗi hàm page_*() append một Page rồi được gọi ngay sau định nghĩa

# Các hàm page_<tên>() (Task 3, 5, 6, 7) đặt ở đây, giữa PAGES và ORDER.

ORDER = [  # thứ tự trang trong file = thứ tự này, không phụ thuộc thứ tự định nghĩa hàm"architecture-current", "architecture-android", "data-model", "navigation",
         "wf-scr01", "wf-scr02", "wf-scr03", "wf-scr04", "wf-scr05", "use-cases",
         "act-uc01", "act-uc02", "act-uc03-04", "act-uc05", "act-uc06", "act-uc07", "act-uc08", "act-uc09",
         "seq-uc01", "seq-uc02", "seq-uc03-04", "seq-uc05", "seq-uc06", "seq-uc08"]
pages = {p.name: p for p in PAGES}
selected = [pages[name] for name in ORDER if name in pages]  # khi chưa đủ 24 trang vẫn chạy được
build(selected, OUT)
if "--export" in sys.argv:
    export(OUT, PNG, [p.name for p in selected])
print(f"{len(selected)} trang -> {OUT}")
```

Mỗi trang là một hàm gọi lúc import, ví dụ:

```python
def page_act_uc06():
    p = Page("act-uc06"); PAGES.append(p)
    s = node(p, 0, 0, "", START)
    a = node(p, 0, 1, "Bấm `Xóa` (main.delete)")
    d = node(p, 0, 2, "Đã chọn dòng?", DECISION)
    w = node(p, 1, 2, "Cảnh báo main.select_first", ALT)
    p.edge(s, a); p.edge(a, d); p.edge(d, w, "Không")
page_act_uc06()
```

- [ ] **Step 4: Chạy sinh + xuất, kiểm tra chỉ số trang**

Run: `.venv/Scripts/python.exe -I "$SP/gen_diagrams.py" . --export`
Expected: in `2 trang -> ...spec.drawio`; có `png/architecture-current.png` và `png/act-uc06.png`.
Acceptance: mở bằng Read hai PNG — mỗi ảnh đúng trang của nó (nếu lệch, CLI dùng chỉ số 0: sửa `start=0` trong `export`). Chữ tiếng Việt hiển thị đúng dấu.

---

### Task 3: `01-domain-data.md` + trang `data-model`

**Files:**
- Create: `docs/android-spec/01-domain-data.md`
- Modify: `$SP/gen_diagrams.py` (thêm `page_data_model`)

**Nguồn:** `app/domain/entities.py`, `categories.py`, `summary.py`; `app/application/transaction_service.py`, `report_service.py`; `app/infrastructure/firestore_mapping.py`, `firestore_repository.py`, `receipt_storage.py`; `app/presentation/formatters.py`, `i18n.py`, `main_window.py:272-274,392-393`; `scripts/migrate_category_keys.py`.

- [ ] **Step 1: Viết file theo dàn ý**

1. `## Entity` — bảng field/kiểu/ràng buộc cho `TransactionType` (`inflow`/`outflow`), `TransactionItem` (`category_key`, `amount`, `note`), `Transaction` (`type`, `date`, `items`, `general_note`, `contact_person`, `receipt_path`, `id`, thuộc tính `total`), `PeriodSummary` (`inflow`, `outflow`, `balance`), `CategoryTotal`, `PeriodReport`. Lỗi `InvalidTransaction`, `NoDataError`.
2. `## Quy tắc nghiệp vụ` — bảng `| **BR-xx** | quy tắc | nguồn |`:
   - BR-01 ≥1 hạng mục; BR-02 `category_key.strip()` không rỗng; BR-03 `amount >= 0` (form chỉ giữ dòng có tiền > 0);
   - BR-04 tổng giao dịch = tổng `amount`; BR-05 thu/chi/số dư của kỳ; BR-06 tổng theo danh mục: theo từng loại, cộng theo `category_key`, sắp giảm dần, bằng nhau giữ thứ tự xuất hiện đầu tiên (danh sách mới nhất trước);
   - BR-07 kỳ = `[ngày bắt đầu 00:00:00, ngày kết thúc 23:59:59]`, mặc định ngày 1 tháng hiện tại → hôm nay; không kiểm tra bắt đầu ≤ kết thúc (⚠ As-is: khoảng ngược cho danh sách rỗng);
   - BR-08 danh sách mới nhất trước, bảng kê báo cáo cũ nhất trước; BR-09 ngày giao dịch = ngày chọn + giờ gốc (sửa) hoặc giờ hiện tại (thêm);
   - BR-10 parse tiền: bỏ mọi ký tự không phải chữ số (⚠ As-is: `"1,5"` → 15; `"-200"` → 200); BR-11 suy key danh mục từ chữ nhập: nhãn đang hiển thị → key; tên tiếng Việt cũ → key; còn lại dùng nguyên văn làm key (danh mục tự đặt);
   - BR-12 nhãn danh mục: key mặc định thì dịch, còn lại hiển thị nguyên văn; BR-13 ảnh biên lai được copy trước khi ghi Firestore; copy lỗi thì không ghi gì (⚠ As-is: copy xong mà ghi Firestore lỗi thì file mồ côi);
   - BR-14 seed 11 danh mục khi collection `categories` rỗng; BR-15 đọc dữ liệu legacy và giá trị thiếu (mục 4); BR-16 ngôn ngữ mặc định `vi`, chỉ nhận `vi`/`en`.
3. `## Hợp đồng Firestore` + ảnh `diagrams/png/data-model.png`:
   - `transactions`: bảng `| field | kiểu Firestore | ghi khi | đọc như thế nào |` cho `type` (string), `total_amount` (double, chỉ ghi, không đọc), `items` (array of map `category_key`/`amount` double/`item_note`), `date` (timestamp), `general_note`, `image_path`, `contact_person` (string), `created_at` (timestamp, khi thêm), `updated_at` (timestamp, khi sửa). Ghi bằng `add()` (id tự sinh) và `update()` (lỗi nếu document đã bị xoá).
   - Truy vấn kỳ: `date >= start`, `date <= end`, `orderBy(date, DESC)`; một field nên không cần composite index.
   - `categories`: `key` (string), `type` (string); legacy `name`. Truy vấn `type == <loại>`, không `orderBy` (⚠ As-is: thứ tự theo document id), bỏ trùng giữ thứ tự, cache theo phiên.
   - Bảng 11 tên tiếng Việt cũ → key (từ `LEGACY_NAME_TO_KEY`), chuẩn hoá Unicode NFC + `strip()`.
   - Thứ tự seed: inflow `salary, bonus, passive_income, sales, other`; outflow `food, bills, transport, shopping, health, entertainment, other`.
4. `## Đọc dữ liệu cũ và giá trị thiếu` — `category_key` thiếu → suy từ `category_name` (thiếu nốt → `other`); `amount` thiếu → 0; `general_note`/`contact_person`/`image_path` thiếu hoặc null → `""`; ⚠ As-is: document có `items` rỗng, `amount` âm hoặc `type` lạ làm hỏng cả lần tải kỳ (hiện `error.invalid_transaction` / `error.generic`), khuyến nghị Android bỏ qua document lỗi và ghi log.
5. `## Quy ước thời gian` — desktop ghi datetime naive (giờ máy); `google.cloud._helpers._microseconds_from_datetime` gắn UTC; đọc lại bỏ tz. Ví dụ: 10:00 giờ VN lưu thành `10:00:00Z`. Tham chiếu C2.
6. `## Ảnh biên lai` — chọn `.jpg/.jpeg/.png`; khi lưu copy vào `<thư mục app>/assets/receipts/YYYYmmdd_HHMMSS_<tên gốc>`; `image_path` = `assets/receipts/...` (dấu `/`); dữ liệu cũ có thể là đường dẫn tuyệt đối; không có cách xoá ảnh; sửa giao dịch mà không chọn ảnh mới thì giữ ảnh cũ.
7. `## settings.json` — `{"language": "vi"|"en"}` cạnh app; thiếu/hỏng → `vi`.
8. `## Migration danh mục` — `scripts/migrate_category_keys.py`: dry-run mặc định, `--apply` backup ra `backups/` rồi chỉ thêm field `key` / `category_key`, không xoá field cũ; chạy lại an toàn.
9. `💡 Gợi ý Compose` — data class Kotlin tương ứng; đọc `amount` bằng `(it as Number).toDouble()`; ghi `Double`.

- [ ] **Step 2: Thêm trang `data-model`** vào `gen_diagrams.py`: ba khối BOX `transactions/{autoId}` (liệt kê field + kiểu, field legacy `category_name` tô ALT), `categories/{autoId}` (`key`, `type`, legacy `name` tô ALT), `settings.json` (FOLDER), `assets/receipts/` (FOLDER); cạnh `items[].category_key → categories.key` nét đứt "khớp theo key (không phải khoá ngoại)"; `image_path → assets/receipts/` nét đứt "đường dẫn tương đối, chỉ trên máy desktop".

- [ ] **Step 3: Acceptance**

Run: `.venv/Scripts/python.exe -I "$SP/gen_diagrams.py" . --export` rồi Read `docs/android-spec/diagrams/png/data-model.png`.
Run: `.venv/Scripts/python.exe -I "$SP/check_spec.py" . | grep "01-domain-data"` → Expected: không có dòng nào (đủ field).
Đối chiếu tay: mỗi BR có cột nguồn trỏ đúng file:dòng.

---

### Task 4: `04-i18n-format.md`

**Files:**
- Create: `$SP/gen_i18n_table.py`, `docs/android-spec/04-i18n-format.md`

- [ ] **Step 1: Viết script sinh bảng**

```python
"""In bảng Markdown 111 key i18n. Chạy: python -I gen_i18n_table.py <repo_root>"""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
vi = json.loads((root / "locales" / "vi.json").read_text(encoding="utf-8"))
en = json.loads((root / "locales" / "en.json").read_text(encoding="utf-8"))


def cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def android_name(key: str) -> str:
    return key.replace(".", "_")


def android_format(value: str) -> str:
    params = list(dict.fromkeys(re.findall(r"\{(\w+)\}", value)))
    for i, name in enumerate(params, start=1):
        value = value.replace("{" + name + "}", f"%{i}$s")
    return value


print("| Key | vi | en | `strings.xml` name | Tham số |")
print("|-----|----|----|--------------------|---------|")
for key in vi:
    params = ", ".join(dict.fromkeys(re.findall(r"\{(\w+)\}", vi[key])))
    print(f"| `{key}` | {cell(vi[key])} | {cell(en[key])} | `{android_name(key)}` | {params} |")
```

- [ ] **Step 2: Viết file theo dàn ý**
  1. `## Cơ chế dịch` — tra theo thứ tự: ngôn ngữ hiện tại → `vi` → trả về chính key; tham số dạng `{amount}`; ngôn ngữ lưu ở `settings.json`; đổi ngôn ngữ dựng lại cửa sổ chính, cửa sổ con đang mở giữ ngôn ngữ cũ (⚠ As-is).
  2. `## Định dạng` — tiền: làm tròn số nguyên, vi `1.500.000 đ`, en `1,500,000 VND`; trục và nhãn cột biểu đồ luôn dùng dấu `,` (⚠ As-is); ngày `dd/MM/yyyy` cả hai ngôn ngữ; chi tiết giao dịch và "ngày xuất báo cáo" `dd/MM/yyyy HH:mm:ss`; tên file báo cáo `{report.file_prefix}_yyyyMMdd_HHmmss.docx`; parse tiền theo BR-10; nhãn danh mục theo BR-12.
  3. `## Bảng chuỗi` — dán nguyên output của script (111 dòng).
  4. `💡 Gợi ý Compose` — `values/strings.xml` (vi, mặc định) + `values-en/strings.xml`; tham số `{x}` → `%1$s` theo thứ tự xuất hiện (cột "Tham số"); nhãn danh mục dùng `when(key)` → `stringResource`, key lạ hiển thị nguyên văn; xuống dòng `<br>` trong bảng = `\n`.

Run: `.venv/Scripts/python.exe -I "$SP/gen_i18n_table.py" . > "$SP/i18n_table.md"` rồi chèn vào mục 3.

- [ ] **Step 3: Acceptance**

Run: `.venv/Scripts/python.exe -I "$SP/check_spec.py" . | grep i18n` → Expected: không có dòng nào.

---

### Task 5: `02-screens.md` + trang `navigation`, `wf-scr01..05`

**Files:**
- Create: `docs/android-spec/02-screens.md`
- Modify: `$SP/gen_diagrams.py`

**Nguồn:** `app/presentation/loading_window.py`, `main_window.py`, `transaction_form.py`, `transaction_detail.py`, `chart_view.py`, `charts.py`, `word_exporter.py`, `ui_helpers.py`.

Mỗi SCR có các mục: wireframe (ảnh), `### Thành phần` (bảng `# | Thành phần | Loại | Nhãn (key) | Mặc định / ghi chú`), `### Sự kiện` (bảng `# | Thao tác | Điều kiện | Kết quả / thông báo (key)`), `### Trạng thái`, thông tin cửa sổ (kích thước, modal), `💡 Gợi ý Compose`.

- [ ] **Step 1: Mục chung** — `## Sơ đồ điều hướng` (ảnh `navigation.png` + danh sách chuyển màn), `## Hộp thoại dùng chung`: lỗi (`dialog.error` + `error.*`), cảnh báo (`dialog.warning`), xác nhận Yes/No (`dialog.confirm`), thông báo (`dialog.success`), chọn file ảnh, lưu file. Bảng ánh xạ exception → key: `InvalidTransaction` → `error.invalid_transaction`; `NoDataError` → `error.no_data`; `FileNotFoundError`/`PermissionError` → `error.file`; còn lại → `error.generic` (`ui_helpers.py:708-723`).

- [ ] **Step 2: SCR-01 Loading** (400×150, giữa màn hình, không đổi kích thước, cửa sổ gốc). Thành phần: ① nhãn `loading.connecting`, ② progress bar chạy liên tục, ③ `loading.retry`, ④ `loading.exit` (③④ chỉ hiện khi lỗi). Sự kiện: mở app → kết nối ở thread nền, kiểm tra kết quả mỗi 100 ms; thành công → đóng, mở SCR-02; lỗi → dừng progress, nhãn đỏ `loading.error`, hiện ③④; ③ → ẩn nút, nhãn `loading.reconnecting`, kết nối lại; ④ hoặc đóng cửa sổ → thoát app, không mở SCR-02.

- [ ] **Step 3: SCR-02 Main** (900×600, cửa sổ gốc, tiêu đề `main.title`). Thành phần: menu `menu.language` (radio `language.vi`/`language.en`); thanh lọc `main.from` + ô ngày (mặc định ngày 1 tháng này), `main.to` + ô ngày (hôm nay), `main.filter`; bên phải `main.add` và `main.export_word`; khung `main.summary` với `summary.inflow` (xanh lá), `summary.outflow` (đỏ), `summary.balance` (đen), chữ đậm; bảng 5 cột `main.col_date` 100 trái, `main.col_type` 80, `main.col_category` 300, `main.col_amount` 120 phải, `main.col_note` 200, thanh cuộn dọc, dòng = một giao dịch, cột danh mục = `Nhãn (tiền), Nhãn (tiền)`; thanh dưới `main.view`, `main.edit`, `main.delete` (trái), `main.chart` (phải).
   Sự kiện (mỗi dòng một thao tác):
   - Mở màn: tải kỳ mặc định; lỗi → `error.generic` (hoặc `error.invalid_transaction` khi có document hỏng), bảng rỗng, tổng 0.
   - Chọn ngôn ngữ: lưu `settings.json` (lỗi → `error.file`/`error.generic`, giao diện vẫn đổi), dựng lại toàn bộ cửa sổ, hiển thị lại dữ liệu đã tải (không gọi Firestore), ô ngày quay về kỳ đang áp dụng (⚠ As-is: mất ngày đã gõ chưa bấm Lọc).
   - `main.filter`: ngày không hợp lệ → `error.invalid_date`; hợp lệ → tải lại theo BR-07.
   - `main.add`: mở SCR-03 chế độ thêm; lưu thành công → tải lại kỳ.
   - Click dòng: chọn dòng (⚠ As-is: cho chọn nhiều dòng bằng Ctrl/Shift nhưng thao tác chỉ dùng dòng đầu tiên; không có double-click).
   - `main.view` / `main.edit` / `main.delete` khi chưa chọn → cảnh báo `main.select_first`.
   - `main.view`: tìm file ảnh biên lai rồi mở SCR-04.
   - `main.edit`: mở SCR-03 chế độ sửa bằng dữ liệu đang hiển thị (⚠ As-is: không đọc lại Firestore).
   - `main.delete`: hỏi `main.confirm_delete`; Không → thôi; Có → xoá, `main.deleted`, tải lại; lỗi → `error.generic`, vẫn tải lại.
   - `main.chart`: mở SCR-05 với dữ liệu kỳ đang hiển thị; nếu lần tải đầu đã lỗi thì không làm gì (⚠ As-is).
   - `main.export_word`: hộp thoại lưu (`report.save_title`, thư mục Desktop, tên `report.file_prefix_yyyyMMdd_HHmmss.docx`, lọc `report.file_type` / `dialog.all_files`); huỷ → thôi; chọn → đọc lại kỳ từ Firestore; rỗng → `error.no_data`; ghi file lỗi → `error.file`; lỗi khác → `error.generic`; thành công → `report.exported`.
   - Đóng cửa sổ: thoát app.

- [ ] **Step 4: SCR-03 Form Thêm/Sửa** (600×700, cửa sổ con không khoá cửa sổ chính — ⚠ As-is: vẫn bấm được SCR-02 khi form mở; tiêu đề `form.title_add`/`form.title_edit`). Thành phần: ① `form.type_frame` radio `type_long.outflow` / `type_long.inflow` (mặc định Chi khi thêm); ② `form.general_frame`: `form.date` + ô ngày, `form.contact` + ô (rộng 20), `form.note` + ô (rộng 50); ③ `form.items_frame`: tiêu đề cột `form.col_category`/`form.col_amount`/`form.col_note`, mỗi dòng = combobox danh mục cho phép gõ + ô tiền + ô ghi chú + nút `X`, nút `form.add_item`; ④ `form.choose_receipt` + nhãn `form.no_receipt` hoặc tên file; ⑤ nhãn `form.total` (đậm) + nút `form.save_new`/`form.save_edit`. Khởi tạo: thêm → 1 dòng trống; sửa → điền ngày, đối tác, ghi chú, tên file ảnh, mỗi hạng mục một dòng (tiền hiển thị dạng `1.500.000 đ`).
   Sự kiện: đổi loại → nạp danh mục theo loại, mọi dòng đổi danh sách và **reset về danh mục đầu tiên** (⚠ As-is); lỗi nạp → `error.generic`, danh sách rỗng; chọn/gõ danh mục (BR-11); gõ tiền → `form.total` cập nhật mỗi phím (BR-10); `X` → xoá dòng, trừ khi chỉ còn 1 dòng (không báo gì); `form.add_item` → thêm dòng; `form.choose_receipt` → chọn ảnh (`form.image_files`: jpg, jpeg, png), huỷ thì giữ nguyên, chọn thì nhãn đổi thành tên file (chưa copy); Lưu → bỏ dòng tiền ≤ 0, ghép ngày (BR-09), kiểm tra BR-01/02 → `error.invalid_transaction`; copy ảnh (BR-13) lỗi → `error.file`; ghi Firestore lỗi → `error.generic`; thành công → `form.added`/`form.updated`, SCR-02 tải lại, form đóng; lỗi thì form giữ nguyên dữ liệu; đóng cửa sổ → bỏ thay đổi, không hỏi.

- [ ] **Step 5: SCR-04 Chi tiết** (500×600, modal). ① `detail.general`: `detail.type` (đậm), `detail.date` (`dd/MM/yyyy HH:mm:ss`), `detail.total` (xanh dương nếu Thu, đỏ nếu Chi, đậm), `detail.contact`, `detail.note`; ② `detail.items`: bảng 3 cột (`form.col_category` 120, `form.col_amount` 100 phải, `form.col_note` 200), cao 5 dòng; ③ `detail.receipt`: chỉ hiện khi file ảnh tồn tại, ảnh thu nhỏ tối đa 400×200, file hỏng → `detail.receipt_error`; ④ `dialog.close`. Sự kiện: ④ đóng.

- [ ] **Step 6: SCR-05 Biểu đồ** (1000×800, phóng to toàn màn hình trên Windows, modal). ① tiêu đề `chart.heading` (ngày bắt đầu/kết thúc kỳ); ② nếu cả hai loại đều không có dữ liệu → `chart.no_data_period`; ngược lại 2 biểu đồ cột xếp dọc: trên `chart.inflow_title` màu xanh lá, dưới `chart.outflow_title` màu đỏ; cột theo BR-06, nhãn trục X là nhãn danh mục xoay 45°, trục Y `chart.y_label`, số trên đỉnh cột, trần trục Y = max(giá trị lớn nhất × 1.2, 1); loại nào rỗng thì ô đó hiện `chart.no_data`; ③ `dialog.close`.

- [ ] **Step 7: `## Báo cáo Word`** — cấu trúc theo `word_exporter.py`: tiêu đề `report.title`; `report.period`; `report.exported_at`; mục `report.section_overview` (3 dòng đậm `summary.inflow`, `summary.outflow`, `report.balance`); mục `report.section_charts` (2 ảnh biểu đồ như SCR-05, rộng 6 inch); mục `report.section_details`: bảng có viền 5 cột `report.col_*`, sắp cũ nhất trước, ô hạng mục mỗi dòng `- <nhãn danh mục>[ report.item_purpose]: <tiền>`; ngôn ngữ = ngôn ngữ giao diện lúc xuất.

- [ ] **Step 8: Diagram** — `navigation` (các SCR là PROC, hộp thoại là ALT/ERROR, cạnh ghi tên nút); `wf-scr01..05`: vẽ đúng thứ tự widget theo `pack`/`grid` trong code, tỉ lệ 1:1 theo kích thước cửa sổ (SCR-05 vẽ 1000×800 thu nhỏ 0.6), mỗi thành phần có `callout` với số trùng cột `#`.

- [ ] **Step 9: Acceptance**

Run: `.venv/Scripts/python.exe -I "$SP/gen_diagrams.py" . --export`, Read 6 PNG (`navigation`, `wf-scr01..05`), so với code: thứ tự widget, nhãn, số callout.
Run: `.venv/Scripts/python.exe -I "$SP/check_spec.py" . | grep 02-screens` → Expected: không có dòng nào.
Đối chiếu tay: mỗi `command=`/`trace_add`/`filedialog`/`messagebox` trong 5 file presentation có đúng một dòng sự kiện.

---

### Task 6: `03-use-cases.md` + trang `use-cases`, `act-*`, `seq-*`

**Files:**
- Create: `docs/android-spec/03-use-cases.md`
- Modify: `$SP/gen_diagrams.py`

Mỗi UC là một mục `## UC-0n <tên>` gồm: tác nhân (Người dùng), màn hình, tiền điều kiện, kích hoạt, luồng chính (đánh số), luồng thay thế `A1..`, luồng lỗi `E1..` (ghi rõ key thông báo dạng `` `error.x` ``), hậu điều kiện, `### Tiêu chí nghiệm thu` (Given/When/Then), ảnh activity và sequence (nếu có). Mở đầu file: ảnh `use-cases.png` + bảng UC → SCR → diagram.

- [ ] **Step 1: UC-01 Khởi động & kết nối** — chính: mở app → SCR-01 → thread nền khởi tạo Firebase bằng service account (chỉ lần đầu) → nếu `categories` rỗng thì seed (BR-14) → tạo service → SCR-02 tải kỳ mặc định. E1 thiếu/hỏng key hoặc mất mạng → `loading.error`; A1 Thử lại; A2 Thoát. Sequence: UI thread, thread nền, `firebase_admin`, Firestore `categories`.
- [ ] **Step 2: UC-02 Xem/lọc theo kỳ** — chính: nhập 2 ngày → Lọc → truy vấn (BR-07) → tính tổng (BR-05) → hiển thị bảng + tổng quan. E1 ngày sai → `error.invalid_date`; E2 lỗi Firestore → `error.generic`; E3 document hỏng → `error.invalid_transaction`; A1 khoảng ngược → bảng rỗng. Sequence: MainWindow → TransactionService.load_period → Repository.list_between → Firestore → build_period_report.
- [ ] **Step 3: UC-03 Thêm giao dịch** — chính theo SCR-03; A1 đổi loại; A2 thêm/xoá dòng; A3 chọn ảnh; A4 danh mục tự gõ; A5 dòng tiền 0 bị bỏ; E1 `error.invalid_transaction`; E2 copy ảnh lỗi `error.file`; E3 ghi lỗi `error.generic`; E4 nạp danh mục lỗi.
- [ ] **Step 4: UC-04 Sửa giao dịch** — khác UC-03: tiền điều kiện có dòng được chọn (E0 `main.select_first`); điền sẵn; giữ giờ gốc; giữ ảnh cũ nếu không chọn mới; ghi `update` + `updated_at`; E5 document đã bị xoá ở máy khác → `error.generic`. Activity và sequence dùng chung trang `act-uc03-04` / `seq-uc03-04` (nhánh `id == null ?`).
- [ ] **Step 5: UC-05 Xem chi tiết** — E0 chưa chọn; A1 không có ảnh hoặc file không tồn tại → ẩn mục biên lai; E1 ảnh hỏng → `detail.receipt_error`. Sequence: MainWindow → TransactionService.resolve_receipt → LocalReceiptStorage → SCR-04.
- [ ] **Step 6: UC-06 Xoá** — E0 chưa chọn; A1 chọn Không; E1 lỗi xoá → `error.generic` (vẫn tải lại). Sequence có frame `alt`.
- [ ] **Step 7: UC-07 Biểu đồ** — A1 chưa tải được kỳ → không làm gì; A2 kỳ rỗng → `chart.no_data_period`; A3 một loại rỗng → `chart.no_data`. Không có sequence.
- [ ] **Step 8: UC-08 Xuất báo cáo** — A1 huỷ hộp thoại lưu; E1 `error.no_data`; E2 `error.file` (file đang mở trong Word); E3 `error.generic`. Sequence: MainWindow → ReportService.export → TransactionService.load_period → Firestore → WordReportExporter → file `.docx`.
- [ ] **Step 9: UC-09 Đổi ngôn ngữ** — chính: chọn ngôn ngữ → lưu `settings.json` → dựng lại SCR-02 → hiển thị lại từ dữ liệu đã tải. E1 ghi file lỗi → `error.file`, giao diện vẫn đổi nhưng lần sau mở lại về ngôn ngữ cũ. Không có sequence.
- [ ] **Step 10: Diagram** — `use-cases` (ACTOR + 9 USECASE, UC-04/05/06 ghi chú «cần chọn dòng»); `act-uc01..09` theo luồng ở trên, nhánh lỗi ERROR, nhánh thay thế ALT, mỗi hình thoi ghi điều kiện, mỗi cạnh ra ghi Có/Không; `seq-*` theo danh sách participant ở từng UC, nhánh dùng `("frame", "alt [điều kiện]", i, j)`.
- [ ] **Step 11: Acceptance**

Run: `.venv/Scripts/python.exe -I "$SP/gen_diagrams.py" . --export`, Read 16 PNG (`use-cases`, `act-*`, `seq-*`): chữ không chồng, mọi nhánh trong `.md` có trên hình.
Run: `.venv/Scripts/python.exe -I "$SP/check_spec.py" . | grep -E "UC-0|03-use-cases"` → Expected: không có dòng nào.

---

### Task 7: `05-android-mapping.md`, `README.md` + trang `architecture-android`, `architecture-current`

**Files:**
- Create: `docs/android-spec/05-android-mapping.md`, `docs/android-spec/README.md`
- Modify: `$SP/gen_diagrams.py`

- [ ] **Step 1: `05-android-mapping.md`** — nội dung mục 7 của spec: bảng `| **C1** |`…`| **C4** |` (C2 kèm đoạn Kotlin minh hoạ: ghi `Timestamp(ldt.toInstant(ZoneOffset.UTC))`, đọc `ts.toDate().toInstant().atOffset(ZoneOffset.UTC).toLocalDateTime()`, áp cho cả hai mốc truy vấn kỳ); bảng `| **D1** |`…`| **D5** |` gồm vấn đề, các lựa chọn, khuyến nghị, ảnh hưởng tới desktop; bảng ánh xạ desktop → Compose; ngoài phạm vi; ảnh `architecture-android.png`.
- [ ] **Step 2: `README.md`** — mục đích; phạm vi; thuật ngữ (giao dịch, hạng mục, kỳ, danh mục/key, biên lai, ⚠ As-is, 💡); kiến trúc hiện tại + ảnh `architecture-current.png` (bảng tầng → file); mục lục 5 file với một câu mô tả; thứ tự đọc 01 → 04 → 02 → 03 → 05; cách mở/sửa `diagrams/spec.drawio` và xuất lại PNG; ghi chú phiên bản nguồn (commit `5614abe`).
- [ ] **Step 3: Diagram** — `architecture-current`: 4 tầng (presentation, application, domain, infrastructure) + `container.py`, Firestore (DB), ổ đĩa (`assets/receipts`, `settings.json`, `locales/`) (FOLDER), file `.docx`; mũi tên phụ thuộc theo quy tắc trong spec cũ. `architecture-android`: Compose UI → ViewModel (StateFlow) → UseCase → Repository → Firestore client SDK + Firebase Auth / DataStore (ngôn ngữ) / bộ nhớ trong (ảnh) / PDF qua SAF; chú thích C1, C2.
- [ ] **Step 4: Acceptance**

Run: `.venv/Scripts/python.exe -I "$SP/gen_diagrams.py" . --export`, Read 2 PNG.
Run: `.venv/Scripts/python.exe -I "$SP/check_spec.py" .` → Expected: `OK`.

---

### Task 8: Kiểm tra tổng thể

- [ ] **Step 1:** Xoá PNG cũ rồi xuất lại toàn bộ: `rm -f docs/android-spec/diagrams/png/*.png && .venv/Scripts/python.exe -I "$SP/gen_diagrams.py" . --export` → Expected: `24 trang -> ...`.
- [ ] **Step 2:** `.venv/Scripts/python.exe -I "$SP/check_spec.py" .` → Expected: `OK`, exit 0.
- [ ] **Step 3:** Mở `spec.drawio` bằng draw.io CLI xuất thử PDF tất cả trang (`draw.io.exe -x -f pdf -a -o "$SP/all.pdf" docs/android-spec/diagrams/spec.drawio`) để chắc file hợp lệ; Read vài trang.
- [ ] **Step 4:** Đọc lại lần lượt 5 file `app/presentation/*.py` có UI, tích từng handler với bảng sự kiện (tiêu chí 1); đọc `transaction_service.py`, `report_service.py`, `ui_helpers.py`, tích từng nhánh lỗi với A*/E* (tiêu chí 3).
- [ ] **Step 5:** `git status --short` → chỉ có file mới dưới `docs/android-spec/` và `docs/plans/2026-11-04-android-spec.md` (cộng `.gitignore` đã sửa từ trước); không có file nào trong `app/`, `locales/`, `scripts/`, `tests/`.

Sau Task 8: verification-before-completion; đề nghị review độc lập (khuyến nghị cho T3); hỏi người dùng có commit không.
