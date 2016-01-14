

from PyQt5 import QtGui, QtCore, QtWidgets

class ResultsView(QtWidgets.QTableView):
    def __init__(self, parent = None):
        super(ResultsView, self).__init__(parent)

        self.verticalHeader().hide()
        self.setSortingEnabled(True)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.clip = QtWidgets.QApplication.clipboard()

        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

    def keyPressEvent(self, e):
        if (e.modifiers() & QtCore.Qt.ControlModifier):
            selected = self.selectionModel().selectedRows()
            if e.key() == QtCore.Qt.Key_C: #copy
                s = ''

                for r in selected:
                    for c in range(self.model().columnCount()):
                        ind = self.model().index(r.row(),c)
                        s += self.model().data(ind, QtCore.Qt.DisplayRole) + "\t"
                    s = s[:-1] + "\n" #eliminate last '\t'
                self.clip.setText(s)

    def setModel(self,model):
        super(ResultsView, self).setModel(model)
