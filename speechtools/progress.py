
from PyQt5 import QtGui, QtCore, QtWidgets

from .helper import get_system_font_height

class SCTProgressBar(QtWidgets.QWidget):
    removeThis = QtCore.pyqtSignal()
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
        self.cancelButton.setIcon(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.cancelButton.clicked.connect(self.cancelWorker)
        self.worker.finishedCancelling.connect(self.finishCancelling)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        pglayout.addWidget(self.progressBar)
        pglayout.addWidget(self.cancelButton)
        layout.addLayout(pglayout)
        self.setLayout(layout)
        self.detached = False

    def cancelWorker(self):
        if not self.detached:
            self.cancelButton.setEnabled(False)
            self.label.setText('Cancelling...')
            self.worker.stop()
        else:
            self.removeThis.emit()

    def finishCancelling(self):
        self.cancelButton.setEnabled(True)
        self.label.setText('Cancelled')
        self.detachAll(cancelled = True)

    def detachAll(self, *args, cancelled = False):
        if not cancelled:
            self.progressBar.setValue(self.progressBar.maximum())
            self.label.setText('Finished!')
        try:
            self.worker.updateProgress.disconnect(self.progressBar.setValue)
        except TypeError:
            pass
        try:
            self.worker.updateMaximum.disconnect(self.progressBar.setMaximum)
        except TypeError:
            pass
        try:
            self.worker.updateProgressText.disconnect(self.label.setText)
        except TypeError:
            pass
        try:
            self.worker.dataReady.disconnect(self.detachAll)
        except TypeError:
            pass
        try:
            self.cancelButton.clicked.disconnect(self.worker.stop)
        except TypeError:
            pass
        self.worker = None
        self.detached = True

class ProgressWidget(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super(ProgressWidget, self).__init__(parent)
        self.progressBars = {}

        self.mainLayout = QtWidgets.QVBoxLayout()

        self.setLayout(self.mainLayout)

        self.setWindowTitle('Progress bars')

    def createProgressBar(self, key, worker):
        pb = SCTProgressBar(self, worker)
        pb.removeThis.connect(self.cleanup)
        #self.progressBars[key] = pb
        self.mainLayout.addWidget(pb)

    def cleanup(self):
        pb = self.sender()
        self.mainLayout.removeWidget(pb)
        pb.deleteLater()

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()
