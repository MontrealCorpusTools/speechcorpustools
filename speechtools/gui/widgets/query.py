
from PyQt5 import QtGui, QtCore, QtWidgets

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
        self.executeButton = QtWidgets.QPushButton('Run query')
        self.executeButton.clicked.connect(self.runQuery)
        self.executeButton.setDisabled(True)
        headerLayout.addWidget(QtWidgets.QLabel('Linguistic type'))

        headerLayout.addWidget(self.linguisticSelect)
        headerLayout.addWidget(self.executeButton)

        mainLayout = QtWidgets.QVBoxLayout()
        if False:
            mainLayout.addLayout(headerLayout)

        phon4Layout = QtWidgets.QHBoxLayout()

        self.lab1Button = QtWidgets.QPushButton('Search for Lab 1 stops')
        self.lab1Button.setDisabled(True)
        self.lab1Button.clicked.connect(self.lab1Query)
        self.exportButton = QtWidgets.QPushButton('Export Lab 1 stops')
        self.exportButton.clicked.connect(self.runExportQuery)
        self.exportButton.setDisabled(True)

        phon4Layout.addWidget(self.lab1Button)
        phon4Layout.addWidget(self.exportButton)

        mainLayout.addLayout(phon4Layout)

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

    def lab1Query(self):
        if self.config is None:
            return
        kwargs = {}
        kwargs['config'] = self.config
        self.lab1Worker.setParams(kwargs)
        self.lab1Worker.start()

    def runExportQuery(self):
        if self.config is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export data", filter = "CSV (*.txt  *.csv)")

        if not path:
            return
        kwargs = {}
        kwargs['config'] = self.config
        kwargs['path'] = path
        self.exportWorker.setParams(kwargs)
        self.exportWorker.start()

    def runQuery(self):
        if self.config is None:
            return
        kwargs = {}
        kwargs['annotation_type'] = self.linguisticSelect.currentText()
        kwargs['config'] = self.config
        self.worker.setParams(kwargs)
        self.worker.start()

    def updateConfig(self, config):
        self.config = config
        self.linguisticSelect.clear()
        if self.config is None or self.config.corpus_name == '':
            self.executeButton.setDisabled(True)
            self.lab1Button.setDisabled(True)
            self.exportButton.setDisabled(True)
            return
        self.executeButton.setDisabled(False)
        self.lab1Button.setDisabled(False)
        self.exportButton.setDisabled(False)
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
