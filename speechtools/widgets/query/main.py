import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum, Count

from ..base import DetailedMessageBox

from ...models import QueryResultsModel, ProxyModel

from ...views import ResultsView

from ...workers import (QueryWorker, ExportQueryWorker)

from .graphical import GraphicalQuery

from .basic import BasicQuery

from ...profiles import available_query_profiles, QueryProfile

class QueryProfileWidget(QtWidgets.QWidget):
    profileSelected = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        super(QueryProfileWidget, self).__init__(parent)
        self.querySelect = QtWidgets.QComboBox()
        self.refresh()

        self.querySelect.currentIndexChanged.connect(self.changeProfile)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Query profiles', self.querySelect)
        self.setLayout(layout)

    def changeProfile(self):
        name = self.currentName()
        if name == '':
            return
        if name == 'New query':
            self.profileSelected.emit(QueryProfile())
        else:
            self.profileSelected.emit(QueryProfile.load_profile(name))

    def refresh(self):
        self.querySelect.clear()
        self.querySelect.addItem('New query')
        profiles = available_query_profiles()
        for p in profiles:
            self.querySelect.addItem(p)

    def currentName(self):
        return self.querySelect.currentText()

    def select(self, name):
        self.querySelect.setCurrentIndex(self.querySelect.findText(name))

class SaveDialog(QtWidgets.QDialog):
    def __init__(self, default_name, parent = None):
        super(SaveDialog, self).__init__(parent)

        mainlayout = QtWidgets.QFormLayout()

        self.nameEdit = QtWidgets.QLineEdit()
        self.nameEdit.setText(default_name)

        mainlayout.addRow('Name', self.nameEdit)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Save')
        self.acceptButton.setDefault(True)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.setAutoDefault(False)

        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.cancelButton)

        acwidget = QtWidgets.QWidget()
        acwidget.setLayout(aclayout)

        mainlayout.addWidget(acwidget)

        self.setLayout(mainlayout)


    def value(self):
        return self.nameEdit.text()

