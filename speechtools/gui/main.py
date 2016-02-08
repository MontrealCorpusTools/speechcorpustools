import os
import pickle

from PyQt5 import QtGui, QtCore, QtWidgets
import PyQt5
import vispy

from polyglotdb.config import BASE_DIR, CorpusConfig

from speechtools.corpus import CorpusContext

from .widgets import (ConnectWidget as PGConnectWidget, ViewWidget, ImportWidget, ExportWidget,
                        HelpWidget, DiscourseWidget, QueryWidget, CollapsibleWidgetPair,
                        get_system_font_height, DetailsWidget)

from .workers import AudioFinderWorker, AudioCheckerWorker

sct_config_pickle_path = os.path.join(BASE_DIR, 'config')

class ConnectWidget(PGConnectWidget):
    def __init__(self, *args, **kwargs):
        self.audioLookupButton = QtWidgets.QPushButton('Find audio')
        self.audioLookupButton.setEnabled(True)
        super(ConnectWidget, self).__init__(*args, **kwargs)
        self.formlayout.addRow(self.audioLookupButton)

        self.audioLookupButton.clicked.connect(self.findAudio)

        self.corporaList.selectionChanged.connect(self.enableFindAudio)

        self.checkerWorker = AudioCheckerWorker()
        self.checkerWorker.dataReady.connect(self.enableFindAudio)

        self.finderWorker = AudioFinderWorker()
        self.finderWorker.dataReady.connect(self.doneFinding)

    def connectToServer(self, ignore = False):
        super(ConnectWidget, self).connectToServer(ignore)
        self.checkAudio()

    def enableFindAudio(self, all_found):
        if not isinstance(all_found, str):
            self.audioLookupButton.setEnabled(False)
            self.audioLookupButton.setText('Audio available')
        else:
            self.audioLookupButton.setText('Find local audio files')
            self.audioLookupButton.setEnabled(True)

    def createConfig(self):
        name = self.corporaList.text()
        if name is None:
            return None
        host = self.hostEdit.text()
        port = self.portEdit.text()
        user = self.userEdit.text()
        password = self.passwordEdit.text()
        return CorpusConfig(name, graph_host = host, graph_port = port,
                        graph_user = user, graph_password = password)

    def checkAudio(self):
        config = self.createConfig()
        if config is None:
            self.audioLookupButton.setEnabled(False)
            self.audioLookupButton.setText('Select a corpus')
        else:
            kwargs = {}
            kwargs['config'] = config
            self.checkerWorker.setParams(kwargs)
            self.checkerWorker.start()

    def findAudio(self):
        if self.corporaList.text() is not None:
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory is None:
                return
            kwargs = {}
            kwargs['config'] = self.createConfig()
            kwargs['directory'] = directory
            self.audioLookupButton.setText('Searching...')
            self.audioLookupButton.setEnabled(False)
            self.finderWorker.setParams(kwargs)
            self.finderWorker.start()

    def doneFinding(self, success):
        if success:
            self.audioLookupButton.setText('Audio found')
            self.audioLookupButton.setEnabled(False)
        else:
            self.audioLookupButton.setText('Find local audio files')
            self.setEnabled(True)


class LeftPane(QtWidgets.QWidget):
    def __init__(self):
        super(LeftPane, self).__init__()


        self.viewWidget = ViewWidget()
        self.queryWidget = QueryWidget()

        splitter = CollapsibleWidgetPair(QtCore.Qt.Vertical, self.queryWidget, self.viewWidget, collapsible = 0)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def updateConfig(self, config):
        self.viewWidget.updateConfig(config)
        self.queryWidget.updateConfig(config)

    def changeDiscourse(self, discourse):
        self.viewWidget.changeDiscourse(discourse)

class RightPane(QtWidgets.QWidget):
    configUpdated = QtCore.pyqtSignal(object)
    discourseChanged = QtCore.pyqtSignal(str)
    def __init__(self):
        super(RightPane, self).__init__()


        if os.path.exists(sct_config_pickle_path):
            with open(sct_config_pickle_path, 'rb') as f:
                config = pickle.load(f)
        else:
            config = None
        self.connectWidget = ConnectWidget(config = config)
        self.connectWidget.configChanged.connect(self.configUpdated.emit)
        self.discourseWidget = DiscourseWidget()
        self.configUpdated.connect(self.discourseWidget.updateConfig)
        self.discourseWidget.discourseChanged.connect(self.discourseChanged.emit)
        self.helpWidget = HelpWidget()
        self.detailsWidget = DetailsWidget()
        upper = QtWidgets.QTabWidget()

        upper.addTab(self.connectWidget,'Connection')
        upper.addTab(self.discourseWidget, 'Discourses')

        lower = QtWidgets.QTabWidget()

        lower.addTab(self.detailsWidget, 'Details')

        lower.addTab(self.helpWidget, 'Help')

        splitter = CollapsibleWidgetPair(QtCore.Qt.Vertical, upper, lower)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

