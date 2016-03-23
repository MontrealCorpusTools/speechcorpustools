import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum, Count

from ..base import DetailedMessageBox

from ...models import QueryResultsModel, ProxyModel

from ...views import ResultsView

from ...workers import (QueryWorker, Lab1QueryWorker, ExportQueryWorker)

from .graphical import GraphicalQuery

from .basic import BasicQuery

class QueryForm(QtWidgets.QWidget):
    finishedRunning = QtCore.pyqtSignal(object)
    def __init__(self):
        super(QueryForm, self).__init__()
        self.config = None

        mainLayout = QtWidgets.QVBoxLayout()
        headerLayout = QtWidgets.QHBoxLayout()

        self.graphicalQuery = BasicQuery()


        self.linguisticSelect = QtWidgets.QComboBox()
        self.querySelect = QtWidgets.QComboBox()
        self.querySelect.addItem('Lab 1 stops')
        self.querySelect.addItem('Lab 2 stops')
        self.querySelect.addItem('Lab 3 stops')
        if not getattr(sys, 'frozen', False):
            mainLayout.addWidget(self.graphicalQuery)
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
        mainLayout.addLayout(headerLayout)

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
            if query_type in ['Lab 1 stops', 'Lab 2 stops', 'Lab 3 stops']:
                columns = [a_type.label.column_name('Stop')]
                if query_type == 'Lab 1 stops':
                    filters.append(a_type.phon4lab1 == True)
                    columns.append(a_type.following.label.column_name('Following_segment'))
                elif query_type == 'Lab 2 stops':
                    filters.append(a_type.phon4lab2 == True)
                    columns.extend([a_type.previous.label.column_name('Previous_segment'),
                                    a_type.following.label.column_name('Following_segment')])
                elif query_type == 'Lab 3 stops':
                    filters.append(a_type.phon4lab3 == True)
                    if ('final_sound', str) in c.hierarchy.type_properties[w_type.type]:
                        columns.append(w_type.final_sound.column_name('Underlying_sound'))
                    if ('tense_sound', str) in c.hierarchy.type_properties[w_type.type]:
                        columns.append(w_type.tense_sound.column_name('Underlying_tense_sound'))
                    columns.append(a_type.previous.label.column_name('Previous_segment'))
                columns.extend([a_type.begin.column_name('Begin'),
                        a_type.end.column_name('End'),
                        w_type.label.column_name('Word'),
                        w_type.transcription.column_name('Transcription'),
                        a_type.checked.column_name('Annotated'),
                        a_type.speaker.name.column_name('Speaker'),
                        a_type.discourse.name.column_name('Discourse'),
                        a_type.id.column_name('Unique_id'),
                        a_type.notes.column_name('Notes')])

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
                            getattr(a_type, 'class').column_name('class'),
                            a_type.place.column_name('place'),
                            Count(a_type.label)
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
        with CorpusContext(config) as c:
            h = c.hierarchy
        self.graphicalQuery.setHierarchy(h)


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
