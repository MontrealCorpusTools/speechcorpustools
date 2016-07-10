
import pytest

from speechtools.widgets.query.main import QueryWidget, QueryForm, QueryResults

from speechtools.widgets.query.basic import ValueWidget

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


def test_value_widget(acoustic_config, qtbot):
    w = ValueWidget(acoustic_config, 'word')
    qtbot.addWidget(w)
    w.changeType('word', 'label', str)

    w.compWidget.setCurrentIndex(2)
    assert(w.mainLayout.itemAt(1).widget().text() == '')

    assert(w.operator() == 'regex')
    assert(w.value() == '')




