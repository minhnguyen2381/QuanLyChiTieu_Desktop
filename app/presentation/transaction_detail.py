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
