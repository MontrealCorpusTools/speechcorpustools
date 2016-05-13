
import pytest

from speechtools.widgets.query.main import QueryWidget, QueryForm, QueryResults


def test_query_widget(qtbot):
    w = QueryWidget()
    qtbot.addWidget(w)

def test_query_form(qtbot):
    w = QueryForm()
    qtbot.addWidget(w)

@pytest.mark.xfail
def test_query_results(qtbot):
    w = QueryResults()
    qtbot.addWidget(w)




