
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.config import BASE_DIR, CorpusConfig

from ..plot import SCTSummaryWidget

from ..workers import (DiscourseQueryWorker, DiscourseAudioWorker)

from .base import DataListWidget, CollapsibleWidgetPair, DetailedMessageBox, CollapsibleTabWidget

from .selectable_audio import SelectableAudioWidget

from polyglotdb import CorpusContext

class DiscourseWidget(QtWidgets.QWidget):
    discourseChanged = QtCore.pyqtSignal(str)
    viewRequested = QtCore.pyqtSignal(object, object)
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
        self.discourseChanged.emit(discourse)
        self.viewRequested.emit(None, None)

    def changeView(self, discourse, begin, end):
        self.viewRequested.emit(begin, end)
        for i in range(self.discourseList.count()):
            item = self.discourseList.item(i)
            if item.text() == discourse:
                index = self.discourseList.model().index(i, 0)
                self.discourseList.selectionModel().select(index,
                                QtCore.QItemSelectionModel.ClearAndSelect|QtCore.QItemSelectionModel.Rows)
                break
        self.discourseChanged.emit(discourse)

    def updateConfig(self, config):
        self.config = config
        self.discourseList.clear()
        if self.config is None or self.config.corpus_name == '':
            return
        with CorpusContext(self.config) as c:
            for d in sorted(c.discourses):
                self.discourseList.addItem(d)

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

        self.audioWorker = DiscourseAudioWorker()
        self.audioWorker.dataReady.connect(self.discourseWidget.updateAudio)
        self.audioWorker.errorEncountered.connect(self.showError)

        self.worker = DiscourseQueryWorker()
        self.worker.dataReady.connect(self.discourseWidget.updateAnnotations)
        self.changingDiscourse.connect(self.worker.stop)
        self.changingDiscourse.connect(self.discourseWidget.clearDiscourse)
        self.worker.errorEncountered.connect(self.showError)
        self.worker.connectionIssues.connect(self.connectionIssues.emit)


    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def changeDiscourse(self, discourse):
        if discourse:
            self.changingDiscourse.emit()
            kwargs = {}

            kwargs['config'] = self.config
            kwargs['discourse'] = discourse

            self.audioWorker.setParams(kwargs)
            self.audioWorker.start()
            kwargs = {}
            with CorpusContext(self.config) as c:
                self.discourseWidget.updateHierachy(c.hierarchy)
                kwargs['seg_type'] = c.hierarchy.lowest
                kwargs['word_type'] = c.hierarchy.highest

            kwargs['config'] = self.config
            kwargs['discourse'] = discourse

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

