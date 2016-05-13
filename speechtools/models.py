
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
        if len(results) > 0:
            self.columns = [x for x in results[0].properties if x not in ['id']] + ['discourse', 'speaker']
        else:
            self.columns = ['label', 'begin', 'end', 'discourse', 'speaker']
        self.rows = results
        QtCore.QAbstractTableModel.__init__(self, parent)

        self.destroyed.connect(self.reset)

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

    def reset(self):
        del self.rows
        self.rows = []
        beg = self.index(0, 0)
        end = self.index(0, len(self.columns) - 1)
        self.dataChanged.emit(beg, end)

    def times(self, index):
        row = index.row()
        result = self.rows[row]

        return result.begin, result.end

    def markRowAsAnnotated(self, row, value):
        return
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

        return result.discourse.name

    def data(self, index, role = None):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        col = self.columns[col]

        if role == QtCore.Qt.DisplayRole:
            try:
                data = self.rows[row]
                if col == 'speaker':
                    data = data.speaker.name
                elif col == 'discourse':
                    data = data.discourse.name
                else:
                    data = getattr(data, col)
                data = make_safe(data)
            except IndexError:
                data = ''

            return data
        elif role == self.SortRole:
            data = self.rows[row]
            if col == 'speaker':
                data = data.speaker.name
            elif col == 'discourse':
                data = data.discourse.name
            else:
                data = getattr(data, col)
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

class DiscourseModel(object):
    dataChanged = QtCore.pyqtSignal(object)
    def __init__(self):
        self.config = None
        self.discourse = None
        self.visible_begin = None
        self.visible_end = None
        self.max_begin = None
        self.max_end

        self.annotation_list = []

        self.queryWorker

    def updateData(self, begin, end):
        kwargs = {'discourse':self.discourse, 'config': self.config}
        if self.max_begin is None:
            kwargs['begin'] = begin
            kwargs['end'] =  end

    def updateView(self, begin, end):
        if self.max_begin is not None and begin > self.max_begin and end < self.max_end:
            self.visible_begin = begin
            self.visible_end = end
            self.dataChanged.emit(filter(lambda x: x.end > self.visible_begin and x.begin < self.visible_end,
                            self.annotationList))
        else:
            self.updateData(begin, end)
