
import pytest

from speechtools.gui.widgets.annotation import SubannotationDialog, NoteDialog
from speechtools.gui.widgets.audio import AudioOutput, Generator
from speechtools.gui.widgets.base import CollapsibleWidgetPair, DataListWidget, DetailedMessageBox
from speechtools.gui.widgets.connection import ConnectWidget, CorporaList
from speechtools.gui.widgets.details import DetailsWidget
from speechtools.gui.widgets.help import HelpWidget
from speechtools.gui.widgets.main import DiscourseWidget, ViewWidget
from speechtools.gui.widgets.query import QueryWidget, QueryForm, QueryResults
from speechtools.gui.widgets.selectable_audio import SelectableAudioWidget
from speechtools.gui.widgets.structure import HierarchyWidget

def test_subannotation_dialog(qtbot):
    w = SubannotationDialog()
    qtbot.addWidget(w)

@pytest.mark.xfail
def test_notes_dialog(qtbot):
    w = NoteDialog()
    qtbot.addWidget(w)

def test_audio(qtbot):
    w = AudioOutput()
    qtbot.addWidget(w)

def test_connection(qtbot):
    w = ConnectWidget()
    qtbot.addWidget(w)

def test_corpora_list(qtbot):
    w = CorporaList()
    qtbot.addWidget(w)

def test_details(qtbot):
    w = DetailsWidget()
    qtbot.addWidget(w)

def test_help(qtbot):
    w = HelpWidget()
    qtbot.addWidget(w)

def test_discourse_widget(qtbot):
    w = DiscourseWidget()
    qtbot.addWidget(w)

def test_view_widget(qtbot):
    w = ViewWidget()
    qtbot.addWidget(w)

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

def test_selectable(qtbot):
    w = SelectableAudioWidget()
    qtbot.addWidget(w)

def test_hierarchy(qtbot):
    w = HierarchyWidget()
    qtbot.addWidget(w)



