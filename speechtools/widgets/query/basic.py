import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum, Count

from ..base import NonScrollingComboBox

from ...profiles import QueryProfile, Filter

class AttributeSelect(QtWidgets.QComboBox):
    def __init__(self, hierarchy, to_find, alignment):
        super(AttributeSelect, self).__init__()
        if not alignment:
            self.addItem('alignment')
            self.addItem('subset')
            self.types = ['node','subset']
            for k,t in sorted(hierarchy.token_properties[to_find]):
                self.addItem(k)
                self.types.append(t)
            for k,t in sorted(hierarchy.type_properties[to_find]):
                self.addItem(k)
                self.types.append(t)
        else:
            self.types = []
        for k in hierarchy.highest_to_lowest:
            if k != to_find:
                self.addItem(k)
                self.types.append('annotation')
        if not alignment:
            self.addItem('speaker')
            self.types.append('speaker')
            self.addItem('discourse')
            self.types.append('discourse')
            if to_find in hierarchy.subannotations:
                for s in sorted(hierarchy.subannotations[to_find]):
                    self.addItem(s)
                    self.types.append('subannotation')

    def type(self):
        index = self.currentIndex()
        return self.types[index]

    def label(self):
        return self.currentText()

class AttributeWidget(QtWidgets.QWidget):
    attributeTypeChanged = QtCore.pyqtSignal(object, object)
    def __init__(self, hierarchy, to_find, alignment = False):
        self.hierarchy = hierarchy
        self.to_find = to_find
        self.alignment = alignment
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
        self.baseSelect = AttributeSelect(self.hierarchy, self.to_find, self.alignment)
        self.baseSelect.currentIndexChanged.connect(self.updateAttribute)

        self.mainLayout.addWidget(self.baseSelect)
        self.attributeTypeChanged.emit(self.to_find, self.baseSelect.type())

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
            widget = AttributeSelect(self.hierarchy, combobox.currentText(), self.alignment)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        annotation = self.to_find
        if index != 0:
            annotation = self.mainLayout.itemAt(index -1).widget().label()
        self.attributeTypeChanged.emit(annotation, combobox.type())

    def type(self):
        num = self.mainLayout.count()
        widget = self.mainLayout.itemAt(num - 1).widget()

        return widget.type()

    def attribute(self):
        att = [self.to_find]
        for i in range(self.mainLayout.count()):
            widget = self.mainLayout.itemAt(i).widget()
            if not isinstance(widget, AttributeSelect):
                continue
            text = widget.currentText()
            if text == 'alignment':
                continue
            att.append(text)
        return tuple(att)

    def setAttribute(self, attribute):
        print(attribute)
        self.initWidget()
        for a in attribute[1:]:
            ind = self.mainLayout.count() - 1
            widget = self.mainLayout.itemAt(ind).widget()
            widget.setCurrentIndex(widget.findText(a))
        annotation = self.to_find
        if self.mainLayout.count() > 1:
            annotation = self.mainLayout.itemAt(self.mainLayout.count() - 2).widget().label()
        self.attributeTypeChanged.emit(annotation, self.mainLayout.itemAt(self.mainLayout.count() - 1).widget().type())


