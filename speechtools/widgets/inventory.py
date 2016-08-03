
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

class PhoneSubsetSelectWidget(QtWidgets.QWidget):
    def __init__(self, config, parent = None):
        super(PhoneSubsetSelectWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()
        self.subsetSelect = QtWidgets.QComboBox()
        with CorpusContext(config) as c:
            try:
                for s in c.hierarchy.subset_types[c.phone_name]:
                    self.subsetSelect.addItem(s)
            except KeyError:
                pass

        layout.addWidget(self.subsetSelect)

        self.setLayout(layout)

    def value(self):
        return self.subsetSelect.currentText()

class PhoneSelectWidget(QtWidgets.QWidget):
    def __init__(self, config, parent = None):
        super(PhoneSelectWidget, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.selectWidget = QtWidgets.QListWidget()
        self.selectWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        with CorpusContext(config) as c:
            for p in c.lexicon.phones():
                self.selectWidget.addItem(p)
        layout.addWidget(self.selectWidget)
        self.setLayout(layout)

        self.selectWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

    def value(self):
        phones = [x.text() for x in self.selectWidget.selectedItems()]
        return phones

class RegexPhoneSelectWidget(QtWidgets.QWidget):
    def __init__(self, config, parent = None):
        super(RegexPhoneSelectWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()
        vlayout1 = QtWidgets.QVBoxLayout()
        vlayout2 = QtWidgets.QVBoxLayout()

        vowelLabel = QtWidgets.QLabel()
        endingLabel = QtWidgets.QLabel()

        vowelLabel.setText('full vowel')
        endingLabel.setText('stress/tone ending')

        self.selectWidget = QtWidgets.QListWidget()
        self.selectWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        self.secondSelect = QtWidgets.QListWidget()
        self.secondSelect.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        vlayout1.addWidget(vowelLabel)
        vlayout1.addWidget(self.selectWidget)
        vlayout2.addWidget(endingLabel)
        vlayout2.addWidget(self.secondSelect)

        layout.addLayout(vlayout1)
        layout.addLayout(vlayout2)

       

        self.setLayout(layout)

        self.selectWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)





