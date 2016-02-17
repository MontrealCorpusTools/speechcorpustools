
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.config import CorpusConfig
from polyglotdb.exceptions import (ConnectionError, PGError,
                            AuthorizationError,NetworkAddressError)
from polyglotdb.corpus import get_corpora_list

from ..workers import AudioFinderWorker, AudioCheckerWorker

class CorporaList(QtWidgets.QGroupBox):
    selectionChanged = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        super(CorporaList, self).__init__('Available corpora', parent)
        layout = QtWidgets.QVBoxLayout()

        self.corporaList = QtWidgets.QListWidget()
        self.corporaList.itemSelectionChanged.connect(self.changed)
        layout.addWidget(self.corporaList)
        self.setLayout(layout)

    def clear(self):
        self.corporaList.clear()

    def add(self, items):
        for i in items:
            self.corporaList.addItem(i)

    def changed(self):
        c = self.text()
        if c is None:
            c = ''
        self.selectionChanged.emit(c)

    def text(self):
        sel = self.corporaList.selectedItems()
        if not sel:
            return None
        return sel[0].text()

class ConnectWidget(QtWidgets.QWidget):
    configChanged = QtCore.pyqtSignal(object)
    def __init__(self, config = None, parent = None):
        super(ConnectWidget, self).__init__(parent)
        self.audioLookupButton = QtWidgets.QPushButton('Find audio')
        self.audioLookupButton.setEnabled(True)

        layout = QtWidgets.QHBoxLayout()
        self.formlayout = QtWidgets.QFormLayout()

        self.hostEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.hostEdit.setText(config.graph_host)
        else:
            self.hostEdit.setText('localhost')
        self.portEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.portEdit.setText(str(config.graph_port))
        else:
            self.portEdit.setText('7474')
        self.userEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.userEdit.setText(config.graph_user)
        self.passwordEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.passwordEdit.setText(config.graph_password)
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)

        self.formlayout.addRow('IP address (or localhost)', self.hostEdit)
        self.formlayout.addRow('Port', self.portEdit)
        self.formlayout.addRow('Username (optional)', self.userEdit)
        self.formlayout.addRow('Password (optional)', self.passwordEdit)

        connectButton = QtWidgets.QPushButton('Connect')
        connectButton.clicked.connect(self.connectToServer)

        self.hostEdit.returnPressed.connect(connectButton.click)
        self.portEdit.returnPressed.connect(connectButton.click)
        self.userEdit.returnPressed.connect(connectButton.click)
        self.passwordEdit.returnPressed.connect(connectButton.click)
        self.formlayout.addRow(connectButton)

        layout.addLayout(self.formlayout)

        self.corporaList = CorporaList()
        self.corporaList.selectionChanged.connect(self.changeConfig)
        layout.addWidget(self.corporaList)

        self.setLayout(layout)
        if config is not None:
            self.connectToServer()

        self.formlayout.addRow(self.audioLookupButton)

        self.audioLookupButton.clicked.connect(self.findAudio)

        self.corporaList.selectionChanged.connect(self.enableFindAudio)

        self.checkerWorker = AudioCheckerWorker()
        self.checkerWorker.dataReady.connect(self.enableFindAudio)

        self.finderWorker = AudioFinderWorker()
        self.finderWorker.dataReady.connect(self.doneFinding)

    def connectToServer(self, ignore = False):
        host = self.hostEdit.text()
        if host == '':
            if not ignore:
                reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information", "IP address must be specified or named 'localhost'.")
            return
        port = self.portEdit.text()
        try:
            port = int(port)
        except ValueError:
            if not ignore:
                reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information", "Port must be an integer.")
            return
        user = self.userEdit.text()
        if not user:
            user = None
        password = self.passwordEdit.text()
        if not password:
            password = None
        config = CorpusConfig('', graph_host = host, graph_port = port,
                        graph_user = user, graph_password = password)
        self.corporaList.clear()
        try:
            corpora = get_corpora_list(config)
            self.corporaList.add(corpora)
            self.configChanged.emit(config)
        except (ConnectionError, AuthorizationError, NetworkAddressError) as e:
            self.configChanged.emit(None)
            if not ignore:
                reply = QtWidgets.QMessageBox.critical(self,
                    "Could not connect to server", str(e))
            return
        self.checkAudio()

    def changeConfig(self, name):
        host = self.hostEdit.text()
        port = self.portEdit.text()
        user = self.userEdit.text()
        password = self.passwordEdit.text()
        config = CorpusConfig(name, graph_host = host, graph_port = port,
                        graph_user = user, graph_password = password)
        self.configChanged.emit(config)

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
