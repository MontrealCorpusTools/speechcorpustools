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
                present = []
                for k,t in sorted(hierarchy.token_properties[to_find], key = lambda x: x[0]):
                    if t in [tuple, list]:
                        continue
                    if k == 'id':
                        continue
                    self.addItem(k)
                    self.types.append(t)
                    present.append(k)
                for k,t in sorted(hierarchy.type_properties[to_find], key = lambda x: x[0]):
                    if k in present:
                        continue
                    if t in [tuple, list]:
                        continue
                    if k == 'id':
                        continue
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
    attributeTypeChanged = QtCore.pyqtSignal(object, object, object)
    def __init__(self, config, to_find, alignment = False):
        self.config = config
        with CorpusContext(self.config) as c:
            self.hierarchy = c.hierarchy
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
        self.attributeTypeChanged.emit(self.to_find, self.baseSelect.label(), self.baseSelect.type())

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
            if self.alignment:
                return
            if combobox.currentText() in self.hierarchy.annotation_types:
                widget = AttributeSelect(self.hierarchy, combobox.currentText(), self.alignment)
            else:
                widget = AttributeSelect(self.hierarchy, current_annotation_type, self.alignment)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif combobox.currentText() in ['speaker', 'discourse']:
            widget = SpeakerAttributeSelect(self.hierarchy)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
            self.attributeTypeChanged.emit(combobox.currentText(), widget.label(), widget.type())
        else:
            self.attributeTypeChanged.emit(current_annotation_type, combobox.label(), combobox.type())

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

    def label(self):
        num = self.mainLayout.count()
        widget = self.mainLayout.itemAt(num - 1).widget()

        return widget.label()

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
                widget = self.mainLayout.itemAt(self.mainLayout.count() - 1).widget()
                self.attributeTypeChanged.emit(annotation, widget.label(), widget.type())


