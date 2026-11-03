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
