
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


class StressToneSelectWidget(QtWidgets.QWidget):
    def __init__(self,config,parent=None):
        super(StressToneSelectWidget, self).__init__(parent)

        layout = QtWidgets.QFormLayout()
        rowLayout = QtWidgets.QHBoxLayout()
        vlayout1 = QtWidgets.QVBoxLayout()
        vlayout2 = QtWidgets.QVBoxLayout()
        vowelLabel = QtWidgets.QLabel()
        regexLabel = QtWidgets.QLabel()

        vowelLabel.setText('vowel')
        regexLabel.setText('stress/tone ending')

        self.regexWidget = RegexWidget(config)
        self.vowelRegexWidget = RegexWidget(config)
        self.vowelRegexWidget.testButton.setParent(None)
        
        vlayout1.addWidget(vowelLabel)
        vlayout1.addWidget(self.vowelRegexWidget)
        vlayout2.addWidget(regexLabel)
        vlayout2.addWidget(self.regexWidget)
        
        rowLayout.addLayout(vlayout1)
        rowLayout.addLayout(vlayout2)

        layout.addRow(rowLayout)

        self.setLayout(layout)

    def value(self):
        return self.regexWidget.value()

    def combo_value(self):
        return self.vowelRegexWidget.value()+self.regexWidget.value()