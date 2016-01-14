import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.gui.widgets import ConnectWidget, ImportWidget, ExportWidget

from .plot import SCTAudioWidget, SCTSummaryWidget

from .workers import QueryWorker, DiscourseQueryWorker

from .models import QueryResultsModel

from .views import ResultsView

from speechtools.corpus import CorpusContext

def get_system_font_height():
    f = QtGui.QFont()
    fm = QtGui.QFontMetrics(f)
    return fm.height()

class SelectableAudioWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(SelectableAudioWidget, self).__init__(parent)
        self.rectselect = False
        layout = QtWidgets.QVBoxLayout()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus(True)

        self.audioWidget = SCTAudioWidget()
        self.audioWidget.events.mouse_press.connect(self.on_mouse_press)
        self.audioWidget.events.mouse_release.connect(self.on_mouse_release)
        self.audioWidget.events.mouse_move.connect(self.on_mouse_move)
        w = self.audioWidget.native
        w.setFocusPolicy(QtCore.Qt.NoFocus)
        layout.addWidget(w)

        self.setLayout(layout)

    def keyPressEvent(self, event):
        """
        Bootstrap the Qt keypress event items
        """
        if event.key() == QtCore.Qt.Key_Shift:
            self.rectselect = True
        else:
            print(event.key())

    def keyReleaseEvent(self, event):
        """
        Bootstrap the Qt Key release event
        """
        if event.key() == QtCore.Qt.Key_Shift:
            self.rectselect = False

    def on_mouse_press(self, event):
        """
        Mouse button press event
        """
        if event.button == 1 and self.rectselect == False:
            pass

        elif event.button == 1 and self.rectselect == True:
            self.audioWidget[0:2, 0].set_end_selection_time(None)
            tr = self.audioWidget.scene.node_transform(self.audioWidget[0:2, 0].visuals[0])
            pos = tr.map(event.pos)
            time = pos[0]
            self.audioWidget[0:2, 0].set_begin_selection_time(time)

    def on_mouse_release(self, event):
        is_single_click = not event.is_dragging or abs(np.sum(event.press_event.pos - event.pos)) < 10
        if event.button == 1 and self.rectselect == True:
            #print(event)
            pass
        elif event.button == 1 and is_single_click and self.rectselect == False:

            tr = self.audioWidget.scene.node_transform(self.audioWidget[0:2, 0].visuals[0])
            pos = tr.map(event.pos)
            time = pos[0]
            self.audioWidget[0:2, 0].set_play_time(time)

    def on_mouse_move(self, event):
        if event.button == 1 and event.is_dragging and self.rectselect:
            #print('hello')
            tr = self.audioWidget.scene.node_transform(self.audioWidget[0:2, 0].visuals[0])
            pos = tr.map(event.pos)
            time = pos[0]
            self.audioWidget[0:2, 0].set_end_selection_time(time)

    def updatePlots(self, data):
        annotations, audio_file = data
        self.audioWidget.plot(audio_file, annotations)

class QueryForm(QtWidgets.QWidget):
    finishedRunning = QtCore.pyqtSignal(object)
    def __init__(self):
        super(QueryForm, self).__init__()
        self.config = None
        headerLayout = QtWidgets.QHBoxLayout()

        self.linguisticSelect = QtWidgets.QComboBox()
        self.executeButton = QtWidgets.QPushButton('Run query')
        self.executeButton.clicked.connect(self.runQuery)
        self.executeButton.setDisabled(True)
        headerLayout.addWidget(QtWidgets.QLabel('Linguistic type'))

        headerLayout.addWidget(self.linguisticSelect)
        headerLayout.addWidget(self.executeButton)

        mainLayout = QtWidgets.QVBoxLayout()

        mainLayout.addLayout(headerLayout)

        self.setLayout(mainLayout)

        self.worker = QueryWorker()
        self.worker.dataReady.connect(self.setResults)

    def runQuery(self):
        kwargs = {}
        if self.config is None:
            return
        kwargs['annotation_type'] = self.linguisticSelect.currentText()
        kwargs['config'] = self.config
        self.worker.setParams(kwargs)
        self.worker.start()

    def updateConfig(self, config):
        self.config = config
        self.linguisticSelect.clear()
        if self.config is None:
            self.executeButton.setDisabled(True)
            return
        self.executeButton.setDisabled(False)
        with CorpusContext(config) as c:
            for a in c.annotation_types:
                self.linguisticSelect.addItem(a)

    def setResults(self, results):
        self.finishedRunning.emit(results)

class QueryResults(QtWidgets.QWidget):
    def __init__(self, results):
        super(QueryResults, self).__init__()

        self.query = results[0]

        self.resultsModel = QueryResultsModel(results[1])

        self.tableWidget = ResultsView()

        self.proxyModel = QtCore.QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.resultsModel)
        self.tableWidget.setModel(self.proxyModel)

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

class QueryWidget(QtWidgets.QWidget):
    def __init__(self):
        super(QueryWidget, self).__init__()
        self.config = None
        self.tabs = QtWidgets.QTabWidget()
        self.currentIndex = 1
        self.queryForm = QueryForm()
        self.queryForm.finishedRunning.connect(self.updateResults)

        self.tabs.addTab(self.queryForm, 'New query')

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.tabs)

        self.setLayout(layout)

    def updateConfig(self, config):
        self.config = config

        self.queryForm.updateConfig(config)

    def updateResults(self, results):
        name = 'Query {}'.format(self.currentIndex)
        self.currentIndex += 1
        widget = QueryResults(results)
        self.tabs.addTab(widget, name)