class ValueWidget(QtWidgets.QWidget):
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(ValueWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()

        self.setLayout(self.mainLayout)

        self.compWidget = None
        self.valueWidget = None

    def changeType(self, annotation, new_type):
        print(new_type)
        while self.mainLayout.count():
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        self.compWidget = QtWidgets.QComboBox()
        if new_type == 'node' or new_type == 'annotation':
            self.compWidget.addItem('Right aligned with')
            self.compWidget.addItem('Left aligned with')
            self.compWidget.addItem('Not right aligned with')
            self.compWidget.addItem('Not left aligned with')
            self.valueWidget = AttributeWidget(self.hierarchy, self.to_find, alignment = True)
        elif new_type == 'subset':
            self.compWidget.addItem('==')
            self.valueWidget = QtWidgets.QComboBox()
            if annotation in self.hierarchy.subset_types:
                for s in self.hierarchy.subset_types[annotation]:
                    self.valueWidget.addItem(s)
            if annotation in self.hierarchy.subset_tokens:
                for s in self.hierarchy.subset_tokens[annotation]:
                    self.valueWidget.addItem(s)


        elif new_type == 'speaker':
            pass
        elif new_type == 'discourse':
            pass
        elif new_type in (int, float):
            self.compWidget.addItem('==')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('>')
            self.compWidget.addItem('>=')
            self.compWidget.addItem('<')
            self.compWidget.addItem('<=')
            self.valueWidget = QtWidgets.QLineEdit()
        elif new_type == str:
            self.compWidget.addItem('==')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('in')
            self.compWidget.addItem('not in')
            self.compWidget.addItem('regex')
            self.valueWidget = QtWidgets.QLineEdit()
        elif new_type == bool:
            self.compWidget.addItem('==')
            self.valueWidget = QtWidgets.QComboBox()
            self.valueWidget.addItem('True')
            self.valueWidget.addItem('False')
            self.valueWidget.addItem('Null')
        if new_type != bool:
            self.mainLayout.addWidget(self.compWidget)
        self.mainLayout.addWidget(self.valueWidget)
        if new_type in [int, float, str, bool]:
            self.switchWidget = QtWidgets.QPushButton('Switch')
            self.mainLayout.addWidget(self.switchWidget)

    def setToFind(self, to_find):
        self.to_find = to_find
        if isinstance(self.valueWidget, AttributeWidget):
            self.valueWidget.setToFind(to_find)

    def operator(self):
        text = self.compWidget.currentText()
        if 'aligned' in text:
            if 'not' in text:
                operator = '!='
            else:
                operator = '=='
        else:
            operator = text
        return operator

    def value(self):
        if isinstance(self.valueWidget, AttributeWidget):
            return self.valueWidget.attribute()
        text = self.valueWidget.text()
        if text == 'Null':
            value = None
        elif text == 'True':
            value = True
        elif text == 'False':
            value = False
        else:
            try:
                value = float(text)
            except ValueError:
                value = text
        return value

    def setOperator(self, operator):
        self.compWidget.setCurrentIndex(self.compWidget.findText(operator))

    def setValue(self, value):
        print(value)
        if isinstance(self.valueWidget, AttributeWidget):
            self.valueWidget.setAttribute(value)
        elif isinstance(self.valueWidget, QtWidgets.QComboBox):
            self.valueWidget.setCurrentIndex(self.valueWidget.findText(value))
        else:
            if value is None:
                text = 'Null'
            else:
                text = str(value)
            self.valueWidget.setText(text)


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
        self.valueWidget.changeType(self.to_find, self.attributeWidget.type())

    def setToFind(self, to_find):
        self.to_find = to_find
        self.attributeWidget.setToFind(to_find)
        self.valueWidget.setToFind(to_find)

    def toFilter(self):
        return Filter(self.attributeWidget.attribute(), self.valueWidget.operator(),
                    self.valueWidget.value())

    def fromFilter(self, filter):
        if filter.is_alignment:
            attribute = tuple(list(filter.attribute)[:-1] + ['alignment'])
            value = tuple(list(filter.value)[:-1])
            a = filter.attribute[-1]
            op = filter.operator
            if a == 'begin':
                if op == '==':
                    operator = 'Left aligned with'
                else:
                    operator = 'Not left aligned with'
            else:
                if op == '==':
                    operator = 'Right aligned with'
                else:
                    operator = 'Not right aligned with'
        else:
            attribute = filter.attribute
            if 'subset' in attribute[-1]:
                attribute = tuple(list(attribute)[:-1] + ['subset'])
            operator = filter.operator
            value = filter.value
        self.attributeWidget.setAttribute(attribute)
        self.valueWidget.setOperator(operator)
        self.valueWidget.setValue(value)


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

    def setFilters(self, filters):
        #Clear filters somehow
        while self.mainLayout.count() > 1:
            item = self.mainLayout.takeAt(self.mainLayout.count() - 2)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        for f in filters:
            widget = FilterWidget(self.hierarchy, self.to_find)
            widget.fromFilter(f)
            self.mainLayout.insertWidget(0, widget)

    def filters(self):
        filters = []
        for i in range(self.mainLayout.count()):
            widget = self.mainLayout.itemAt(i).widget()
            if not isinstance(widget, FilterWidget):
                continue
            filters.append(widget.toFilter())
        return filters

class BasicQuery(QtWidgets.QWidget):
    def __init__(self):
        super(BasicQuery, self).__init__()
        self.hierarchy = None
        mainLayout = QtWidgets.QFormLayout()
        self.toFindWidget = QtWidgets.QComboBox()
        self.toFindWidget.currentIndexChanged.connect(self.updateToFind)

        self.filterWidget = FilterBox()

        mainLayout.addRow('Linguistic objects to find', self.toFindWidget)
        mainLayout.addRow(self.filterWidget)

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

    def updateProfile(self, profile):
        if profile.to_find is None:
            self.toFindWidget.setCurrentIndex(0)
        else:
            self.toFindWidget.setCurrentIndex(self.toFindWidget.findText(profile.to_find))
        self.filterWidget.setFilters(profile.filters)

    def generateProfile(self):
        profile = QueryProfile()
        profile.to_find = self.toFindWidget.text()
        profile.filters = self.filterWidget.filters()
        return profile
