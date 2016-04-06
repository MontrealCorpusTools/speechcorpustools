
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
            for p in c.inventory.all():
                self.selectWidget.addItem(p)
        layout.addWidget(self.selectWidget)
        self.setLayout(layout)

        self.selectWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

    def value(self):
        phones = [x.text() for x in self.selectWidget.selectedItems()]
        return phones