class ValueWidget(QtWidgets.QWidget):
    def __init__(self, config, to_find):
        self.config = config
        with CorpusContext(self.config) as c:
            self.hierarchy = c.hierarchy
        self.to_find = to_find
        self.levels = None
        super(ValueWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0,10,0,10)

        self.setLayout(self.mainLayout)

        self.compWidget = None
        self.valueWidget = None

    def changeType(self, annotation, label, new_type):
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
            self.valueWidget = AttributeWidget(self.config, self.to_find, alignment = True)
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
            self.compWidget.currentIndexChanged.connect(self.updateValueWidget)
            self.compWidget.addItem('==')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('regex')
            self.mainLayout.addWidget(self.compWidget)
            if self.hierarchy.has_type_property(annotation, label):
                with CorpusContext(self.config) as c:
                    if label == 'label':
                        self.levels = c.lexicon.list_labels(annotation)
                    else:
                        self.levels = c.lexicon.get_property_levels(label, annotation)
                self.updateValueWidget()
            elif annotation == 'speaker':
                with CorpusContext(self.config) as c:
                    self.levels = c.speakers
                self.updateValueWidget()
            elif annotation == 'discourse':
                with CorpusContext(self.config) as c:
                    self.levels = c.discourses
                self.updateValueWidget()
            else:
                self.levels = []
                self.updateValueWidget()

        elif new_type == bool:
            self.compWidget.addItem('==')
            self.valueWidget = QtWidgets.QComboBox()
            self.valueWidget.addItem('True')
            self.valueWidget.addItem('False')
            self.valueWidget.addItem('Null')
        if new_type == str:
            pass
        elif new_type != bool:
            self.mainLayout.addWidget(self.compWidget)
            self.mainLayout.addWidget(self.valueWidget)
        #if new_type in [int, float, str, bool]:
        #    self.switchWidget = QtWidgets.QPushButton('Switch')
        #    self.mainLayout.addWidget(self.switchWidget)

    def updateValueWidget(self):
        if self.levels is None:
            return

        label = self.compWidget.currentText()
        if self.valueWidget is not None:
            self.mainLayout.removeWidget(self.valueWidget)
            self.valueWidget.deleteLater()
        if label == 'regex' or len(self.levels) == 0:
            self.valueWidget = QtWidgets.QLineEdit()
        else:
            if len(self.levels) < 10:
                self.valueWidget = NonScrollingComboBox()
                for l in self.levels:
                    self.valueWidget.addItem(l)
            else:
                self.valueWidget = QtWidgets.QLineEdit()
                completer = QtWidgets.QCompleter(self.levels)
                completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                self.valueWidget.setCompleter(completer)
        self.mainLayout.addWidget(self.valueWidget)


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
    def __init__(self, config, to_find):
        self.config = config
        with CorpusContext(self.config) as c:
            self.hierarchy = c.hierarchy
        self.to_find = to_find
        super(FilterWidget, self).__init__()

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(0,0,0,0)

        self.attributeWidget = AttributeWidget(self.config, self.to_find)
        mainLayout.addWidget(self.attributeWidget)

        self.valueWidget = ValueWidget(self.config, self.to_find)
        mainLayout.addWidget(self.valueWidget)

        self.deleteButton = QtWidgets.QPushButton()
        self.deleteButton.setIcon(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.deleteButton.clicked.connect(self.needsDelete.emit)
        self.deleteButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        mainLayout.addWidget(self.deleteButton)

        self.setLayout(mainLayout)

        self.attributeWidget.attributeTypeChanged.connect(self.valueWidget.changeType)
        self.valueWidget.changeType(self.to_find, self.attributeWidget.label(), self.attributeWidget.type())

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

class BasicFilterBox(QtWidgets.QGroupBox):
    filterToAdd = QtCore.pyqtSignal(object)
    filterToAdd2 = QtCore.pyqtSignal(object)
    filterToAdd3 = QtCore.pyqtSignal(object)
    toFindToAdd = QtCore.pyqtSignal(object)

    def __init__(self):
        super(BasicFilterBox, self).__init__('Basic Filters')

        self.FilterBox = FilterBox()

        self.checked = []

        self.simplenames = ['utterance-initial words', 'utterance-final words', 'syllable-initial phones', 'syllable-final phones', 'penultimate syllables', 'phones before a consonant']
        self.complexnames = ['all vowels in monosyllabic words', 'phones before a word-final consonant']

        self.positions = [(i, j) for i in range(3) for j in range(2)]
        self.positions2 = [(i, j) for i in range(2) for j in range(1)]

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()

        self.tab_widget.addTab(self.tab1, 'Simple queries')
        self.tab_widget.addTab(self.tab2, 'Complex queries')

        self.grid = QtWidgets.QGridLayout()
        self.grid2 = QtWidgets.QGridLayout()
        self.tablayout = QtWidgets.QVBoxLayout(self.tab1)
        self.tablayout.addLayout(self.grid)
        self.tablayout2 = QtWidgets.QVBoxLayout(self.tab2)
        self.tablayout2.addLayout(self.grid2)

        self.superlayout = QtWidgets.QVBoxLayout()
        self.superlayout.addWidget(self.tab_widget)

        self.setLayout(self.superlayout)

        self.tab1UI()
        self.tab2UI()

        self.widgets = [self.grid.itemAt(i).widget() for i in range(self.grid.count())]

    def tab1UI(self):

        layout = QtWidgets.QVBoxLayout()
        self.tablayout.setSpacing(0)
        self.tablayout.setContentsMargins(0,0,0,0)
        self.tablayout.setAlignment(QtCore.Qt.AlignTop)

        mainWidget = QtWidgets.QWidget()
        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        mainWidget.setLayout(self.tablayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(10)
        scroll.setMinimumWidth(10)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.tab1.setLayout(layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        policy = self.sizePolicy()
        policy.setVerticalStretch(1)
        self.setSizePolicy(policy)

        for position, name in zip(self.positions, self.simplenames):

            widget = QtWidgets.QCheckBox(name)
            widget.setMinimumSize(175, 35)
            widget.toggled.connect(self.addColumn)

            self.grid.addWidget(widget, *position)

        self.setGeometry(300, 300, 1000, 300)
        self.show()

    def tab2UI(self):

        layout =QtWidgets.QVBoxLayout()
        self.tablayout2.setSpacing(0)
        self.tablayout2.setContentsMargins(0,0,0,0)
        self.tablayout2.setAlignment(QtCore.Qt.AlignTop)

        mainWidget = QtWidgets.QWidget()
        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        mainWidget.setLayout(self.tablayout2)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(10)
        scroll.setMinimumWidth(10)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.tab2.setLayout(layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        policy = self.sizePolicy()
        policy.setVerticalStretch(1)
        self.setSizePolicy(policy)

        for position, name in zip(self.positions2, self.complexnames):

            widget = QtWidgets.QCheckBox(name)
            widget.setMinimumSize(175, 35)
            widget.toggled.connect(self.addColumn)

            self.grid2.addWidget(widget, *position)

        self.setGeometry(300, 300, 1000, 300)
        self.show()

    def addColumn(self):
        senderwidget = self.sender()
        sender = senderwidget.text()
        if sender == 'utterance-final words':
            label = ['word', 'alignment', 'Right aligned with', 'utterance']
        if sender == 'utterance-initial words':
            label = ['word', 'alignment', 'Left aligned with', 'utterance']
        if sender == 'syllable-initial phones':
            label = ['phone', 'alignment', 'Left aligned with', 'syllable']
        if sender == 'syllable-final phones':
            label = ['phone', 'alignment', 'Right aligned with', 'syllable']
        if sender == 'penultimate syllables':
            label = ['syllable', 'following', 'alignment', 'Right aligned with', 'word']
        if sender == 'phones before a consonant':
            label = ['phone', 'following', 'subset', '==', 'consonant']
        if sender == 'all vowels in monosyllabic words':
            label = ['phone', 'subset', '==', 'syllabic']
            label2 = ['phone', 'syllable', 'alignment', 'Right aligned with', 'word']
            label3 = ['phone', 'syllable', 'alignment', 'Left aligned with', 'word']
        if sender == 'phones before a word-final consonant':
            label = ['phone', 'following', 'alignment', 'Right aligned with', 'word']
            label2 = ['phone', 'following', 'subset', '==', 'consonant']

        '''if sender == 'word-initial phones' and senderwidget.isChecked() == True:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'word-initial phones':
                    checkbox.setChecked(False)
            for i in range(len(self.grid2)):
                checkbox2 = self.grid2.itemAt(i).widget()
                if checkbox2.text() != 'word-initial phones':
                    checkbox2.setChecked(False)
            self.toFindToAdd.emit(label)

        if sender == 'utterance-final words' and senderwidget.isChecked() == True:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'utterance-final words':
                    checkbox.setChecked(False)
            for i in range(len(self.grid2)):
                checkbox2 = self.grid2.itemAt(i).widget()
                if checkbox2.text() != 'utterance-final words':
                    checkbox2.setChecked(False)
            self.toFindToAdd.emit(label)

        if sender == 'penultimate syllables' and senderwidget.isChecked() == True:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'penultimate syllables':
                    checkbox.setChecked(False)
            for i in range(len(self.grid2)):
                checkbox2 = self.grid2.itemAt(i).widget()
                if checkbox2.text() != 'penultimate syllables':
                    checkbox2.setChecked(False)
            self.toFindToAdd.emit(label)'''

        if sender == 'all vowels in monosyllabic words' and senderwidget.isChecked() == True:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'all vowels in monosyllabic words':
                    checkbox.setChecked(False)
            for i in range(len(self.grid2)):
                checkbox2 = self.grid2.itemAt(i).widget()
                if checkbox2.text() != 'all vowels in monosyllabic words':
                    checkbox2.setChecked(False)
            self.toFindToAdd.emit(label)

        if sender == 'phones before a word-final consonant' and senderwidget.isChecked() == True:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'phones before a word-final consonant':
                    checkbox.setChecked(False)
            for i in range(len(self.grid2)):
                checkbox2 = self.grid2.itemAt(i).widget()
                if checkbox2.text() != 'phones before a word-final consonant':
                    checkbox2.setChecked(False)
            self.toFindToAdd.emit(label)

        if label not in self.checked and senderwidget.isChecked() == True:
            self.checked.append(label)
            self.filterToAdd.emit(label)
            if sender == 'all vowels in monosyllabic words' or sender == 'phones before a word-final consonant':
                self.filterToAdd2.emit(label2)
            if sender == 'all vowels in monosyllabic words':
                self.filterToAdd3.emit(label3)
        else:
            self.checked.remove(label)
            label.append('delete')
            label.append('delete2')
            self.filterToAdd.emit(label)
            if sender == 'all vowels in monosyllabic words' or sender == 'phones before a word-final consonant':
                label2.append('delete')
                label2.append('delete2')
                self.filterToAdd2.emit(label2)
            if sender == 'all vowels in monosyllabic words':
                label3.append('delete')
                label3.append('delete2')
                self.filterToAdd3.emit(label3)

    def uncheck(self, to_uncheck):
        if to_uncheck == ['alignment', 'Right aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'utterance-final words':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['alignment', 'Left aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'word-initial phones':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['following', 'alignment']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'penultimate syllables':
                    wcheckbox.setChecked(False)


class FilterBox(QtWidgets.QGroupBox):
    checkboxToUncheck = QtCore.pyqtSignal(object)
    tofind = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FilterBox, self).__init__('Filters')

        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        mainWidget = QtWidgets.QWidget()

        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        mainWidget.setLayout(self.mainLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(10)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.config = None
        self.to_find = None
        self.addButton = QtWidgets.QPushButton('+')
        self.addButton.clicked.connect(self.addNewFilter)
        self.addButton.setEnabled(False)
        layout.addWidget(self.addButton)

        self.setLayout(layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        policy = self.sizePolicy()
        policy.setVerticalStretch(1)
        self.setSizePolicy(policy)


    def deleteWidget(self):
        widget = self.sender()
        self.mainLayout.removeWidget(widget)
        widget.deleteLater()
        categorywidget = widget.attributeWidget.mainLayout.itemAt(0).widget().currentText()
        if len(widget.attributeWidget.mainLayout) > 1:
            infowidget = widget.attributeWidget.mainLayout.itemAt(0).widget().currentText()
            self.checkboxToUncheck.emit([categorywidget, infowidget])
        else:
            infowidget = widget.valueWidget.mainLayout.itemAt(0).widget().currentText()
            self.checkboxToUncheck.emit([categorywidget, infowidget])

    def clearFilters(self):
        while self.mainLayout.count() > 0:
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()

    def setConfig(self, config):
        self.config = config
        self.clearFilters()
        self.addButton.setEnabled(True)

    def setToFind(self, to_find):
        self.to_find = to_find
        for i in range(self.mainLayout.count()):
            self.mainLayout.itemAt(i).widget().setToFind(to_find)

    def addNewFilter(self):
        if self.config is None:
            return
        widget = FilterWidget(self.config, self.to_find)
        widget.needsDelete.connect(self.deleteWidget)
        self.mainLayout.insertWidget(self.mainLayout.count(), widget)

    def setFilters(self, filters):
        self.clearFilters()
        for f in filters:
            widget = FilterWidget(self.config, self.to_find)
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

    def fillInColumn(self, label):
        delete = []
        for i in range(len(self.mainLayout)):
            match = self.mainLayout.itemAt(i)
            delete.append(match.widget())
        if len(delete) > 0:
            for i in range(len(delete)):
                todelete = delete[i]
                self.mainLayout.removeWidget(todelete)
                todelete.setParent(None)
                todelete.deleteLater()

        if len(label) < 6:
            widget = FilterWidget(self.config, self.to_find)
            widget.needsDelete.connect(self.deleteWidget)
            self.mainLayout.addWidget(widget)

            defaultwidget = widget.attributeWidget.mainLayout.itemAt(0).widget()
            index = defaultwidget.findText(label[0])
            defaultwidget.setCurrentIndex(index)
            if label[1] == 'alignment':
                defaultwidget2 = widget.attributeWidget.mainLayout.itemAt(1).widget()
                index2 = defaultwidget2.findText(label[1])
                defaultwidget2.setCurrentIndex(index2)
                defaultwidget3 = widget.valueWidget.mainLayout.itemAt(0).widget()
                index3 = defaultwidget3.findText(label[2])
                defaultwidget3.setCurrentIndex(index3)
                #defaultwidget4 = widget.attributeWidget.mainLayout.itemAt(1).widget()
                #index4 = defaultwidget4.findText(label[3])
                #defaultwidget4.setCurrentIndex(index4)
            if label[1] == 'following' and label[0] == 'syllable':
                defaultwidget2 = widget.attributeWidget.mainLayout.itemAt(1).widget()
                index2 = defaultwidget2.findText(label[1])
                defaultwidget2.setCurrentIndex(index2)
                defaultwidget3 = widget.valueWidget.mainLayout.itemAt(0).widget()
                index3 = defaultwidget3.findText(label[2])
                defaultwidget3.setCurrentIndex(index3)
                defaultwidget4 = widget.attributeWidget.mainLayout.itemAt(2).widget()
                #index4 = defaultwidget4.findText(label[4])
                #defaultwidget4.setCurrentIndex(index4)'''
            #if label[1] == 'following' and label[0] == 'phone':

        if len(label) > 5:
            unchecked = []
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                checkdefault = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                if label[1] == 'alignment':
                    checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                    if checkdefault2 == label[2] and checkdefault == label[1]:
                        unchecked.append(match.widget())
                if label[1] == 'following':
                    checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                    if checkdefault2 == label[3] and checkdefault == label[1]:
                        unchecked.append(match.widget())
                if label[1] == 'subset':
                    checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                    if checkdefault2 == label[2] and checkdefault == label[1]:
                        unchecked.append(match.widget())              

            if len(unchecked) > 0:
                for i in range(len(unchecked)):
                    todelete = unchecked[i]
                    self.mainLayout.removeWidget(todelete)
                    todelete.setParent(None)
                    todelete.deleteLater()

    def fillInColumn2(self, label2):
        widget = FilterWidget(self.config, self.to_find)
        widget.needsDelete.connect(self.deleteWidget)
        self.mainLayout.addWidget(widget)

        defaultwidget = widget.attributeWidget.mainLayout.itemAt(0).widget()
        index = defaultwidget.findText(label2[1])
        defaultwidget.setCurrentIndex(index)
        if label2[1] == 'subset':
            defaultwidget2 = widget.valueWidget.mainLayout.itemAt(0).widget()
            index2 = defaultwidget2.findText(label2[2])
            defaultwidget2.setCurrentIndex(index2)
            defaultwidget3 = widget.valueWidget.mainLayout.itemAt(1).widget()
            #index3 = defaultwidget3.findText(label[3])
            #defaultwidget3.setCurrentIndex(index3)
        if label2[1] == 'syllable':
            defaultwidget2 = widget.valueWidget.mainLayout.itemAt(0).widget()
            index2 = defaultwidget2.findText(label2[2])
            defaultwidget2.setCurrentIndex(index2)
            defaultwidget3 = widget.valueWidget.mainLayout.itemAt(0).widget()
            index3 = defaultwidget3.findText(label2[3])
            defaultwidget3.setCurrentIndex(index3)
        if label2[1] == 'following':
            defaultwidget2 = widget.attributeWidget.mainLayout.itemAt(1).widget()
            index2 = defaultwidget2.findText(label2[2])
            defaultwidget2.setCurrentIndex(index2)
            defaultwidget3 = widget.valueWidget.mainLayout.itemAt(0).widget()
            index3 = defaultwidget3.findText(label2[3])
            defaultwidget3.setCurrentIndex(index3)
            defaultwidget4 = widget.valueWidget.mainLayout.itemAt(1).widget()
            index4 = defaultwidget4.findText(label2[4])
            defaultwidget4.setCurrentIndex(index4)

        if len(label2) > 5:
            unchecked = []
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                checkdefault = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                if label2[1] == 'syllable':
                    checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                    if checkdefault2 == label2[3] and checkdefault == label2[1]:
                        unchecked.append(match.widget())
                if label2[1] == 'following':
                    checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                    if checkdefault2 == label2[3] and checkdefault == label2[1]:
                        unchecked.append(match.widget())

            if len(unchecked) > 0:
                for i in range(len(unchecked)):
                    todelete = unchecked[i]
                    self.mainLayout.removeWidget(todelete)
                    todelete.setParent(None)
                    todelete.deleteLater()

    def fillInColumn3(self, label3):
        widget = FilterWidget(self.config, self.to_find)
        widget.needsDelete.connect(self.deleteWidget)
        self.mainLayout.addWidget(widget)

        defaultwidget = widget.attributeWidget.mainLayout.itemAt(0).widget()
        index = defaultwidget.findText(label3[1])
        defaultwidget.setCurrentIndex(index)

        defaultwidget2 = widget.attributeWidget.mainLayout.itemAt(1).widget()
        index2 = defaultwidget2.findText(label3[2])
        defaultwidget2.setCurrentIndex(index2)
        defaultwidget3 = widget.valueWidget.mainLayout.itemAt(0).widget()
        index3 = defaultwidget3.findText(label3[3])
        defaultwidget3.setCurrentIndex(index3)
        defaultwidget4 = widget.valueWidget.mainLayout.itemAt(1).widget()
        #index4 = defaultwidget4.findText(label3[4])
        #defaultwidget4.setCurrentIndex(index4)

        if len(label3) > 5:
            unchecked = []
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                checkdefault = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                if checkdefault2 == label3[3] and checkdefault == label3[1]:
                    unchecked.append(match.widget())

            if len(unchecked) > 0:
                for i in range(len(unchecked)):
                    todelete = unchecked[i]
                    self.mainLayout.removeWidget(todelete)
                    todelete.setParent(None)
                    todelete.deleteLater()


class BasicQuery(QtWidgets.QWidget):
    def __init__(self):
        super(BasicQuery, self).__init__()
        self.config = None
        self.hierarchy = None
        mainLayout = QtWidgets.QFormLayout()
        mainLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.toFindWidget = QtWidgets.QComboBox()
        self.toFindWidget.currentIndexChanged.connect(self.updateToFind)

        self.filterWidget = FilterBox()
        self.basicFilterWidget = BasicFilterBox()

        self.basicFilterWidget.filterToAdd.connect(self.filterWidget.fillInColumn)
        self.basicFilterWidget.filterToAdd2.connect(self.filterWidget.fillInColumn2)
        self.basicFilterWidget.filterToAdd3.connect(self.filterWidget.fillInColumn3)
        #self.basicFilterWidget.toFindToAdd.connect(self.checkboxUpdateToFind)
        self.filterWidget.checkboxToUncheck.connect(self.basicFilterWidget.uncheck)

        mainLayout.addRow('Linguistic objects to find', self.toFindWidget)
        mainLayout.addRow(self.filterWidget)
        mainLayout.addRow(self.basicFilterWidget)

        self.setLayout(mainLayout)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)


    def updateToFind(self):
        to_find = self.toFindWidget.currentText()
        self.filterWidget.setToFind(to_find)

    #def checkboxUpdateToFind(self, to_find):
     #   to_find = to_find[0]
      #  self.filterWidget.setToFind(to_find)
       # index = self.toFindWidget.findText(to_find)
        #self.toFindWidget.setCurrentIndex(index)

    def updateConfig(self, config):
        self.config = config
        with CorpusContext(config) as c:
            self.hierarchy = c.hierarchy
        self.filterWidget.setConfig(config)
        self.toFindWidget.clear()

        self.toFindWidget.currentIndexChanged.disconnect(self.updateToFind)
        for i, at in enumerate(self.hierarchy.highest_to_lowest):
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
