
import pytest

from speechtools.views import ResultsView

def test_results_view(qtbot):
    w = ResultsView()
    qtbot.addWidget(w)
