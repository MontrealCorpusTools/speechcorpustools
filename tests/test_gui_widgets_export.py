import pytest
from PyQt5 import QtCore
from speechtools.widgets.query.export import BasicColumnBox, ColumnWidget, ExportProfileDialog
from polyglotdb import CorpusContext
import collections

def test_export_basiccolumnbox(acoustic_config, qtbot):
    w = ExportProfileDialog(acoustic_config, 'phone', None)
    w.show()
    qtbot.addWidget(w)
    widget = w.BasicColumnBox.grid.itemAt(2).widget()
    qtbot.addWidget(widget)
    widget2 = w.BasicColumnBox.grid.itemAt(7).widget()
    qtbot.addWidget(widget2)
    widget.setChecked(True)
    widget2.setChecked(True)
    print (w.columnWidget.columns())
    assert w.columnWidget.columns()[0].attribute == ('phone','end')
    #assert w.columnWidget.columns()[1].attribute == ('phone', 'word', 'end')
    widget2.setChecked(False)
    #print (w.columnWidget.columns()[1].attribute)
    #assert w.columnWidget.columns()[0].attribute == ('phone','end')
    assert len(w.columnWidget.columns()) == 1
