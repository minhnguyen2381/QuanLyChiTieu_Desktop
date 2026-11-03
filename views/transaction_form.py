import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from PIL import Image, ImageTk
import os
from utils.helpers import format_currency, parse_currency_to_float, save_receipt_image

class TransactionForm(tk.Toplevel):
    def __init__(self, parent, db_manager, on_save_callback, transaction_id=None):
        super().__init__(parent)
        self.transaction_id = transaction_id
        if self.transaction_id:
            self.title("Sửa Giao Dịch")
        else:
            self.title("Thêm Giao Dịch Mới")
        self.geometry("600x700")
        self.db_manager = db_manager
        self.on_save_callback = on_save_callback
        
        self.transaction_type = tk.StringVar(value="outflow")
        self.items = [] # list to hold references to dynamic row widgets
        self.image_path = None
        
        self._build_ui()
        
        if self.transaction_id:
            self._load_transaction_data()
        
    def _build_ui(self):
        # Type selection
        type_frame = ttk.LabelFrame(self, text="Loại giao dịch")
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(type_frame, text="Khoản Chi (Outflow)", variable=self.transaction_type, value="outflow", command=self._refresh_categories).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="Khoản Thu (Inflow)", variable=self.transaction_type, value="inflow", command=self._refresh_categories).pack(side=tk.LEFT, padx=10)
        
        # General Info
        general_frame = ttk.LabelFrame(self, text="Thông tin chung")
        general_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(general_frame, text="Ngày giờ:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.date_entry = DateEntry(general_frame, width=15, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(general_frame, text="Đối tác (Payee):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.contact_entry = ttk.Entry(general_frame, width=20)
        self.contact_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(general_frame, text="Ghi chú chung:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.note_entry = ttk.Entry(general_frame, width=50)
        self.note_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Items Frame (Split Transactions)
        self.items_frame = ttk.LabelFrame(self, text="Chi tiết hạng mục")
        self.items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.items_inner_frame = ttk.Frame(self.items_frame)
        self.items_inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(self.items_frame, text="+ Thêm hạng mục", command=self._add_item_row).pack(anchor=tk.E, padx=5, pady=5)
        
        # Receipt Image
        receipt_frame = ttk.Frame(self)
        receipt_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(receipt_frame, text="Chọn ảnh biên lai", command=self._choose_image).pack(side=tk.LEFT)
        self.lbl_image_path = ttk.Label(receipt_frame, text="Chưa chọn ảnh")
        self.lbl_image_path.pack(side=tk.LEFT, padx=10)
        
        # Total and Save
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.lbl_total = ttk.Label(bottom_frame, text="Tổng cộng: 0 đ", font=("Arial", 12, "bold"))
        self.lbl_total.pack(side=tk.LEFT)
        
        btn_text = "Lưu Thay Đổi" if getattr(self, 'transaction_id', None) else "Xác Nhận"
        ttk.Button(bottom_frame, text=btn_text, command=self._save_transaction).pack(side=tk.RIGHT)
        
        # Add initial row
        self._add_item_row()
        
    def _refresh_categories(self):
        cats = self.db_manager.get_categories(self.transaction_type.get())
        for item in self.items:
            item['category_cb']['values'] = cats
            if cats:
                item['category_cb'].set(cats[0])

    def _add_item_row(self):
        row_frame = ttk.Frame(self.items_inner_frame)
        row_frame.pack(fill=tk.X, pady=2)
        
        cats = self.db_manager.get_categories(self.transaction_type.get())
        
        cb_cat = ttk.Combobox(row_frame, values=cats, width=15)
        if cats:
            cb_cat.set(cats[0])
        cb_cat.pack(side=tk.LEFT, padx=2)
        
        amount_var = tk.StringVar()
        amount_var.trace_add("write", lambda *args: self._update_total())
        ent_amount = ttk.Entry(row_frame, textvariable=amount_var, width=15)
        ent_amount.pack(side=tk.LEFT, padx=2)
        
        ent_note = ttk.Entry(row_frame, width=20)
        ent_note.insert(0, "Ghi chú...")
        ent_note.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        btn_remove = ttk.Button(row_frame, text="X", width=2, command=lambda f=row_frame: self._remove_item_row(f))
        btn_remove.pack(side=tk.LEFT, padx=2)
        
        self.items.append({
            'frame': row_frame,
            'category_cb': cb_cat,
            'amount_var': amount_var,
            'note_entry': ent_note
        })
        self._update_total()
        
    def _remove_item_row(self, frame):
        if len(self.items) <= 1:
            return # Keep at least one
        frame.destroy()
        self.items = [i for i in self.items if i['frame'] != frame]
        self._update_total()
        
    def _update_total(self):
        total = 0.0
        for item in self.items:
            val = parse_currency_to_float(item['amount_var'].get())
            total += val
        self.lbl_total.config(text=f"Tổng cộng: {format_currency(total)}")
        
    def _choose_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.image_path = file_path
            self.lbl_image_path.config(text=os.path.basename(file_path))

    def _load_transaction_data(self):
        txn = self.db_manager.get_transaction_by_id(self.transaction_id)
        if not txn:
            messagebox.showerror("Lỗi", "Không tìm thấy giao dịch.")
            self.destroy()
            return
            
        self.transaction_type.set(txn.get("type", "outflow"))
        self._refresh_categories()
        
        if txn.get("date"):
            self.date_entry.set_date(txn["date"])
            
        self.contact_entry.delete(0, tk.END)
        self.contact_entry.insert(0, txn.get("contact_person", ""))
        
        self.note_entry.delete(0, tk.END)
        self.note_entry.insert(0, txn.get("general_note", ""))
        
        if txn.get("image_path") and os.path.exists(txn.get("image_path")):
            self.image_path = txn["image_path"]
            self.lbl_image_path.config(text=os.path.basename(self.image_path))
            
        items_data = txn.get("items", [])
        for i, it_data in enumerate(items_data):
            if i > 0:
                self._add_item_row()
            current_item = self.items[i]
            
            # Use specific amount directly to format correctly (assuming stored as float without commas)
            amount_str = str(int(it_data.get("amount", 0))) if it_data.get("amount", 0) == int(it_data.get("amount", 0)) else str(it_data.get("amount", 0))
            current_item['amount_var'].set(amount_str)
            
            if it_data.get("category_name"):
                current_item['category_cb'].set(it_data.get("category_name"))
                
            ent_note = current_item['note_entry']
            ent_note.delete(0, tk.END)
            ent_note.insert(0, it_data.get("item_note", ""))

    def _save_transaction(self):
        total = 0.0
        item_data = []
        for item in self.items:
            val = parse_currency_to_float(item['amount_var'].get())
            if val <= 0:
                continue
            cat = item['category_cb'].get()
            note = item['note_entry'].get()
            if note == "Ghi chú...": note = ""
            
            total += val
            item_data.append({
                "category_name": cat,
                "amount": val,
                "item_note": note
            })
            
        if not item_data:
            messagebox.showerror("Lỗi", "Vui lòng nhập số tiền hợp lệ cho ít nhất 1 hạng mục.")
            return
            
        # Parse date
        try:
            dt = datetime.strptime(self.date_entry.get(), "%d/%m/%Y")
            now = datetime.now()
            dt = dt.replace(hour=now.hour, minute=now.minute, second=now.second)
        except Exception:
            dt = datetime.now()
            
        saved_img_path = self.image_path or ""
        if self.image_path and not self.image_path.startswith("assets"):
            # Only save if it's a newly picked image (outside assets folder)
            try:
                saved_img_path = save_receipt_image(self.image_path)
            except Exception as e:
                print(f"Error saving image: {e}")
            
        if self.transaction_id:
            self.db_manager.update_transaction(
                self.transaction_id,
                t_type=self.transaction_type.get(),
                total_amount=total,
                items=item_data,
                date=dt,
                general_note=self.note_entry.get(),
                image_path=saved_img_path,
                contact_person=self.contact_entry.get()
            )
            messagebox.showinfo("Thành công", "Đã cập nhật giao dịch!")
        else:
            self.db_manager.add_transaction(
                t_type=self.transaction_type.get(),
                total_amount=total,
                items=item_data,
                date=dt,
                general_note=self.note_entry.get(),
                image_path=saved_img_path,
                contact_person=self.contact_entry.get()
            )
            messagebox.showinfo("Thành công", "Đã thêm giao dịch!")
            
        if self.on_save_callback:
            self.on_save_callback()
        self.destroy()

