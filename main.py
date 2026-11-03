import tkinter as tk
from tkinter import ttk
import threading
from database.db_manager import DBManager
from services.report_service import ReportService
from views.main_window import MainWindow

def main():
    loading_root = tk.Tk()
    loading_root.title("Khởi động ứng dụng")
    loading_root.geometry("400x150")
    # Center the window on screen
    loading_root.eval('tk::PlaceWindow . center')
    loading_root.resizable(False, False)
    
    lbl = ttk.Label(loading_root, text="Đang kết nối đến cơ sở dữ liệu...", font=("Arial", 11))
    lbl.pack(expand=True, pady=(20, 5))
    
    progress = ttk.Progressbar(loading_root, mode='indeterminate')
    progress.pack(fill=tk.X, padx=30, pady=(0, 20))
    progress.start()

    app_data = {}

    def init_db():
        try:
            db_manager = DBManager()
            report_service = ReportService(db_manager)
            app_data['db_manager'] = db_manager
            app_data['report_service'] = report_service
            loading_root.after(0, loading_root.destroy)
        except Exception as e:
            app_data['error'] = str(e)
            loading_root.after(0, on_error)

    def on_error():
        progress.stop()
        lbl.config(text="Lỗi kết nối CSDL!\nVui lòng kiểm tra lại kết nối mạng hoặc MongoDB.", foreground="red")
        
        btn_frame = ttk.Frame(loading_root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Thử lại", command=retry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Thoát", command=loading_root.destroy).pack(side=tk.LEFT, padx=5)

    def retry():
        for widget in loading_root.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.destroy()
        
        lbl.config(text="Đang kết nối lại...", foreground="black")
        progress.start()
        threading.Thread(target=init_db, daemon=True).start()

    threading.Thread(target=init_db, daemon=True).start()
    loading_root.mainloop()

    if 'db_manager' in app_data and 'report_service' in app_data:
        app = MainWindow(app_data['db_manager'], app_data['report_service'])
        app.mainloop()

if __name__ == "__main__":
    main()
