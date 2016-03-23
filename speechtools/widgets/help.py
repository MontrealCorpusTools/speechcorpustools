
from PyQt5 import QtGui, QtCore, QtWidgets

class HelpWidget(QtWidgets.QWidget):
    def __init__(self):
        super(HelpWidget, self).__init__()

        layout = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel('Placeholder help, kinda useless, oh well'))
        self.setLayout(layout)
