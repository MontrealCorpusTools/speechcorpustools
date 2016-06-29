
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
        self.worker.dataReady.connect(self.finish)

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
        self.done = False

    def cancelWorker(self):
        if not self.done:
            self.cancelButton.setEnabled(False)
            self.label.setText('Cancelling...')
            self.worker.stop()
        else:
            self.hide()
            #self.removeThis.emit()

    def finishCancelling(self):
        self.cancelButton.setEnabled(True)
        self.label.setText('Cancelled')
        self.done = True

    def finish(self):
        self.done = True
        self.label.setText('Finished!')
        if self.progressBar.maximum() == 0:
            self.progressBar.setMaximum(1)
        self.progressBar.setValue(self.progressBar.maximum())

class ProgressWidget(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super(ProgressWidget, self).__init__(parent)
        self.progressBars = {}

        self.mainLayout = QtWidgets.QVBoxLayout()

        self.setLayout(self.mainLayout)

        self.setWindowTitle('Progress bars')

    def createProgressBar(self, key, worker):
        if key in self.progressBars:
            self.progressBars[key].show()
            self.progressBars[key].done = False
        else:
            pb = SCTProgressBar(self, worker)
            self.progressBars[key] = pb
            self.mainLayout.addWidget(pb)

    def cleanup(self):
        pb = self.sender()
        self.mainLayout.removeWidget(pb)
        pb.deleteLater()

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()