class QueryForm(QtWidgets.QWidget):
    finishedRunning = QtCore.pyqtSignal(object)
    def __init__(self):
        super(QueryForm, self).__init__()
        self.config = None

        mainLayout = QtWidgets.QVBoxLayout()
        headerLayout = QtWidgets.QHBoxLayout()

        self.queryWidget = BasicQuery()

        self.profileWidget = QueryProfileWidget()
        self.profileWidget.profileSelected.connect(self.queryWidget.updateProfile)

        self.executeButton = QtWidgets.QPushButton('Run query')
        self.exportButton = QtWidgets.QPushButton('Export query results')
        self.saveButton = QtWidgets.QPushButton('Save query profile')
        self.executeButton.clicked.connect(self.runQuery)
        self.executeButton.setDisabled(True)
        self.exportButton.clicked.connect(self.exportQuery)
        self.exportButton.setDisabled(True)
        self.saveButton.clicked.connect(self.saveProfile)
        self.saveButton.setDisabled(True)

        mainLayout.addWidget(self.profileWidget)
        mainLayout.addWidget(self.queryWidget)
        headerLayout.addWidget(self.executeButton)
        headerLayout.addWidget(self.exportButton)
        headerLayout.addWidget(self.saveButton)
        mainLayout.addLayout(headerLayout)

        self.setLayout(mainLayout)

        self.queryWorker = QueryWorker()
        self.queryWorker.dataReady.connect(self.setResults)
        self.queryWorker.errorEncountered.connect(self.showError)

        self.exportWorker = ExportQueryWorker()
        self.exportWorker.errorEncountered.connect(self.showError)

    def saveProfile(self):
        default = self.profileWidget.currentName()
        if default == 'New query':
            new_default_template = 'New query {}'
            index = 1
            while new_default_template.format(index) in available_query_profiles():
                index += 1
            default = new_default_template.format(index)

        dialog = SaveDialog(default, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile = self.currentProfile()
            profile.name = dialog.value()
            profile.save_profile()
            self.profileWidget.refresh()
            self.profileWidget.select(dialog.value())

    def currentProfile(self):
        return self.queryWidget.profile()

    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def exportQuery(self):
        if self.config is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export data", filter = "CSV (*.txt  *.csv)")

        if not path:
            return
        filters = []
        columns = []
        query_type = self.querySelect.currentText()
        with CorpusContext(self.config) as c:
            a_type = c.hierarchy.lowest
            w_type = c.hierarchy[a_type]
            utt_type = c.hierarchy.highest
            a_type = getattr(c, a_type)
            w_type = getattr(a_type, w_type)
            utt_type = getattr(a_type, utt_type)
            if query_type in ['Lab 1 stops', 'Lab 2 stops', 'Lab 3 stops']:
                if query_type == 'Lab 1 stops':
                    filters.append(a_type.phon4lab1 == True)
                elif query_type == 'Lab 2 stops':
                    filters.append(a_type.phon4lab2 == True)
                elif query_type == 'Lab 3 stops':
                    filters.append(a_type.phon4lab3 == True)
                columns = [a_type.label.column_name('Stop'),
                            a_type.begin.column_name('Begin'),
                            a_type.end.column_name('End'),
                            a_type.duration.column_name('Duration')]
                if 'burst' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    columns.extend([a_type.burst.begin.column_name('Burst_begin'),
                            a_type.burst.end.column_name('Burst_end'),
                            Sum(a_type.burst.duration).column_name('Burst_duration')])
                if 'voicing' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    columns.extend([a_type.voicing.begin.column_name('Voicing_begin'),
                                a_type.voicing.end.column_name('Voicing_end'),
                                Sum(a_type.voicing.duration).column_name('Voicing_duration')])
                if 'closure' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    columns.extend([a_type.closure.begin.column_name('Closure_begin'),
                                a_type.closure.end.column_name('Closure_end'),
                                Sum(a_type.closure.duration).column_name('Closure_duration')])
                if 'preaspiration' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    columns.extend([a_type.preaspiration.begin.column_name('Preaspiration_begin'),
                                a_type.preaspiration.end.column_name('Preaspiration_end'),
                                Sum(a_type.preaspiration.duration).column_name('Preaspiration_duration')])
                if 'vowel_duration' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    columns.extend([a_type.vowel_duration.begin.column_name('vowel_duration_begin'),
                                a_type.vowel_duration.end.column_name('vowel_duration_end'),
                                Sum(a_type.vowel_duration.duration).column_name('vowel_duration')])

                columns.extend([w_type.label.column_name('Word'),
                            w_type.begin.column_name('Word_begin'),
                            w_type.end.column_name('Word_end'),
                            w_type.duration.column_name('Word_duration'),
                            w_type.transcription.column_name('Word_transcription'),
                            a_type.following.label.column_name('Following_segment'),
                            a_type.following.begin.column_name('Following_segment_begin'),
                            a_type.following.end.column_name('Following_segment_end'),
                            a_type.following.duration.column_name('Following_segment_duration'),
                            a_type.following.following.label.column_name('Following_following_segment'),
                            a_type.following.following.begin.column_name('Following_following_segment_begin'),
                            a_type.following.following.end.column_name('Following_following_segment_end'),
                            a_type.following.following.duration.column_name('Following_following_segment_duration'),
                            a_type.checked.column_name('Annotated'),
                            a_type.speaker.name.column_name('Speaker'),
                            a_type.discourse.name.column_name('Discourse'),
                            w_type.utterance.phones.rate.column_name('Speaking_rate'),
                            a_type.notes.column_name('Notes')])

        kwargs = {}
        kwargs['config'] = self.config
        kwargs['path'] = path
        kwargs['filters'] = filters
        kwargs['columns'] = columns
        self.exportWorker.setParams(kwargs)
        self.exportWorker.start()


    def runQuery(self):
        self.queryWorker.stop()
        if self.config is None:
            return
        kwargs = {}
        kwargs['config'] = self.config
        kwargs['profile'] = self.currentProfile()

        self.queryWorker.setParams(kwargs)
        self.queryWorker.start()

    def updateConfig(self, config):
        self.config = config
        if self.config is None or self.config.corpus_name == '':
            self.executeButton.setDisabled(True)
            self.exportButton.setDisabled(True)
            self.saveButton.setDisabled(True)
            return
        self.executeButton.setDisabled(False)
        self.exportButton.setDisabled(False)
        self.saveButton.setDisabled(False)
        with CorpusContext(config) as c:
            h = c.hierarchy
        self.queryWidget.setHierarchy(h)


    def setResults(self, results):
        self.finishedRunning.emit(results)

class QueryResults(QtWidgets.QWidget):
    def __init__(self, results):
        super(QueryResults, self).__init__()

        self.query = results[0]

        self.resultsModel = QueryResultsModel(results[1])

        self.tableWidget = ResultsView()

        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.resultsModel)
        self.proxyModel.setSortRole( QueryResultsModel.SortRole )
        self.proxyModel.setDynamicSortFilter(False)
        self.tableWidget.setModel(self.proxyModel)

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

class QueryWidget(QtWidgets.QWidget):
    viewRequested = QtCore.pyqtSignal(str, float, float)
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
        widget.tableWidget.viewRequested.connect(self.viewRequested.emit)
        self.tabs.addTab(widget, name)

    def markAnnotated(self, value):
        w = self.tabs.currentWidget()
        if not isinstance(w, QueryResults):
            return
        w.tableWidget.markAnnotated(value)

    def requestNext(self):
        w = self.tabs.currentWidget()
        if not isinstance(w, QueryResults):
            return
        w.tableWidget.selectNext()

    def requestPrevious(self):
        w = self.tabs.currentWidget()
        if not isinstance(w, QueryResults):
            return
        w.tableWidget.selectPrevious()
