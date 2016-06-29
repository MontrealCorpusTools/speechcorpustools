
import pytest

from speechtools.widgets.annotation import SubannotationDialog, NoteDialog
from speechtools.widgets.audio import MediaPlayer
from speechtools.widgets.base import CollapsibleWidgetPair, DataListWidget, DetailedMessageBox
from speechtools.widgets.connection import ConnectWidget, CorporaList
from speechtools.widgets.details import DetailsWidget
from speechtools.widgets.help import HelpWidget
from speechtools.widgets.main import DiscourseWidget, ViewWidget
from speechtools.widgets.selectable_audio import SelectableAudioWidget
from speechtools.widgets.structure import HierarchyWidget

def test_subannotation_dialog(qtbot):
    w = SubannotationDialog()
    qtbot.addWidget(w)

@pytest.mark.xfail
def test_notes_dialog(qtbot):
    w = NoteDialog()
    qtbot.addWidget(w)

def test_audio(qtbot):
    w = MediaPlayer()
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

def test_selectable(qtbot):
    w = SelectableAudioWidget()
    qtbot.addWidget(w)

def test_hierarchy(qtbot):
    w = HierarchyWidget()
    qtbot.addWidget(w)



