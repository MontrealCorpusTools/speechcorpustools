
from PyQt5 import QtGui, QtCore, QtWidgets

from .helper import get_system_font_height

class SCTProgressBar(QtWidgets.QWidget):
    def __init__(self, parent, worker):
        super(SCTProgressBar, self).__init__(parent)
        self.progressBar = QtWidgets.QProgressBar()
        self.label = QtWidgets.QLabel()
        self.worker = worker
        self.worker.updateProgress.connect(self.progressBar.setValue)
        self.worker.updateMaximum.connect(self.progressBar.setMaximum)
        self.worker.updateProgressText.connect(self.label.setText)
        self.worker.dataReady.connect(self.detachAll)

        pglayout = QtWidgets.QHBoxLayout()

        self.cancelButton = QtWidgets.QPushButton()
        size = get_system_font_height()
        self.cancelButton.setIcon(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton))
        self.cancelButton.clicked.connect(self.cancelWorker)
        self.worker.finishedCancelling.connect(self.finishCancelling)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        pglayout.addWidget(self.progressBar)
        pglayout.addWidget(self.cancelButton)
        layout.addLayout(pglayout)
        self.setLayout(layout)

    def cancelWorker(self):
        self.cancelButton.setEnabled(False)
        self.label.setText('Cancelling...')
        self.worker.stop()

    def finishCancelling(self):
        self.label.setText('Cancelled')

    def detachAll(self):
        self.worker.updateProgress.disconnect(self.progressBar.setValue)
        self.worker.updateMaximum.disconnect(self.progressBar.setMaximum)
        self.worker.updateProgressText.disconnect(self.label.setText)
        self.worker.dataReady.disconnect(self.detachAll)
        self.cancel.clicked.disconnect(self.worker.stop)
        self.worker = None

class ProgressWidget(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super(ProgressWidget, self).__init__(parent)
        self.progressBars = {}

        self.mainLayout = QtWidgets.QVBoxLayout()

        self.setLayout(self.mainLayout)

        self.setWindowTitle('Progress bars')

    def createProgressBar(self, key, worker):
        pb = SCTProgressBar(self, worker)
        self.progressBars[key] = pb
        self.mainLayout.addWidget(pb)

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()
