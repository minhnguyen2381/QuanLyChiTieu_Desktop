"""Biểu đồ cột tổng tiền theo danh mục — dùng chung cho cửa sổ biểu đồ và báo cáo Word."""
from matplotlib import ticker

from app.domain.summary import CategoryTotal
from app.presentation.formatters import category_label
from app.presentation.i18n import t


def plot_category_bars(axes, totals: list[CategoryTotal], title: str, color: str) -> None:
    axes.set_title(title)
    if not totals:
        axes.text(0.5, 0.5, t("chart.no_data"), ha="center", va="center")
        axes.axis("off")
        return

    values = [category.total for category in totals]
    bars = axes.bar([category_label(category.category_key) for category in totals], values, color=color)
    axes.set_ylabel(t("chart.y_label"))
    axes.set_ylim(0, max(max(values) * 1.2, 1))  # chừa chỗ cho nhãn số; >= 1 khi mọi cột bằng 0
    axes.yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, _: f"{int(value):,}"))
    axes.tick_params(axis="x", rotation=45)
    for bar in bars:
        height = bar.get_height()
        axes.annotate(f"{height:,.0f}", xy=(bar.get_x() + bar.get_width() / 2, height),
                      xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
