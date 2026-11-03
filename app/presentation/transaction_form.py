"""Form thêm/sửa giao dịch gồm nhiều hạng mục."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.application.transaction_service import TransactionService
from app.domain.categories import legacy_name_to_key
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
            self._key_by_label[category_label(item.category_key)] = item.category_key
            row.category.set(category_label(item.category_key))
            row.amount.set(format_money(item.amount))
            row.note.insert(0, item.note)

    # ---------- danh mục ----------

    def _category_labels(self) -> list[str]:
        keys: list[str] = []
        with reported_errors(self):
            keys = self._service.category_keys(TransactionType(self._type.get()))
        labels = {category_label(key): key for key in keys}
        self._key_by_label.update(labels)
        return list(labels)

    def _category_key(self, label: str) -> str:
        """Label đang hiển thị -> key; tên tiếng Việt cũ -> key của nó; chuỗi khác dùng làm key luôn."""
        label = label.strip()
        if not label:
            return ""  # domain sẽ báo thiếu danh mục
        return self._key_by_label.get(label) or legacy_name_to_key(label)

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
