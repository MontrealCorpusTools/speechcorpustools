
import pytest

from speechtools.gui.views import ResultsView

def test_results_view(qtbot):
    w = ResultsView()
    qtbot.addWidget(w)
