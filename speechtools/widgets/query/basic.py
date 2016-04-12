import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum, Count

from ..base import NonScrollingComboBox

from ...profiles import QueryProfile, Filter

class AttributeSelect(NonScrollingComboBox):
    def __init__(self, hierarchy, to_find, alignment):
        super(AttributeSelect, self).__init__()
        if not alignment:
            self.addItem('alignment')
            self.addItem('following')
            self.addItem('previous')
            self.addItem('subset')
            self.addItem('duration')
            self.types = ['alignment', 'annotation',' annotation','subset', float]
            if to_find != '':
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

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)

    def type(self):
        index = self.currentIndex()
        return self.types[index]

    def label(self):
        return self.currentText()


class SpeakerAttributeSelect(AttributeSelect):
    def __init__(self, hierarchy):
        QtWidgets.QComboBox.__init__(self)
        self.addItem('name')
        self.types = [str]


class AttributeWidget(QtWidgets.QWidget):
    attributeTypeChanged = QtCore.pyqtSignal(object, object)
    def __init__(self, hierarchy, to_find, alignment = False):
        self.hierarchy = hierarchy
        self.to_find = to_find
        self.alignment = alignment
        super(AttributeWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0,10,0,10)
        self.initWidget()

        self.setLayout(self.mainLayout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)

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
        current_annotation_type = self.annotationType()
        if combobox.currentText() in self.hierarchy.annotation_types or \
            combobox.currentText() in ['previous','following']:
            if combobox.currentText() in self.hierarchy.annotation_types:
                widget = AttributeSelect(self.hierarchy, combobox.currentText(), self.alignment)
            else:
                widget = AttributeSelect(self.hierarchy, current_annotation_type, self.alignment)
            if self.alignment:
                widget.insertItem(0, '')
                widget.setCurrentIndex(0)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif combobox.currentText() in ['speaker', 'discourse']:
            widget = SpeakerAttributeSelect(self.hierarchy)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
            self.attributeTypeChanged.emit('speaker', widget.type())
        else:
            self.attributeTypeChanged.emit(current_annotation_type, combobox.type())

    def annotationType(self):
        index = self.mainLayout.count() - 1
        if index == 0:
            return self.to_find

        a = self.mainLayout.itemAt(index - 1).widget().currentText()
        while a in ['previous', 'following']:
            index -= 1
            if index  < 0:
                a = self.to_find
            else:
                a = self.mainLayout.itemAt(index).widget().currentText()
        return a

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
            if text == self.hierarchy.lowest:
                text = 'phone_name'
            elif text.startswith('word'):
                text = 'word_name'
            att.append(text)
        return tuple(att)

    def setAttribute(self, attribute):
        self.initWidget()
        for a in attribute[1:]:
            ind = self.mainLayout.count() - 1
            widget = self.mainLayout.itemAt(ind).widget()
            if a.endswith('name'):
                a = getattr(self.hierarchy, a)
            widget.setCurrentIndex(widget.findText(a))
        if len(attribute) > 1:
            if a == 'alignment':
                annotation = self.annotationType()
                self.attributeTypeChanged.emit(annotation, self.mainLayout.itemAt(self.mainLayout.count() - 1).widget().type())


