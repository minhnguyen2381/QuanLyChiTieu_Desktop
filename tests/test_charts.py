import unittest
import warnings

from matplotlib.figure import Figure

from app.domain.summary import CategoryTotal
from app.presentation.charts import plot_category_bars
from app.presentation.i18n import set_language, t


class PlotCategoryBarsTest(unittest.TestCase):
    def setUp(self):
        set_language("vi", persist=False)

    def test_draws_one_bar_per_category_with_translated_labels(self):
        axes = Figure().subplots()
        plot_category_bars(axes, [CategoryTotal("food", 300.0), CategoryTotal("Cà phê", 100.0)], "T", "red")
        axes.figure.draw_without_rendering()  # tick label của trục phân loại chỉ có sau khi vẽ
        self.assertEqual(len(axes.patches), 2)
        self.assertEqual(axes.get_title(), "T")
        self.assertEqual([label.get_text() for label in axes.get_xticklabels()], ["Ăn uống", "Cà phê"])

    def test_all_zero_totals_render_without_warnings(self):
        axes = Figure().subplots()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            plot_category_bars(axes, [CategoryTotal("food", 0.0)], "T", "red")
        self.assertGreater(axes.get_ylim()[1], 0)

    def test_empty_totals_show_no_data(self):
        axes = Figure().subplots()
        plot_category_bars(axes, [], "T", "red")
        self.assertFalse(axes.axison)
        self.assertEqual(axes.texts[0].get_text(), t("chart.no_data"))


if __name__ == "__main__":
    unittest.main()
