
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
            statement = 'MATCH (n:phone_type:{corpus_name}) RETURN n.label as label'.format(corpus_name=c.corpus_name)
            res = c.execute_cypher(statement)
            phones = []
            for item in res:
                phones.append(item['label'])
            phones = sorted(phones, key = lambda x : x[0])    
            for phone in phones:
                self.selectWidget.addItem(phone)
            #for p in c.lexicon.phones():
                #self.selectWidget.addItem(p)
        layout.addWidget(self.selectWidget)
        self.setLayout(layout)

        self.selectWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

    def value(self):
        phones = [x.text() for x in self.selectWidget.selectedItems()]
        return phones

class RegexPhoneSelectWidget(QtWidgets.QTableWidget):
    def __init__(self, data, x,y):
        QtWidgets.QTableWidget.__init__(self,y,x)
        self.data = data
        self.setdata()
        self.resizeRowsToContents()

    def setdata(self):
        
        headers = [col for col in self.data.keys()]

        for i, k in enumerate(self.data.keys()):
            for j, v in enumerate(self.data[k]):
                item = QtWidgets.QTableWidgetItem(v)
                self.setItem(j,i,item)
        self.setHorizontalHeaderLabels(headers)




