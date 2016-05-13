
from PyQt5 import QtGui, QtCore, QtWidgets

class RegexWidget(QtWidgets.QWidget):
    def __init__(self, config, parent = None):
        super(RegexWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()

        self.regexEdit = QtWidgets.QLineEdit()
        self.regexEdit.setText('^[<{].*$')

        self.testButton = QtWidgets.QPushButton('Test regex')

        layout.addWidget(self.regexEdit)
        layout.addWidget(self.testButton)

        self.setLayout(layout)

    def value(self):
        return self.regexEdit.text()

class WordSelectWidget(QtWidgets.QWidget):
    def __init__(self, config, parent = None):
        super(WordSelectWidget, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.regexWidget = RegexWidget(config)
        layout.addRow('Specify regex', self.regexWidget)

        self.setLayout(layout)

    def value(self):
        return self.regexWidget.value()
