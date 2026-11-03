import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from utils.helpers import format_currency

class TransactionDetail(tk.Toplevel):
    def __init__(self, parent, transaction):
        super().__init__(parent)
        self.title("Chi Tiết Giao Dịch")
        self.geometry("500x600")
        self.transaction = transaction
        
        self._build_ui()
        
    def _build_ui(self):
        # General Info Frame
        info_frame = ttk.LabelFrame(self, text="Thông tin chung")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        t_type_str = "Khoản Thu" if self.transaction.get("type") == "inflow" else "Khoản Chi"
        date_str = self.transaction.get("date").strftime("%d/%m/%Y %H:%M:%S") if self.transaction.get("date") else ""
        amount_str = format_currency(self.transaction.get("total_amount", 0))
        contact = self.transaction.get("contact_person", "")
        note = self.transaction.get("general_note", "")
        
        ttk.Label(info_frame, text=f"Loại giao dịch: {t_type_str}", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(info_frame, text=f"Ngày giờ: {date_str}").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(info_frame, text=f"Tổng số tiền: {amount_str}", foreground="blue" if self.transaction.get("type") == "inflow" else "red", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(info_frame, text=f"Đối tác: {contact}").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(info_frame, text=f"Ghi chú chung: {note}").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Items Frame
        items_frame = ttk.LabelFrame(self, text="Hạng mục chi tiết")
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("category", "amount", "note")
        tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=5)
        tree.heading("category", text="Danh mục")
        tree.heading("amount", text="Số tiền")
        tree.heading("note", text="Ghi chú")
        
        tree.column("category", width=120)
        tree.column("amount", width=100, anchor=tk.E)
        tree.column("note", width=200)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for item in self.transaction.get("items", []):
            tree.insert("", tk.END, values=(
                item.get("category_name", ""),
                format_currency(item.get("amount", 0)),
                item.get("item_note", "")
            ))
            
        # Image Frame
        img_path = self.transaction.get("image_path", "")
        if img_path and os.path.exists(img_path):
            img_frame = ttk.LabelFrame(self, text="Biên lai")
            img_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            try:
                img = Image.open(img_path)
                img.thumbnail((400, 200))
                photo = ImageTk.PhotoImage(img)
                lbl_img = ttk.Label(img_frame, image=photo)
                lbl_img.image = photo # keep reference
                lbl_img.pack(padx=5, pady=5)
            except Exception as e:
                ttk.Label(img_frame, text="Không thể tải ảnh biên lai").pack(padx=5, pady=5)
        
        # Close Button
        ttk.Button(self, text="Đóng", command=self.destroy).pack(pady=10)
