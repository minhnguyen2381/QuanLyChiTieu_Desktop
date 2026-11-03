"""Cửa sổ biểu đồ thu/chi theo danh mục cho kỳ đang xem."""
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.domain.summary import PeriodReport
from app.presentation.charts import plot_category_bars
from app.presentation.formatters import format_date
from app.presentation.i18n import t


class ChartView(tk.Toplevel):
    def __init__(self, parent, report: PeriodReport):
        super().__init__(parent)
        self.title(t("chart.window_title"))
        self.geometry("1000x800")
        try:
            self.state("zoomed")
        except tk.TclError:
            pass  # 'zoomed' chỉ có trên Windows
        self.transient(parent)
        self.grab_set()

        heading = t("chart.heading", start=format_date(report.start), end=format_date(report.end))
        ttk.Label(self, text=heading, font=("Arial", 14, "bold")).pack(pady=10)
        if report.inflow_by_category or report.outflow_by_category:
            self._draw(report)
        else:
            ttk.Label(self, text=t("chart.no_data_period"), font=("Arial", 12)).pack(pady=20)
        ttk.Button(self, text=t("dialog.close"), command=self.destroy).pack(pady=10)

    def _draw(self, report: PeriodReport):
        figure = Figure(figsize=(10, 8))
        inflow_axes, outflow_axes = figure.subplots(2, 1)
        plot_category_bars(inflow_axes, report.inflow_by_category, t("chart.inflow_title"), "green")
        plot_category_bars(outflow_axes, report.outflow_by_category, t("chart.outflow_title"), "red")
        figure.tight_layout(pad=5.0, h_pad=6.0)
        canvas = FigureCanvasTkAgg(figure, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
