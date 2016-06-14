
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.config import BASE_DIR, CorpusConfig

from ..plot import SCTSummaryWidget

from ..workers import (DiscourseQueryWorker)

from .base import DataListWidget, CollapsibleWidgetPair, DetailedMessageBox, CollapsibleTabWidget

from .selectable_audio import SelectableAudioWidget

from polyglotdb import CorpusContext

from polyglotdb.exceptions import GraphQueryError

class DiscourseWidget(QtWidgets.QWidget):
    discourseChanged = QtCore.pyqtSignal(str, object, object)
    def __init__(self):
        super(DiscourseWidget, self).__init__()

        self.config = None

        layout = QtWidgets.QHBoxLayout()

        self.discourseList = QtWidgets.QListWidget()
        self.discourseList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.discourseList.currentItemChanged.connect(self.changeDiscourse)

        layout.addWidget(self.discourseList)

        self.setLayout(layout)

    def changeDiscourse(self):
        item = self.discourseList.currentItem()
        if item is None:
            discourse = None
        else:
            discourse = item.text()
        self.discourseChanged.emit(discourse, None, None)

    def updateConfig(self, config):
        self.config = config
        self.discourseList.clear()
        if self.config is None or self.config.corpus_name == '':
            return
        try:
            with CorpusContext(self.config) as c:
                for d in sorted(c.discourses):
                    self.discourseList.addItem(d)
        except GraphQueryError:
            self.discourseList.clear()

class ViewWidget(CollapsibleTabWidget):
    
    changingDiscourse = QtCore.pyqtSignal()
    connectionIssues = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        super(ViewWidget, self).__init__(parent)
   
        self.discourseWidget = SelectableAudioWidget()

        self.summaryWidget = SCTSummaryWidget(self)

        self.dataTabs = QtWidgets.QTabWidget()

        self.phoneList = DataListWidget(self.summaryWidget, 'p')
        self.phoneList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.wordList = DataListWidget(self.summaryWidget, 'w')
        self.wordList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.dataTabs.addTab(self.phoneList, 'Phones')
        self.dataTabs.addTab(self.wordList, 'Words')

        summaryTab = CollapsibleWidgetPair(QtCore.Qt.Horizontal, self.summaryWidget.native, self.dataTabs)

        self.addTab(self.discourseWidget, 'Discourse')
        #self.addTab(summaryTab, 'Summary')

        self.worker = DiscourseQueryWorker()
        self.worker.dataReady.connect(self.discourseWidget.updateDiscourseModel)
        self.changingDiscourse.connect(self.worker.stop)
        self.changingDiscourse.connect(self.discourseWidget.clearDiscourse)
        self.worker.errorEncountered.connect(self.showError)
        self.worker.connectionIssues.connect(self.connectionIssues.emit)


    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def changeDiscourse(self, discourse, begin = None, end = None):
        if discourse:
            self.changingDiscourse.emit()
            kwargs = {}
            if begin is None:
                begin = 0
            if end is None:
                end = 30
            kwargs['config'] = self.config
            kwargs['discourse'] = discourse
            kwargs['begin'] = begin
            kwargs['end'] = end
            print(discourse, begin, end)
            self.worker.setParams(kwargs)
            self.worker.start()

    def updateConfig(self, config):
        self.config = config
        self.changingDiscourse.emit()
        self.discourseWidget.config = config
        if self.config is None:
            return
        if self.config.corpus_name:
            with CorpusContext(self.config) as c:
                if c.hierarchy != self.discourseWidget.hierarchy:
                    self.discourseWidget.updateHierachy(c.hierarchy)

