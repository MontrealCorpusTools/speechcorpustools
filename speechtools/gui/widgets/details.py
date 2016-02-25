
from PyQt5 import QtGui, QtCore, QtWidgets

class DetailsWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(DetailsWidget, self).__init__(parent)

        self.detailLayout = QtWidgets.QFormLayout()

        self.detailLayout.addRow(QtWidgets.QLabel('Please select an annotation'))

        self.setLayout(self.detailLayout)

    def showDetails(self, annotation):
        while self.detailLayout.count():
            item = self.detailLayout.takeAt(0)
            item.widget().deleteLater()
        if annotation is None:
            self.detailLayout.addRow(QtWidgets.QLabel('Please select an annotation'))
            return
        self.detailLayout.addRow('Label', QtWidgets.QLabel(annotation.label))
        self.detailLayout.addRow('Begin', QtWidgets.QLabel(str(round(annotation.begin, 3))))
        self.detailLayout.addRow('End', QtWidgets.QLabel(str(round(annotation.end, 3))))
        for k in sorted(annotation.node.properties.keys()):
            if k in ['label', 'begin', 'end']:
                continue
            v = annotation.node.properties[k]
            if k == 'checked':
                k = 'annotated'
            self.detailLayout.addRow(k.title(), QtWidgets.QLabel(str(v)))
        self.update()

class AcousticDetailsWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(AcousticDetailsWidget, self).__init__(parent)

        self.detailLayout = QtWidgets.QFormLayout()

        self.setLayout(self.detailLayout)

    def showDetails(self, acoustics):
        while self.detailLayout.count():
            item = self.detailLayout.takeAt(0)
            item.widget().deleteLater()
        if acoustics is None:
            return
        for k,v in sorted(acoustics.items()):
            if v is None:
                v = 'unknown'
            else:
                if v < 0:
                    v = 'unvoiced'
                else:
                    v = str(round(v, 3))
            self.detailLayout.addRow(k, QtWidgets.QLabel(v))
        self.update()
