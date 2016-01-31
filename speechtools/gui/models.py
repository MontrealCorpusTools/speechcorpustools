
from PyQt5 import QtGui, QtCore, QtWidgets


class QueryResultsModel(QtCore.QAbstractTableModel):
    def __init__(self, results, parent = None):
        self.columns = results.columns
        self.rows = results
        QtCore.QAbstractTableModel.__init__(self, parent)

    def rowCount(self, parent = None):
        return len(self.rows)

    def columnCount(self, parent = None):
        return len(self.columns)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.columns[col]
        return None

    def times(self, index):
        row = index.row()
        result = self.rows[row]

        return result.Begin, result.End

    def discourse(self, index):
        row = index.row()
        result = self.rows[row]

        return result.Discourse

    def data(self, index, role = None):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        row = index.row()
        col = index.column()
        try:
            data = self.rows[row][col]
            if isinstance(data,float):
                data = str(round(data, 3))
            elif isinstance(data,bool):
                if data:
                    data = 'Yes'
                else:
                    data = 'No'
            elif isinstance(data,(list, tuple)):
                data = ', '.join(data)
            else:
                data = str(data)
        except IndexError:
            data = ''

        return data