class MainWindow(QtWidgets.QMainWindow):
    configUpdated = QtCore.pyqtSignal(object)
    def __init__(self, app):
        super(MainWindow, self).__init__()
        vispy.sys_info(os.path.join(BASE_DIR, 'vispy.info'), overwrite = True)
        self.corpusConfig = None
        #self.connectWidget = ConnectWidget(self)
        #self.connectWidget.configChanged.connect(self.updateConfig)
        #self.viewWidget = ViewWidget(self)
        #self.importWidget = ImportWidget(self)
        #self.exportWidget = ExportWidget(self)

        self.leftPane = LeftPane()
        self.configUpdated.connect(self.leftPane.updateConfig)
        self.leftPane.viewWidget.connectionIssues.connect(self.havingConnectionIssues)

        self.rightPane = RightPane()
        self.rightPane.configUpdated.connect(self.updateConfig)
        self.rightPane.discourseChanged.connect(self.leftPane.changeDiscourse)

        self.leftPane.queryWidget.viewRequested.connect(self.rightPane.discourseWidget.changeView)
        self.rightPane.discourseWidget.viewRequested.connect(self.leftPane.viewWidget.discourseWidget.changeView)
        self.leftPane.viewWidget.discourseWidget.nextRequested.connect(self.leftPane.queryWidget.requestNext)
        self.leftPane.viewWidget.discourseWidget.previousRequested.connect(self.leftPane.queryWidget.requestPrevious)
        self.leftPane.viewWidget.discourseWidget.markedAsAnnotated.connect(self.leftPane.queryWidget.markAnnotated)
        self.leftPane.viewWidget.discourseWidget.selectionChanged.connect(self.rightPane.detailsWidget.showDetails)
        self.mainWidget = CollapsibleWidgetPair(QtCore.Qt.Horizontal, self.leftPane,self.rightPane)

        #self.mainWidget.setStretchFactor(0, 1)


        self.wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.mainWidget)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)

        self.status = QtWidgets.QLabel()
        self.statusBar().addWidget(self.status, stretch=1)
        self.connectionStatus = QtWidgets.QLabel()
        self.statusBar().addWidget(self.connectionStatus)
        self.setWindowTitle("Speech Corpus Tools")
        self.createActions()
        self.createMenus()

        self.updateStatus()

        if os.path.exists(sct_config_pickle_path):
            self.rightPane.connectWidget.connectToServer(ignore=True)

    def havingConnectionIssues(self):
        size = get_system_font_height()
        self.connectionStatus.setPixmap(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning).pixmap(size, size))
        self.connectionStatus.setToolTip('Having connection issues...')

    def updateConfig(self, config):
        self.corpusConfig = config
        self.updateStatus()
        self.configUpdated.emit(self.corpusConfig)

    def updateStatus(self):
        if self.corpusConfig is None:
            self.status.setText('No connection')
            size = get_system_font_height()
            self.connectionStatus.setPixmap(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical).pixmap(size, size))
            self.connectionStatus.setToolTip('No connection')

        else:
            c_name = self.corpusConfig.corpus_name
            if not c_name:
                c_name = 'No corpus selected'
            self.status.setText('Connected to {} ({})'.format(self.corpusConfig.graph_hostname, c_name))
            size = get_system_font_height()
            self.connectionStatus.setPixmap(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton).pixmap(size, size))
            self.connectionStatus.setToolTip('Connected!')

    def closeEvent(self, event):
        if self.corpusConfig is not None:
            with open(sct_config_pickle_path, 'wb') as f:
                pickle.dump(self.corpusConfig, f)
        super(MainWindow, self).closeEvent(event)

    def createActions(self):

        self.connectAct = QtWidgets.QAction( "Connect to corpus...",
                self,
                statusTip="Connect to a corpus", triggered=self.connect)

        self.importAct = QtWidgets.QAction( "Import a  corpus...",
                self,
                statusTip="Import a corpus", triggered=self.importCorpus)

        self.specifyAct = QtWidgets.QAction( "Add phonological features...",
                self,
                statusTip="Specify a corpus", triggered=self.specifyCorpus)

        self.exportAct = QtWidgets.QAction( "Export a  corpus...",
                self,
                statusTip="Export a corpus", triggered=self.exportCorpus)

    def createMenus(self):
        self.corpusMenu = self.menuBar().addMenu("Corpus")
        self.corpusMenu.addAction(self.connectAct)

        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.importAct)
        self.corpusMenu.addAction(self.specifyAct)
        self.corpusMenu.addAction(self.exportAct)

    def connect(self):
        pass

    def importCorpus(self):
        pass

    def specifyCorpus(self):
        pass

    def exportCorpus(self):
        pass
