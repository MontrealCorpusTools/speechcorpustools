
from PyQt5 import QtGui, QtCore, QtWidgets

def make_safe(data):
    if isinstance(data,float):
        data = str(round(data, 3))
    elif isinstance(data,bool):
        if data:
            data = 'Yes'
        else:
            data = 'No'
    elif isinstance(data,(list, tuple)):
        data = ', '.join(make_safe(x) for x in data)
    else:
        data = str(data)
    return data

class QueryResultsModel(QtCore.QAbstractTableModel):
    SortRole = 999
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
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return col
        return None

    def times(self, index):
        row = index.row()
        result = self.rows[row]

        return result.Begin, result.End

    def markRowAsAnnotated(self, row, value):
        if value is None:
            current = self.rows[row]['Annotated']
            value = not current
        setattr(self.rows[row], 'Annotated', value)
        beg = self.index(row, 0)
        end = self.index(row, len(self.columns) - 1)
        self.dataChanged.emit(beg, end)

    def discourse(self, index):
        row = index.row()
        result = self.rows[row]

        return result.Discourse

    def data(self, index, role = None):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        col = self.columns[col]

        if role == QtCore.Qt.DisplayRole:
            try:
                data = self.rows[row][col]
                data = make_safe(data)
            except IndexError:
                data = ''

            return data
        elif role == self.SortRole:
            data = self.rows[row][col]
            if isinstance(data, (tuple,list)):
                if len(data):
                    data = data[0]
                else:
                    return None
            return data
        return None

class ProxyModel(QtCore.QSortFilterProxyModel):
    # Adapted from http://stackoverflow.com/questions/15111965/qsortfilterproxymodel-and-row-numbers
    def headerData(self, section, orientation, role):
        # if display role of vertical headers
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            # return the actual row number
            return section + 1
        # for other cases, rely on the base implementation
        return super(ProxyModel, self).headerData(section, orientation, role)

