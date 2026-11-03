import os
from docx import Document
from docx.shared import Inches
from datetime import datetime
from utils.helpers import format_currency
from config import BASE_DIR
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class ReportService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def export_to_word(self, start_date, end_date, export_path=None):
        """Xuất báo cáo tra soát giao dịch ra file Word có kèm biểu đồ."""
        transactions = self.db_manager.get_transactions(start_date=start_date, end_date=end_date, sort_by="date", direction=1)
        
        if not transactions:
            return None
            
        summary = self.db_manager.get_summary_by_date_range(start_date, end_date)
        inflow_data = self.db_manager.get_summary_by_category(start_date, end_date, "inflow")
        outflow_data = self.db_manager.get_summary_by_category(start_date, end_date, "outflow")
        
        doc = Document()
        doc.add_heading("BÁO CÁO QUẢN LÝ CHI TIÊU", 0)
        
        period_str = f"Từ ngày: {start_date.strftime('%d/%m/%Y')} - Đến ngày: {end_date.strftime('%d/%m/%Y')}"
        doc.add_paragraph(period_str)
        doc.add_paragraph(f"Ngày xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Summary
        doc.add_heading("1. Tổng quan", level=1)
        p = doc.add_paragraph()
        p.add_run(f"Tổng Thu: {format_currency(summary['inflow'])}\n").bold = True
        p.add_run(f"Tổng Chi: {format_currency(summary['outflow'])}\n").bold = True
        p.add_run(f"Số dư trong kỳ: {format_currency(summary['balance'])}").bold = True
        
        # Charts
        doc.add_heading("2. Biểu đồ thống kê", level=1)
        reports_dir = os.path.join(BASE_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        chart_inflow_path = os.path.join(reports_dir, f"temp_inflow_{ts}.png")
        chart_outflow_path = os.path.join(reports_dir, f"temp_outflow_{ts}.png")
        
        self._generate_chart_image(inflow_data, chart_inflow_path, "Tổng Thu Theo Hạng Mục", "green")
        doc.add_picture(chart_inflow_path, width=Inches(6.0))
        
        self._generate_chart_image(outflow_data, chart_outflow_path, "Tổng Chi Theo Hạng Mục", "red")
        doc.add_picture(chart_outflow_path, width=Inches(6.0))
        
        # Detail Table
        doc.add_heading("3. Bảng kê chi tiết", level=1)
        
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Ngày'
        hdr_cells[1].text = 'Loại'
        hdr_cells[2].text = 'Hạng mục chi tiết'
        hdr_cells[3].text = 'Tổng tiền'
        hdr_cells[4].text = 'Ghi chú chung'
        
        for t in transactions:
            row_cells = table.add_row().cells
            row_cells[0].text = t["date"].strftime("%d/%m/%Y")
            row_cells[1].text = "Thu" if t["type"] == "inflow" else "Chi"
            
            items = t.get("items", [])
            cats_list = []
            for item in items:
                purpose = item.get('item_note', '')
                purpose_str = f" (Mục đích: {purpose})" if purpose else ""
                cats_list.append(f"- {item['category_name']}{purpose_str}: {format_currency(item['amount'])}")
            
            row_cells[2].text = "\n".join(cats_list)
            row_cells[3].text = format_currency(t["total_amount"])
            row_cells[4].text = t.get("general_note", "")
            
        if export_path is None:
            filename = f"BaoCaoChiTieu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            filepath = os.path.join(reports_dir, filename)
        else:
            filepath = export_path
            
        doc.save(filepath)
        
        # Cleanup temp chart image
        if os.path.exists(chart_inflow_path):
            os.remove(chart_inflow_path)
        if os.path.exists(chart_outflow_path):
            os.remove(chart_outflow_path)
            
        return filepath

    def _generate_chart_image(self, data, save_path, title, color):
        import matplotlib.ticker as ticker
        fig, ax = plt.subplots(figsize=(8, 5))
        
        self._plot_bar(ax, data, title, color)
        
        fig.tight_layout()
        fig.savefig(save_path, bbox_inches='tight')
        plt.close(fig)

    def _plot_bar(self, ax, data, title, color):
        import matplotlib.ticker as ticker
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
        
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
        ax.tick_params(axis='x', rotation=45)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), 
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
