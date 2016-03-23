import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum, Count

from ..base import NonScrollingComboBox

class AttributeSelect(QtWidgets.QComboBox):
    def __init__(self, hierarchy, to_find):
        super(AttributeSelect, self).__init__()
        self.types = []
        for k,t in sorted(hierarchy.token_properties[to_find]):
            self.addItem(k)
            self.types.append(t)
        for k,t in sorted(hierarchy.type_properties[to_find]):
            self.addItem(k)
            self.types.append(t)
        for k in hierarchy.highest_to_lowest:
            if k != to_find:
                self.addItem(k)
                self.types.append(None)
        self.addItem('speaker')
        self.types.append(None)
        self.addItem('discourse')
        self.types.append(None)
        if to_find in hierarchy.subannotations:
            for s in sorted(hierarchy.subannotations[to_find]):
                self.addItem(s)
                self.types.append(None)

    def type(self):
        index = self.currentIndex()
        return self.types[index]

class AttributeWidget(QtWidgets.QWidget):
    attributeTypeChanged = QtCore.pyqtSignal(object)
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(AttributeWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.initWidget()

        self.setLayout(self.mainLayout)

    def initWidget(self):
        while self.mainLayout.count():
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        self.baseSelect = AttributeSelect(self.hierarchy, self.to_find)
        self.baseSelect.currentIndexChanged.connect(self.updateAttribute)

        self.mainLayout.addWidget(self.baseSelect)

    def setToFind(self, to_find):
        self.to_find = to_find
        self.initWidget()

    def updateAttribute(self):
        combobox = self.sender()
        index = self.mainLayout.indexOf(combobox)
        while self.mainLayout.count() - 1 > index:
            item = self.mainLayout.takeAt(self.mainLayout.count() - 1)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        if combobox.currentText() in self.hierarchy.annotation_types:
            widget = AttributeSelect(self.hierarchy, combobox.currentText())
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        self.attributeTypeChanged.emit(combobox.type())

class ValueWidget(QtWidgets.QWidget):
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(ValueWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()

        self.setLayout(self.mainLayout)

        self.compWidget = None
        self.valueWidget = None

    def changeType(self, new_type):
        while self.mainLayout.count():
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        self.compWidget = QtWidgets.QComboBox()
        if new_type == 'node':
            self.compWidget.addItem('Right aligned to')
            self.compWidget.addItem('Left aligned to')
            self.compWidget.addItem('Not right aligned to')
            self.compWidget.addItem('Not left aligned to')
            self.valueWidget = AttributeWidget(self.hierarchy, self.to_find)
        elif new_type in (int, float):
            self.compWidget.addItem('=')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('>')
            self.compWidget.addItem('>=')
            self.compWidget.addItem('<')
            self.compWidget.addItem('<=')
            self.valueWidget = QtWidgets.QLineEdit()
        elif new_type == str:
            self.compWidget.addItem('=')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('in')
            self.compWidget.addItem('not in')
            self.valueWidget = QtWidgets.QLineEdit()
        elif new_type == bool:
            self.compWidget.addItem('=')
            self.valueWidget = QtWidgets.QComboBox()
            self.valueWidget.addItem('True')
            self.valueWidget.addItem('False')
            self.valueWidget.addItem('Null')
        if new_type != bool:
            self.mainLayout.addWidget(self.compWidget)
        self.mainLayout.addWidget(self.valueWidget)
        if new_type is not None:
            self.switchWidget = QtWidgets.QPushButton('Switch')
            self.mainLayout.addWidget(self.switchWidget)

    def setToFind(self, to_find):
        self.to_find = to_find
        if isinstance(self.valueWidget, AttributeWidget):
            self.valueWidget.setToFind(to_find)

class FilterWidget(QtWidgets.QWidget):
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(FilterWidget, self).__init__()

        mainLayout = QtWidgets.QHBoxLayout()

        self.attributeWidget = AttributeWidget(self.hierarchy, self.to_find)
        mainLayout.addWidget(self.attributeWidget)

        self.valueWidget = ValueWidget(self.hierarchy, self.to_find)
        mainLayout.addWidget(self.valueWidget)
        self.setLayout(mainLayout)

        self.attributeWidget.attributeTypeChanged.connect(self.valueWidget.changeType)

    def setToFind(self, to_find):
        self.to_find = to_find
        self.attributeWidget.setToFind(to_find)
        self.valueWidget.setToFind(to_find)

class FilterBox(QtWidgets.QGroupBox):
    def __init__(self):
        super(FilterBox, self).__init__('Filters')
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.hierarchy = None
        self.to_find = None
        self.addButton = QtWidgets.QPushButton('+')
        self.addButton.clicked.connect(self.addNewFilter)
        self.addButton.setEnabled(False)
        self.mainLayout.addWidget(self.addButton)
        self.setLayout(self.mainLayout)

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy
        self.addButton.setEnabled(True)

    def setToFind(self, to_find):
        self.to_find = to_find
        for i in range(self.mainLayout.count() - 1):
            self.mainLayout.itemAt(i).widget().setToFind(to_find)

    def addNewFilter(self):
        if self.hierarchy is None:
            return
        widget = FilterWidget(self.hierarchy, self.to_find)
        self.mainLayout.insertWidget(self.mainLayout.count() - 1, widget)

class BasicQuery(QtWidgets.QWidget):
    def __init__(self):
        super(BasicQuery, self).__init__()
        self.hierarchy = None
        mainLayout = QtWidgets.QVBoxLayout()
        self.toFindWidget = QtWidgets.QComboBox()
        self.toFindWidget.currentIndexChanged.connect(self.updateToFind)

        self.filterWidget = FilterBox()

        mainLayout.addWidget(self.toFindWidget)
        mainLayout.addWidget(self.filterWidget)

        self.setLayout(mainLayout)


    def updateToFind(self):
        to_find = self.toFindWidget.currentText()
        self.filterWidget.setToFind(to_find)

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy
        self.filterWidget.setHierarchy(hierarchy)
        self.toFindWidget.clear()

        self.toFindWidget.currentIndexChanged.disconnect(self.updateToFind)
        for i, at in enumerate(hierarchy.highest_to_lowest):
            self.toFindWidget.addItem(at)
        self.toFindWidget.currentIndexChanged.connect(self.updateToFind)
        self.updateToFind()

