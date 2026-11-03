import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from tkcalendar import DateEntry
from datetime import datetime
from utils.helpers import format_currency
from views.transaction_form import TransactionForm
from views.transaction_detail import TransactionDetail
from views.chart_view import ChartView

class MainWindow(tk.Tk):
    def __init__(self, db_manager, report_service):
        super().__init__()
        self.title("Phần mềm Quản lý Chi tiêu")
        self.geometry("900x600")
        self.db_manager = db_manager
        self.report_service = report_service
        
        self.start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        self.end_date = datetime.now().replace(hour=23, minute=59, second=59)
        
        self._build_ui()
        self.refresh_data()
        
    def _build_ui(self):
        # Top Frame for Filters
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Từ ngày:").pack(side=tk.LEFT, padx=5)
        self.date_from = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_from.set_date(self.start_date)
        self.date_from.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="Đến ngày:").pack(side=tk.LEFT, padx=5)
        self.date_to = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_to.set_date(self.end_date)
        self.date_to.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Lọc", command=self._apply_filter).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(filter_frame, text="Xuất Báo Cáo Word", command=self._export_report).pack(side=tk.RIGHT, padx=5)
        ttk.Button(filter_frame, text="+ Thêm Giao Dịch", command=self._open_add_form).pack(side=tk.RIGHT, padx=5)
        
        # Summary Frame
        summary_frame = ttk.LabelFrame(self, text="Tổng quan trong kỳ")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_inflow = ttk.Label(summary_frame, text="Tổng Thu: 0 đ", foreground="green", font=("Arial", 11, "bold"))
        self.lbl_inflow.pack(side=tk.LEFT, expand=True)
        
        self.lbl_outflow = ttk.Label(summary_frame, text="Tổng Chi: 0 đ", foreground="red", font=("Arial", 11, "bold"))
        self.lbl_outflow.pack(side=tk.LEFT, expand=True)
        
        self.lbl_balance = ttk.Label(summary_frame, text="Số Dư: 0 đ", font=("Arial", 11, "bold"))
        self.lbl_balance.pack(side=tk.LEFT, expand=True)
        
        # Treeview Frame
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("date", "type", "category", "amount", "note")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.tree.heading("date", text="Ngày")
        self.tree.heading("type", text="Loại")
        self.tree.heading("category", text="Danh mục chi tiết")
        self.tree.heading("amount", text="Tổng số tiền")
        self.tree.heading("note", text="Ghi chú chung")
        
        self.tree.column("date", width=100)
        self.tree.column("type", width=80)
        self.tree.column("category", width=300)
        self.tree.column("amount", width=120, anchor=tk.E)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action Frame
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Xem chi tiết", command=self._view_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Sửa", command=self._edit_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Xóa", command=self._delete_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Xem Biểu Đồ Chi Tiêu", command=self._view_chart).pack(side=tk.RIGHT, padx=5)
        
    def _apply_filter(self):
        try:
            d_from = self.date_from.get_date()
            d_to = self.date_to.get_date()
            self.start_date = datetime(d_from.year, d_from.month, d_from.day, 0, 0, 0)
            self.end_date = datetime(d_to.year, d_to.month, d_to.day, 23, 59, 59)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ.")

    def refresh_data(self):
        summary = self.db_manager.get_summary_by_date_range(self.start_date, self.end_date)
        self.lbl_inflow.config(text=f"Tổng Thu: {format_currency(summary['inflow'])}")
        self.lbl_outflow.config(text=f"Tổng Chi: {format_currency(summary['outflow'])}")
        self.lbl_balance.config(text=f"Số Dư: {format_currency(summary['balance'])}")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        transactions = self.db_manager.get_transactions(start_date=self.start_date, end_date=self.end_date)
        
        for t in transactions:
            date_str = t["date"].strftime("%d/%m/%Y")
            t_type = "Thu" if t["type"] == "inflow" else "Chi"
            amount_str = format_currency(t["total_amount"])
            
            items = t.get("items", [])
            cats_str = ", ".join([f"{item['category_name']} ({format_currency(item['amount'])})" for item in items])
            
            self.tree.insert("", tk.END, iid=str(t["_id"]), values=(
                date_str, 
                t_type, 
                cats_str, 
                amount_str, 
                t.get("general_note", "")
            ))

    def _open_add_form(self):
        form = TransactionForm(self, self.db_manager, on_save_callback=self.refresh_data)
        self.wait_window(form)
        
    def _export_report(self):
        if self.report_service:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            default_filename = f"BaoCaoChiTieu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            filepath = filedialog.asksaveasfilename(
                initialdir=desktop_path,
                initialfile=default_filename,
                defaultextension=".docx",
                filetypes=[("Word Document", "*.docx"), ("All files", "*.*")],
                title="Chọn vị trí lưu báo cáo"
            )
            
            if not filepath:
                return  # Người dùng hủy lưu
                
            path = self.report_service.export_to_word(self.start_date, self.end_date, export_path=filepath)
            if path:
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo tại:\n{path}")
            else:
                messagebox.showerror("Lỗi", "Không có dữ liệu hoặc xuất báo cáo thất bại.")

    def _get_selected_transaction_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một giao dịch.")
            return None
        return selected[0]

    def _view_transaction(self):
        t_id = self._get_selected_transaction_id()
        if t_id:
            txn = self.db_manager.get_transaction_by_id(t_id)
            if txn:
                detail_win = TransactionDetail(self, txn)
                detail_win.grab_set()

    def _edit_transaction(self):
        t_id = self._get_selected_transaction_id()
        if t_id:
            form = TransactionForm(self, self.db_manager, on_save_callback=self.refresh_data, transaction_id=t_id)
            self.wait_window(form)

    def _delete_transaction(self):
        t_id = self._get_selected_transaction_id()
        if t_id:
            if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa giao dịch này?"):
                self.db_manager.delete_transaction(t_id)
                messagebox.showinfo("Thành công", "Đã xóa giao dịch.")
                self.refresh_data()
    def _view_chart(self):
        inflow_data = self.db_manager.get_summary_by_category(self.start_date, self.end_date, "inflow")
        outflow_data = self.db_manager.get_summary_by_category(self.start_date, self.end_date, "outflow")
        chart_win = ChartView(self, inflow_data, outflow_data, self.start_date, self.end_date)
        chart_win.grab_set()
