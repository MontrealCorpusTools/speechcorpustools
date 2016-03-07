import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from speechtools.corpus import CorpusContext

from polyglotdb.graph.func import Sum, Count

from .base import DetailedMessageBox

from ..models import QueryResultsModel, ProxyModel

from ..views import ResultsView

from ..workers import (QueryWorker, Lab1QueryWorker, ExportQueryWorker)

class NonScrollingComboBox(QtWidgets.QComboBox):
    def __init__(self, parent = None):
        super(NonScrollingComboBox, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()

class AnnotationRect(QtWidgets.QGraphicsTextItem):
    clicked = QtCore.pyqtSignal(object)
    def __init__(self, text, hierarchy, pos = 0):
        super(AnnotationRect, self).__init__(text)
        self.linear_position = pos
        self.hierarchy = hierarchy
        for i, at in enumerate(self.hierarchy.lowest_to_highest):
            if at == text:
                self.hierarchy_position = i
                break

    def paint(self, painter, option, widget = 0):
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtGui.QColor(230,230,230))
        r = option.rect
        mod = 50 * self.hierarchy_position
        r.setWidth(r.width() + mod)
        r.setX(0 - r.width() / 2)
        painter.drawRect(r)
        super(AnnotationRect, self).paint(painter, option, widget)

    def mousePressEvent(self, event):
        super(AnnotationRect, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.toPlainText())

class FilterWidgetItem(QtWidgets.QWidget):
    def __init__(self, column, value):
        super(FilterWidgetItem, self).__init__()

        self.column = column
        self.value = value

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(column))

        if value in (int, float):
            self.compWidget = NonScrollingComboBox()
            self.compWidget.addItem('=')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('>')
            self.compWidget.addItem('>=')
            self.compWidget.addItem('<')
            self.compWidget.addItem('<=')
            layout.addWidget(self.compWidget)
            self.valueWidget = QtWidgets.QLineEdit()
            layout.addWidget(self.valueWidget)
        self.setLayout(layout)

class SubsetWidgetItem(QtWidgets.QWidget):
    def __init__(self):
        super(SubsetWidgetItem, self).__init__()

        self.subsetList = NonScrollingComboBox()
        self.subsetList.addItem('')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Subset'))
        layout.addWidget(self.subsetList)
        self.setLayout(layout)

    def clear(self):
        self.subsetList.clear()
        self.subsetList.addItem('')

    def addItems(self, items):
        for i in items:
            self.subsetList.addItem(i)

class FilterWidget(QtWidgets.QGroupBox):
    def __init__(self):
        self.hierarchy = None
        super(FilterWidget, self).__init__('Filters')

        mainlayout = QtWidgets.QVBoxLayout()

        self.filterLayout = QtWidgets.QVBoxLayout()

        self.subsetWidget = SubsetWidgetItem()

        self.filterLayout.addWidget(self.subsetWidget)

        self.attributeBox = QtWidgets.QGroupBox('Attributes')

        self.attributeBox.setLayout(self.filterLayout)

        mainlayout.addWidget(self.attributeBox)

        self.speakerBox = QtWidgets.QGroupBox('Speakers')

        mainlayout.addWidget(self.speakerBox)
        self.discourseBox = QtWidgets.QGroupBox('Discourses')

        mainlayout.addWidget(self.discourseBox)

        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(mainlayout)

        layout = QtWidgets.QVBoxLayout()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(200)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.acceptButton = QtWidgets.QPushButton('Add filters')

        layout.addWidget(self.acceptButton)

        self.setLayout(layout)

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy

    def updateAnnotation(self, text):
        while self.filterLayout.count():
            item = self.filterLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()

        self.subsetWidget = SubsetWidgetItem()

        self.filterLayout.addWidget(self.subsetWidget)
        subsets = []
        if text in self.hierarchy.subset_tokens:
            for s in self.hierarchy.subset_tokens[text]:
                subsets.append(s)
        if text in self.hierarchy.subset_types:
            for s in self.hierarchy.subset_types[text]:
                subsets.append(s)
        self.subsetWidget.addItems(subsets)
        if text in self.hierarchy.type_properties:
            for p, v in self.hierarchy.type_properties[text]:
                self.filterLayout.addWidget(FilterWidgetItem(p, v))
        if text in self.hierarchy.token_properties:
            for p, v in self.hierarchy.token_properties[text]:
                self.filterLayout.addWidget(FilterWidgetItem(p, v))

class GraphicalQuery(QtWidgets.QWidget):
    vert_step = 50
    horz_step = 200
    def __init__(self):
        super(GraphicalQuery, self).__init__()
        self.hierarchy = None
        visualLayout = QtWidgets.QHBoxLayout()

        self.filterWidget = FilterWidget()

        self.queryScene = QtWidgets.QGraphicsScene()
        self.queryView = QtWidgets.QGraphicsView(self.queryScene)
        self.queryView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.queryView.customContextMenuRequested.connect(self.showMenu)

        visualLayout.addWidget(self.queryView)
        visualLayout.addWidget(self.filterWidget)

        self.setLayout(visualLayout)

    def showMenu(self, pos):

        menu = QtWidgets.QMenu()
        items = self.queryView.items(pos)
        if not items:
            return
        previous_action = QtWidgets.QAction('Add previous annotation', self)
        following_action = QtWidgets.QAction('Add following annotation', self)

        menu.addAction(previous_action)
        menu.addAction(following_action)

        action = menu.exec_(self.mapToGlobal(pos))
        if action == previous_action:
            new_pos = items[0].linear_position - 1
        elif action == following_action:
            new_pos = items[0].linear_position + 1
        else:
            return
        self.addNew(items[0].toPlainText(), new_pos)

    def addNew(self, text, pos):
        for i, at in enumerate(self.hierarchy.highest_to_lowest):
            if at == text:
                break
        ar = AnnotationRect(text, self.hierarchy)
        ar.clicked.connect(self.filterWidget.updateAnnotation)
        ar.setPos(self.horz_step * pos, self.vert_step*i)

        br = ar.boundingRect()
        br.setWidth(br.width() + self.vert_step*i)
        self.queryScene.addItem(ar)

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy
        self.filterWidget.setHierarchy(hierarchy)
        self.queryScene.clear()

        for i, at in enumerate(hierarchy.highest_to_lowest):
            ar = AnnotationRect(at, hierarchy)
            ar.clicked.connect(self.filterWidget.updateAnnotation)
            ar.setPos(0, self.vert_step*i)
            br = ar.boundingRect()
            br.setWidth(br.width() + self.vert_step*i)
            self.queryScene.addItem(ar)

class QueryForm(QtWidgets.QWidget):
    finishedRunning = QtCore.pyqtSignal(object)
    def __init__(self):
        super(QueryForm, self).__init__()
        self.config = None

        mainLayout = QtWidgets.QVBoxLayout()
        headerLayout = QtWidgets.QHBoxLayout()

        self.graphicalQuery = GraphicalQuery()


        self.linguisticSelect = QtWidgets.QComboBox()
        self.querySelect = QtWidgets.QComboBox()
        self.querySelect.addItem('Lab 1 stops')
        self.querySelect.addItem('Lab 2 stops')
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
                            w_type.transcription.column_name('Transcription'),
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
