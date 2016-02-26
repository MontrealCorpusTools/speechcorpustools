
from PyQt5 import QtGui, QtCore, QtWidgets

from speechtools.corpus import CorpusContext

from polyglotdb.graph.func import Sum, Count

from .base import DetailedMessageBox

from ..models import QueryResultsModel, ProxyModel

from ..views import ResultsView

from ..workers import (QueryWorker, Lab1QueryWorker, ExportQueryWorker)

class QueryForm(QtWidgets.QWidget):
    finishedRunning = QtCore.pyqtSignal(object)
    def __init__(self):
        super(QueryForm, self).__init__()
        self.config = None
        headerLayout = QtWidgets.QHBoxLayout()

        self.linguisticSelect = QtWidgets.QComboBox()
        self.querySelect = QtWidgets.QComboBox()
        self.querySelect.addItem('Lab 1 stops')
        self.querySelect.addItem('Lab 2 stops')
        self.querySelect.addItem('Lab 1 laryngeal sampling')
        self.querySelect.addItem('Lab 2 laryngeal sampling')
        self.executeButton = QtWidgets.QPushButton('Run query')
        self.exportButton = QtWidgets.QPushButton('Export query')
        self.executeButton.clicked.connect(self.runQuery)
        self.executeButton.setDisabled(True)
        self.exportButton.clicked.connect(self.exportQuery)
        self.exportButton.setDisabled(True)
        headerLayout.addWidget(QtWidgets.QLabel('Query type'))

        headerLayout.addWidget(self.querySelect)
        headerLayout.addWidget(self.executeButton)
        headerLayout.addWidget(self.exportButton)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(headerLayout)

        phon4Layout = QtWidgets.QHBoxLayout()

        #self.lab1Button = QtWidgets.QPushButton('Search for Lab 1 stops')
        #self.lab1Button.setDisabled(True)
        #self.lab1Button.clicked.connect(self.lab1Query)
        #self.exportButton = QtWidgets.QPushButton('Export Lab 1 stops')
        #self.exportButton.clicked.connect(self.runExportQuery)
        #self.exportButton.setDisabled(True)

        #phon4Layout.addWidget(self.lab1Button)
        #phon4Layout.addWidget(self.exportButton)

        #mainLayout.addLayout(phon4Layout)

        #phon4Lab2Layout = QtWidgets.QHBoxLayout()

        #self.lab2Button = QtWidgets.QPushButton('Search for Lab 2 stops')
        #self.lab2Button.setDisabled(True)
        #self.lab2Button.clicked.connect(self.lab2Query)
        #self.export2Button = QtWidgets.QPushButton('Export Lab 2 stops')
        #self.export2Button.clicked.connect(self.runExport2Query)
        #self.export2Button.setDisabled(True)

        #phon4Lab2Layout.addWidget(self.lab2Button)
        #phon4Lab2Layout.addWidget(self.export2Button)

        #mainLayout.addLayout(phon4Lab2Layout)

        self.setLayout(mainLayout)

        self.worker = QueryWorker()
        self.worker.dataReady.connect(self.setResults)

        self.lab1Worker = Lab1QueryWorker()
        self.lab1Worker.dataReady.connect(self.setResults)
        self.lab1Worker.errorEncountered.connect(self.showError)

        self.exportWorker = ExportQueryWorker()
        self.exportWorker.errorEncountered.connect(self.showError)

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
            if query_type in ['Lab 1 stops', 'Lab 2 stops']:
                if query_type == 'Lab 1 stops':
                    filters.append(a_type.phon4lab1 == True)
                elif query_type == 'Lab 2 stops':
                    filters.append(a_type.phon4lab2 == True)
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
        if self.config is None:
            return
        kwargs = {}
        kwargs['config'] = self.config
        filters = []
        columns = []
        query_type = self.querySelect.currentText()
        with CorpusContext(self.config) as c:
            a_type = c.hierarchy.lowest
            w_type = c.hierarchy[a_type]
            utt_type = c.hierarchy.highest
            a_type = getattr(c, a_type)
            w_type = getattr(a_type, w_type)
            utt_type = getattr(w_type, utt_type)
            if query_type in ['Lab 1 stops', 'Lab 2 stops']:
                if query_type == 'Lab 1 stops':
                    filters.append(a_type.phon4lab1 == True)
                elif query_type == 'Lab 2 stops':
                    filters.append(a_type.phon4lab2 == True)
                columns = [a_type.label.column_name('Stop'),
                            a_type.begin.column_name('Begin'),
                            a_type.end.column_name('End'),
                            w_type.label.column_name('Word'),
                            a_type.checked.column_name('Annotated'),
                            a_type.speaker.name.column_name('Speaker'),
                            a_type.discourse.name.column_name('Discourse'),
                            a_type.id.column_name('Unique_id'),
                            a_type.notes.column_name('Notes')]

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
            else:
                if query_type == 'Lab 1 laryngeal sampling':
                    filters.extend([a_type.begin == w_type.begin,
                                    w_type.begin == utt_type.begin,
                                a_type.following.type_subset == 'syllabic'])
                elif query_type == 'Lab 2 laryngeal sampling':
                    filters.extend([a_type.begin != w_type.begin,
                                a_type.end != w_type.end,
                            w_type.begin == utt_type.begin,
                            #qw_type.end != utt_type.end)
                            a_type.following.type_subset == 'syllabic',
                            a_type.previous.type_subset == 'syllabic',
                            w_type.num_syllables == 2,
                            #w_type.num_syllables <= 3,
                            ])
                columns.extend([a_type.speaker.name.column_name('speaker'),
                            Count(getattr(a_type, 'class').column_name('class')),
                            #a_type.place.column_name('place'),
                            #Count(a_type.label)
                            ])
        kwargs['query_type'] = query_type
        kwargs['filters'] = filters
        kwargs['columns'] = columns
        self.lab1Worker.setParams(kwargs)
        self.lab1Worker.start()

    def updateConfig(self, config):
        self.config = config
        self.linguisticSelect.clear()
        if self.config is None or self.config.corpus_name == '':
            self.executeButton.setDisabled(True)
            #self.lab1Button.setDisabled(True)
            self.exportButton.setDisabled(True)
            #self.lab2Button.setDisabled(True)
            #self.export2Button.setDisabled(True)
            return
        self.executeButton.setDisabled(False)
        #self.lab1Button.setDisabled(False)
        self.exportButton.setDisabled(False)
        #self.lab2Button.setDisabled(False)
        #self.export2Button.setDisabled(False)
        #with CorpusContext(config) as c:
        #    for a in c.annotation_types:
        #        self.linguisticSelect.addItem(a)

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
