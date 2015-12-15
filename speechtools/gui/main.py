

from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.gui.main import MainWindow as PGMainWindow

from .widgets import ViewWidget

class MainWindow(PGMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__(app)

        self.viewWidget = ViewWidget(self)
        self.configUpdated.connect(self.viewWidget.updateConfig)
        self.mainWidget.removeTab(0)
        self.mainWidget.insertTab(0, self.viewWidget, 'Current corpus')
