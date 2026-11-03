import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import matplotlib.ticker as ticker

class ChartView(tk.Toplevel):
    def __init__(self, parent, inflow_data, outflow_data, start_date, end_date):
        super().__init__(parent)
        self.title("Biểu đồ Thu/Chi")
        self.geometry("1000x800")
        try:
            self.state("zoomed")
        except:
            pass
            
        self.inflow_data = inflow_data
        self.outflow_data = outflow_data
        self.start_date = start_date
        self.end_date = end_date
        
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()

    def _build_ui(self):
        lbl_title = ttk.Label(self, text=f"Thống kê giao dịch từ {self.start_date.strftime('%d/%m/%Y')} đến {self.end_date.strftime('%d/%m/%Y')}", font=("Arial", 14, "bold"))
        lbl_title.pack(pady=10)

        if not self.inflow_data and not self.outflow_data:
            ttk.Label(self, text="Không có dữ liệu trong khoảng thời gian này.", font=("Arial", 12)).pack(pady=20)
            btn_close = ttk.Button(self, text="Đóng", command=self.destroy)
            btn_close.pack(pady=10)
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.tight_layout(pad=5.0, h_pad=6.0)

        self._plot_bar(ax1, self.inflow_data, "Tổng Thu Theo Hạng Mục", "green")
        self._plot_bar(ax2, self.outflow_data, "Tổng Chi Theo Hạng Mục", "red")

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        btn_close = ttk.Button(self, text="Đóng", command=self.destroy)
        btn_close.pack(pady=10)

    def _plot_bar(self, ax, data, title, color):
        if not data:
            ax.set_title(title)
            ax.text(0.5, 0.5, "Không có dữ liệu", ha='center', va='center')
            ax.axis('off')
            return

        labels = [item['_id'] for item in data]
        values = [item['total'] for item in data]

        bars = ax.bar(labels, values, color=color)
        ax.set_title(title)
        ax.set_ylabel("Số tiền (VND)")
        
        # Thêm không gian phía trên để text không bị cắt
        max_val = max(values) if values else 0
        ax.set_ylim(0, max_val * 1.2)
        
        # Định dạng trục Y hiển thị đầy đủ số
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
        ax.tick_params(axis='x', rotation=45)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), 
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