class HelpWidget(QtWidgets.QWidget):
    def __init__(self):
        super(HelpWidget, self).__init__()

        layout = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel('Placeholder help, kind useless, oh well'))
        self.setLayout(layout)

class DiscourseWidget(QtWidgets.QWidget):
    discourseChanged = QtCore.pyqtSignal(str)
    def __init__(self):
        super(DiscourseWidget, self).__init__()

        self.config = None

        layout = QtWidgets.QHBoxLayout()

        self.discourseList = QtWidgets.QListWidget()
        self.discourseList.currentItemChanged.connect(self.changeDiscourse)

        layout.addWidget(self.discourseList)

        self.setLayout(layout)

    def changeDiscourse(self):
        discourse = self.discourseList.currentItem().text()
        self.discourseChanged.emit(discourse)

    def updateConfig(self, config):
        self.config = config
        self.discourseList.clear()
        if self.config.corpus_name == '':
            return
        with CorpusContext(self.config) as c:
            for d in sorted(c.discourses):
                self.discourseList.addItem(d)

class ViewWidget(QtWidgets.QWidget):
    plotDataReady = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        super(ViewWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()

        tabs = QtWidgets.QTabWidget()

        self.discourseWidget = SelectableAudioWidget()
        self.plotDataReady.connect(self.discourseWidget.updatePlots)

        self.summaryWidget = SCTSummaryWidget(self)
        self.plotDataReady.connect(self.summaryWidget.updatePlots)

        self.dataTabs = QtWidgets.QTabWidget()

        self.phoneList = DataListWidget(self.summaryWidget, 'p')
        self.phoneList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.wordList = DataListWidget(self.summaryWidget, 'w')
        self.wordList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.dataTabs.addTab(self.phoneList, 'Phones')
        self.dataTabs.addTab(self.wordList, 'Words')

        summaryTab = CollapsibleWidgetPair(QtCore.Qt.Horizontal, self.summaryWidget.native, self.dataTabs)

        tabs.addTab(self.discourseWidget, 'Discourse')
        tabs.addTab(summaryTab, 'Summary')

        layout.addWidget(tabs, 1)

        self.setLayout(layout)

        self.worker = DiscourseQueryWorker()
        self.worker.dataReady.connect(self.plotDataReady.emit)

    def changeDiscourse(self, discourse):



        with CorpusContext(self.config) as c:
            phone_annotation = c.lowest_annotation

        kwargs = {}
        if phone_annotation is not None:
            kwargs['seg_type'] = phone_annotation.type
        kwargs['word_type'] = 'word'
        kwargs['config'] = self.config
        kwargs['discourse'] = discourse

        self.worker.setParams(kwargs)
        self.worker.run()

        self.phoneList.selectAll()
        self.wordList.selectAll()

    def updateConfig(self, config):
        self.config = config


class CollapsibleWidgetPair(QtWidgets.QSplitter):
    def __init__(self, orientation, widgetOne, widgetTwo, collapsible = 1, parent = None):
        super(CollapsibleWidgetPair, self).__init__(orientation, parent)
        self.collapsible = collapsible
        self.addWidget(widgetOne)
        self.addWidget(widgetTwo)

        if self.orientation() == QtCore.Qt.Horizontal:
            if self.collapsible == 1:
                self.uncollapsed_arrow = QtCore.Qt.RightArrow
                self.collapsed_arrow = QtCore.Qt.LeftArrow
            else:
                self.uncollapsed_arrow = QtCore.Qt.LeftArrow
                self.collapsed_arrow = QtCore.Qt.RightArrow
        else:
            if self.collapsible == 1:
                self.uncollapsed_arrow = QtCore.Qt.DownArrow
                self.collapsed_arrow = QtCore.Qt.UpArrow
            else:
                self.uncollapsed_arrow = QtCore.Qt.UpArrow
                self.collapsed_arrow = QtCore.Qt.DownArrow

        size_unit = get_system_font_height()
        handle = self.handle(1)
        self.button = QtWidgets.QToolButton(handle)
        if self.orientation() == QtCore.Qt.Horizontal:
            self.button.setMinimumHeight(8 * size_unit)
            layout = QtWidgets.QVBoxLayout()
            self.button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        else:
            self.button.setMinimumWidth(8 * size_unit)
            layout = QtWidgets.QHBoxLayout()
            self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)

        self.button.setArrowType(self.uncollapsed_arrow)
        layout.setContentsMargins(0, 0, 0, 0)
        self.button.clicked.connect(self.onCollapse)
        layout.addWidget(self.button)
        handle.setLayout(layout)
        self.setHandleWidth(size_unit)

    def onCollapse(self):
        if self.collapsible == 1:
            collapsed_size = [1, 0]
            uncollapsed_size = [1000,1]
        else:
            collapsed_size = [0, 1]
            uncollapsed_size = [1, 1000]
        if self.sizes()[self.collapsible]:
            self.setSizes(collapsed_size)
            self.button.setArrowType(self.collapsed_arrow)
        else:
            self.setSizes(uncollapsed_size)
            self.button.setArrowType(self.uncollapsed_arrow)


class DataListWidget(QtWidgets.QListWidget):
    def __init__(self, plot, plot_type, parent = None):
        super(DataListWidget, self).__init__(parent)
        self.plot = plot
        self.plot_type = plot_type
        self.itemSelectionChanged.connect(self.update_plot)

    def selectAll(self):
        for i in range(self.count()): self.item(i).setSelected(True)

    def update_plot(self):
        labels = [i.text() for i in self.selectedItems()]
        self.plot.update_data(labels, self.plot_type)