class ValueWidget(QtWidgets.QWidget):
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(ValueWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0,10,0,10)

        self.setLayout(self.mainLayout)

        self.compWidget = None
        self.valueWidget = None

    def changeType(self, annotation, new_type):
        while self.mainLayout.count():
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        self.compWidget = NonScrollingComboBox()
        self.compWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        if new_type == 'alignment':
            self.compWidget.addItem('Right aligned with')
            self.compWidget.addItem('Left aligned with')
            self.compWidget.addItem('Not right aligned with')
            self.compWidget.addItem('Not left aligned with')
            self.valueWidget = AttributeWidget(self.hierarchy, self.to_find, alignment = True)
        elif new_type == 'subset':
            self.compWidget.addItem('==')
            self.valueWidget = NonScrollingComboBox()
            if annotation in self.hierarchy.subset_types:
                for s in self.hierarchy.subset_types[annotation]:
                    self.valueWidget.addItem(s)
            if annotation in self.hierarchy.subset_tokens:
                for s in self.hierarchy.subset_tokens[annotation]:
                    self.valueWidget.addItem(s)

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
        #if new_type in [int, float, str, bool]:
        #    self.switchWidget = QtWidgets.QPushButton('Switch')
        #    self.mainLayout.addWidget(self.switchWidget)

    def setToFind(self, to_find):
        self.to_find = to_find
        if isinstance(self.valueWidget, AttributeWidget):
            self.valueWidget.setToFind(to_find)

    def operator(self):
        text = self.compWidget.currentText()
        operator = text
        return operator

    def value(self):
        if isinstance(self.valueWidget, AttributeWidget):
            return self.valueWidget.attribute()
        elif isinstance(self.valueWidget, QtWidgets.QComboBox):
            text = self.valueWidget.currentText()
        else:
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
    needsDelete = QtCore.pyqtSignal()
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(FilterWidget, self).__init__()

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(0,0,0,0)

        self.attributeWidget = AttributeWidget(self.hierarchy, self.to_find)
        mainLayout.addWidget(self.attributeWidget)

        self.valueWidget = ValueWidget(self.hierarchy, self.to_find)
        mainLayout.addWidget(self.valueWidget)

        self.deleteButton = QtWidgets.QPushButton()
        self.deleteButton.setIcon(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.deleteButton.clicked.connect(self.needsDelete.emit)
        self.deleteButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        mainLayout.addWidget(self.deleteButton)

        self.setLayout(mainLayout)

        self.attributeWidget.attributeTypeChanged.connect(self.valueWidget.changeType)
        self.valueWidget.changeType(self.to_find, self.attributeWidget.type())

    def setToFind(self, to_find):
        self.to_find = to_find
        self.attributeWidget.setToFind(to_find)
        self.valueWidget.setToFind(to_find)

    def toFilter(self):
        att = self.attributeWidget.attribute()
        op = self.valueWidget.operator()
        val = self.valueWidget.value()
        if att[-1] == 'subset':
            a = self.attributeWidget.annotationType()
            if val in self.hierarchy.subset_types[a]:
                att = tuple(list(att[:-1]) + ['type_subset'])
            else:
                att = tuple(list(att[:-1]) + ['token_subset'])
        elif att[-1] == 'alignment':
            if op.startswith('Left') or op.startswith('Not left'):
                a = 'begin'
            else:
                a = 'end'
            att = tuple(list(att)[:-1] + [a])

            if op.startswith('Not'):
                op = '!='
            else:
                op = '=='
            val = tuple(list(val) + [a])
        return Filter(att, op, val)

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

        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(self.mainLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(200)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.hierarchy = None
        self.to_find = None
        self.addButton = QtWidgets.QPushButton('+')
        self.addButton.clicked.connect(self.addNewFilter)
        self.addButton.setEnabled(False)
        layout.addWidget(self.addButton)

        self.setLayout(layout)

    def deleteWidget(self):
        widget = self.sender()
        self.mainLayout.removeWidget(widget)
        widget.deleteLater()

    def clearFilters(self):
        while self.mainLayout.count() > 0:
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy
        self.clearFilters()
        self.addButton.setEnabled(True)

    def setToFind(self, to_find):
        self.to_find = to_find
        for i in range(self.mainLayout.count()):
            self.mainLayout.itemAt(i).widget().setToFind(to_find)

    def addNewFilter(self):
        if self.hierarchy is None:
            return
        widget = FilterWidget(self.hierarchy, self.to_find)
        widget.needsDelete.connect(self.deleteWidget)
        self.mainLayout.insertWidget(self.mainLayout.count(), widget)

    def setFilters(self, filters):
        self.clearFilters()
        for f in filters:
            widget = FilterWidget(self.hierarchy, self.to_find)
            widget.fromFilter(f)
            self.mainLayout.addWidget(widget)

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
            if profile.to_find.endswith('_name') and self.hierarchy is not None:
                to_find = getattr(self.hierarchy, profile.to_find)
            else:
                to_find = profile.to_find
            self.toFindWidget.setCurrentIndex(self.toFindWidget.findText(to_find))
        self.filterWidget.setFilters(profile.filters)

    def profile(self):
        profile = QueryProfile()
        profile.to_find = self.toFindWidget.currentText()
        profile.filters = self.filterWidget.filters()
        return profile
