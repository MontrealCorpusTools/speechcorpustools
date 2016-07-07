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
            
            if self.hierarchy.has_type_property(annotation, label):
                with CorpusContext(self.config) as c:
                    if label == 'label':
                        self.levels = c.lexicon.list_labels(annotation)
                    else:
                        self.levels = c.lexicon.get_property_levels(label, annotation)
                boolean = self.updateValueWidget()
            elif annotation == 'speaker':
                with CorpusContext(self.config) as c:
                    self.levels = c.speakers
                boolean = self.updateValueWidget()
            elif annotation == 'discourse':
                with CorpusContext(self.config) as c:
                    self.levels = c.discourses
                boolean = self.updateValueWidget()
            else:
                self.levels = []
                boolean = self.updateValueWidget()
            if not boolean: 
                self.compWidget.currentIndexChanged.connect(self.updateValueWidget)
                self.compWidget.addItem('==')
                self.compWidget.addItem('!=')
                self.compWidget.addItem('regex')
            self.mainLayout.addWidget(self.compWidget)
            self.mainLayout.addWidget(self.valueWidget)
        elif new_type == bool:
            print("in bool!!! \n\n\n\n")
            self.compWidget.addItem('==')
            self.valueWidget = QtWidgets.QComboBox()
            self.valueWidget.addItem('True')
            self.valueWidget.addItem('False')
            self.valueWidget.addItem('Null')
            self.mainLayout.addWidget(self.valueWidget)
        if new_type == str:
            pass
        elif new_type != bool:
            self.mainLayout.addWidget(self.compWidget)
            self.mainLayout.addWidget(self.valueWidget)

        #if new_type in [int, float, str, bool]:
        #    self.switchWidget = QtWidgets.QPushButton('Switch')
        #    self.mainLayout.addWidget(self.switchWidget)

    def updateValueWidget(self):
        boolean = False
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
                
                if len(self.levels) == 1 and self.levels[0] == 'True' or self.levels[0] == 'False':
                    self.compWidget.addItem('==')
                    self.valueWidget = QtWidgets.QComboBox()
                    self.valueWidget.addItem('True')
                    self.valueWidget.addItem('False')
                    self.valueWidget.addItem('Null')
                    boolean = True
                    #self.mainLayout.addWidget(self.compWidget)
                    

                else:
                    self.valueWidget = NonScrollingComboBox()
                    for l in self.levels:
                        self.valueWidget.addItem(l)
            else:
                self.valueWidget = QtWidgets.QLineEdit()
                completer = QtWidgets.QCompleter(self.levels)
                completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                self.valueWidget.setCompleter(completer)
        #self.mainLayout.addWidget(self.valueWidget)
        return boolean

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
    needsHelp = QtCore.pyqtSignal(object)
    def __init__(self, config, to_find):
        #add in slot to tell which type to find

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

        self.helpButton = QtWidgets.QPushButton()
        self.helpButton.setText("help")
        self.helpButton.clicked.connect(self.needHelp)
        self.helpButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        
        mainLayout.addWidget(self.helpButton)


        self.setLayout(mainLayout)

        self.attributeWidget.attributeTypeChanged.connect(self.valueWidget.changeType)
        self.valueWidget.changeType(self.to_find, self.attributeWidget.label(), self.attributeWidget.type())

    def needHelp(self, to_find):
        options = [self.attributeWidget.attribute(), self.valueWidget.operator(), self.valueWidget.value()]   
        self.needsHelp.emit(options)

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
            main = filter.attribute
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
    filterToDelete = QtCore.pyqtSignal(object)
    filterToAdd2 = QtCore.pyqtSignal(object)
    filterToAdd3 = QtCore.pyqtSignal(object)
    toFindToAdd = QtCore.pyqtSignal(object)
    compdelete = QtCore.pyqtSignal(object)
    deletecomplex = QtCore.pyqtSignal()
    labelout = QtCore.pyqtSignal(object)
    labelout2 = QtCore.pyqtSignal(object)
    labelout3 = QtCore.pyqtSignal(object)

    def __init__(self):
        super(BasicFilterBox, self).__init__('Basic Filters')

        self.FilterBox = FilterBox()

        self.annotation_types = {}
        self.subset_tokens = {}
        self.subset_types = {}

        self.checked = []
        self.checkedsenders = []
        self.stayunchecked = []

        self.simplenames = ['utterance-initial words', 'utterance-final words', 'penultimate syllables', 'syllable-initial phones', 'syllable-final phones', 'phones before a syllabic']
        self.complexnames = ['all vowels in monosyllabic words', 'word-final phones after a syllabic']

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

    def store(self, annotation_types):
        self.annotation_types = annotation_types[0]
        self.subset_tokens = annotation_types[1]
        self.subset_types = annotation_types[2]

    def disable(self, to_find):
        for i in range(len(self.grid2)):
            checkbox = self.grid2.itemAt(i).widget()
            if to_find[0] != 'phone':
                checkbox.setChecked(False)
        for i in range(len(self.grid)):
            checkbox = self.grid.itemAt(i).widget()
            checkbox.setChecked(False)
        if to_find[0] == 'utterance':
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                checkbox.setEnabled(False)
        if to_find[0] == 'word':
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'penultimate syllables' and checkbox.text() != 'syllable-initial phones' and checkbox.text() != 'syllable-final phones' and checkbox.text() != 'phones before a syllabic':
                    checkbox.setEnabled(True)
                else:
                    checkbox.setEnabled(False)
                if (checkbox.text() == 'utterance-final words' or checkbox.text() == 'utterance-initial words') and ('utterance' not in self.annotation_types or 'word' not in self.annotation_types):
                    checkbox.setEnabled(False)
        if to_find[0] == 'syllable':
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'syllable-initial phones' and checkbox.text() != 'syllable-final phones' and checkbox.text() != 'phones before a syllabic':
                    checkbox.setEnabled(True)
                else:
                    checkbox.setEnabled(False)
                if (checkbox.text() == 'utterance-final words' or checkbox.text() == 'utterance-initial words') and ('utterance' not in self.annotation_types or 'word' not in self.annotation_types):
                    checkbox.setEnabled(False)
                if checkbox.text() == 'penultimate syllables' and ('syllable' not in self.annotation_types or 'word' not in self.annotation_types):
                    checkbox.setEnabled(False)
        if to_find[0] == 'phone':
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                checkbox.setEnabled(True)
                if (checkbox.text() == 'utterance-final words' or checkbox.text() == 'utterance-initial words') and ('utterance' not in self.annotation_types or 'word' not in self.annotation_types):
                    checkbox.setEnabled(False)
                if (checkbox.text() == 'syllable-initial phones' or checkbox.text() == 'syllable-final phones') and ('syllable' not in self.annotation_types or 'phone' not in self.annotation_types):
                    checkbox.setEnabled(False)
                if checkbox.text() == 'penultimate syllables' and ('syllable' not in self.annotation_types or 'word' not in self.annotation_types):
                    checkbox.setEnabled(False)
                if checkbox.text() == 'phones before a syllabic' and ('phone' not in self.annotation_types or ('syllabic' not in self.subset_tokens['phone'] and 'syllabic' not in self.subset_types['phone'])):

                    checkbox.setEnabled(False)
        for i in range(len(self.grid2)):
            checkbox = self.grid2.itemAt(i).widget()
            if checkbox.text() == 'all vowels in monosyllabic words' and ('phone' not in self.annotation_types or 'word' not in self.annotation_types or
            ('syllabic' not in self.subset_tokens['phone'] and 'syllabic' not in self.subset_types['phone'])):
                checkbox.setEnabled(False)
                self.stayunchecked.append(checkbox)
            if checkbox.text() == 'all vowels in monosyllabic words' and 'phone' in self.annotation_types and 'word' in self.annotation_types and ('syllabic' in self.subset_tokens['phone'] or 'syllabic' in self.subset_types['phone']):
                checkbox.setEnabled(True)
                if checkbox in self.stayunchecked:
                    self.stayunchecked.remove(checkbox)
        for i in range(len(self.grid2)):
            checkbox = self.grid2.itemAt(i).widget()
            if checkbox.text() == 'phones before a word-final consonant' and ('phone' not in self.annotation_types or
            ('consonant' not in self.subset_tokens['phone'] and 'consonant' not in self.subset_types['phone'])):
                checkbox.setEnabled(False)
                self.stayunchecked.append(checkbox)
            if checkbox.text() == 'phones before a word-final consonant' and 'phone' in self.annotation_types and ('consonant' in self.subset_tokens['phone'] or 'consonant' in self.subset_types['phone']):
                checkbox.setEnabled(True)
        if len(self.stayunchecked) > 2:
            self.stayunchecked.pop(0)
            self.stayunchecked.pop(1)

    def addColumn(self):
        senderwidget = self.sender()
        sender = senderwidget.text()
        if sender == 'utterance-final words':
            label = ['word', 'alignment', 'Right aligned with', 'utterance']
            f = Filter(('','word','end'), '==', ('', 'word','utterance','end'))
        if sender == 'utterance-initial words':
            label = ['word', 'alignment', 'Left aligned with', 'utterance']
            f = Filter(('', 'word','begin'), '==', ('', 'word','utterance','begin'))
        if sender == 'syllable-initial phones':
            label = ['phone', 'alignment', 'Left aligned with', 'syllable']
            f = Filter(('', 'phone','begin'), '==', ('', 'phone','syllable','begin'))
        if sender == 'syllable-final phones':
            label = ['phone', 'alignment', 'Right aligned with', 'syllable']
            f = Filter(('', 'phone','end'), '==', ('', 'phone','syllable','end'))
        if sender == 'penultimate syllables':
            label = ['syllable', 'following', 'alignment', 'Right aligned with', 'word']
            f = Filter(('', 'syllable','following', 'end'), '==', ('', 'syllable','word','end'))
        if sender == 'phones before a syllabic':
            label = ['phone', 'following', 'subset', '==', 'syllabic']
            f = Filter(('', 'phone','following', 'type_subset'), '==', 'syllabic')

        if sender == 'all vowels in monosyllabic words':
            label = ['phone', 'subset', '==', 'syllabic']
            f = Filter(('phone', 'type_subset'), '==', 'syllabic')
            label2 = ['phone', 'syllable', 'alignment', 'Right aligned with', 'word']
            f2 = Filter(('phone','syllable', 'end'), '==', ('phone', 'syllable','word','end'))
            label3 = ['phone', 'syllable', 'alignment', 'Left aligned with', 'word']
            f3 = Filter(('phone','syllable', 'begin'), '==', ('phone', 'syllable','word','begin'))

        if sender == 'word-final phones after a syllabic':
            label = ['phone', 'alignment', 'Right aligned with', 'word']
            f = Filter(('phone', 'end'), '==', ('phone','word','end'))
            label2 = ['phone', 'previous', 'subset', '==', 'syllabic']
            f2 = Filter(('phone', 'previous', 'type_subset'), '==', 'syllabic')

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

        if sender == 'word-final phones after a syllabic' and senderwidget.isChecked() == True:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.text() != 'word-final phones after a syllabic':
                    checkbox.setChecked(False)
            for i in range(len(self.grid2)):
                checkbox2 = self.grid2.itemAt(i).widget()
                if checkbox2.text() != 'word-final phones after a syllabic':
                    checkbox2.setChecked(False)
            self.toFindToAdd.emit(label)

        if label not in self.checked and senderwidget.isChecked() == True:
            self.checked.append(label)
            self.checkedsenders.append(sender)
            self.filterToAdd.emit(f)
            if sender == 'all vowels in monosyllabic words' or sender == 'word-final phones after a syllabic':
                self.filterToAdd2.emit(f2)
            if sender == 'all vowels in monosyllabic words':
                self.filterToAdd3.emit(f3)
        elif label in self.checked:
            self.checked.remove(label)
            self.checkedsenders.remove(sender)
            label.append('delete')
            label.append('delete2')
            self.labelout.emit(label)
            if sender == 'all vowels in monosyllabic words' or sender == 'word-final phones after a syllabic':
                label2.append('delete')
                label2.append('delete2')
                self.labelout2.emit(label2)
            if sender == 'all vowels in monosyllabic words':
                label3.append('delete')
                label3.append('delete2')
                self.labelout3.emit(label3)

        if 'all vowels in monosyllabic words' in self.checkedsenders or 'word-final phones after a syllabic' in self.checkedsenders:
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                checkbox.setEnabled(False)
        else:
            shaded = []
            for i in range(len(self.grid)):
                checkbox = self.grid.itemAt(i).widget()
                if checkbox.isEnabled() == True:
                    shaded.append(checkbox)
            if len(shaded) == 0:
                for i in range(len(self.grid)):
                    checkbox = self.grid.itemAt(i).widget()
                    checkbox.setEnabled(True)
                    if (checkbox.text() == 'utterance-final words' or checkbox.text() == 'utterance-initial words') and ('utterance' not in self.annotation_types or 'word' not in self.annotation_types):
                        checkbox.setEnabled(False)
                    if (checkbox.text() == 'syllable-initial phones' or checkbox.text() == 'syllable-final phones') and ('syllable' not in self.annotation_types or 'phone' not in self.annotation_types):
                        checkbox.setEnabled(False)
                    if checkbox.text() == 'penultimate syllables' and ('syllable' not in self.annotation_types or 'word' not in self.annotation_types):
                        checkbox.setEnabled(False)
                    if checkbox.text() == 'phones before a syllabic' and ('phone' not in self.annotation_types or ('syllabic' not in self.subset_tokens['phone'] and 'syllabic' not in self.subset_types['phone'])):
                        checkbox.setEnabled(False)

        if len(self.checkedsenders) > 0 and 'all vowels in monosyllabic words' not in self.checkedsenders and 'word-final phones after a syllabic' not in self.checkedsenders:
            for i in range(len(self.grid2)):
                checkbox = self.grid2.itemAt(i).widget()
                checkbox.setEnabled(False)
        else:
            for i in range(len(self.grid2)):
                checkbox = self.grid2.itemAt(i).widget()
                if checkbox not in self.stayunchecked:
                    checkbox.setEnabled(True)
        if len(self.checkedsenders) == 0:
            for i in range(len(self.grid2)):
                checkbox = self.grid2.itemAt(i).widget()
                if checkbox not in self.stayunchecked:
                    checkbox.setEnabled(True)

    def uncheck(self, to_uncheck):
        checked = []
        if to_uncheck == ['word', 'alignment', 'Right aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'utterance-final words':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['word', 'alignment', 'Left aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'utterance-initial words':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['phone', 'alignment', 'Right aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'syllable-final phones':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['phone', 'alignment', 'Left aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'syllable-initial phones':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['syllable', 'following', 'Right aligned with'] or to_uncheck == ['following', 'alignment', 'Right aligned with']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'penultimate syllables':
                    wcheckbox.setChecked(False)
        elif to_uncheck == ['phone', 'following', '=='] or to_uncheck == ['following', 'subset', '==']:
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == 'phones before a syllabic':
                    wcheckbox.setChecked(False)
        for i in range(len(self.grid)):
            checkbox = self.grid.itemAt(i).widget()
            if checkbox.isChecked() == True:
                checked.append(checkbox)
        if len(checked) == 0:
            for i in range(len(self.grid2)):
                checkbox = self.grid2.itemAt(i).widget()
                if checkbox not in self.stayunchecked:
                    checkbox.setEnabled(True)


class FilterBox(QtWidgets.QGroupBox):
    checkboxToUncheck = QtCore.pyqtSignal(object)
    tofind = QtCore.pyqtSignal(object)
    uncheckall = QtCore.pyqtSignal()

    needsHelp = QtCore.pyqtSignal(object)

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
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(mainWidget)
        self.scroll.setMinimumHeight(10)
        self.scroll.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
        policy = self.scroll.sizePolicy()
        policy.setVerticalStretch(1)
        self.scroll.setSizePolicy(policy)
        layout.addWidget(self.scroll)

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
        w = FilterWidget(self.config, self.to_find)
        categorywidget = widget.attributeWidget.mainLayout.itemAt(0).widget().currentText()
        if len(widget.attributeWidget.mainLayout) > 1:
            infowidget = widget.attributeWidget.mainLayout.itemAt(1).widget().currentText()
            infowidget2 = widget.valueWidget.mainLayout.itemAt(0).widget().currentText()
            infowidget3 = widget.valueWidget.mainLayout.itemAt(1).widget()
            self.checkboxToUncheck.emit([categorywidget, infowidget, infowidget2])
        else:
            infowidget = widget.valueWidget.mainLayout.itemAt(0).widget().currentText()
            self.checkboxToUncheck.emit([w.to_find, categorywidget, infowidget])

    def clearFilters(self):
        while self.mainLayout.count() > 0:
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        self.uncheckall.emit()

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
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        widget.needsHelp.connect(self.needsHelp.emit)

    def setFilters(self, filters):
        self.clearFilters()
        for f in filters:
            self.addFilter(f)

    def filters(self):
        filters = []
        for i in range(self.mainLayout.count()):
            widget = self.mainLayout.itemAt(i).widget()
            if not isinstance(widget, FilterWidget):
                continue
            filters.append(widget.toFilter())
        return filters

    def addFilter(self, filter):
        widget = FilterWidget(self.config, self.to_find)
        widget.fromFilter(filter)
        self.mainLayout.addWidget(widget)
        widget.needsDelete.connect(self.deleteWidget)
        widget.needsHelp.connect(self.needsHelp.emit)

    def fillInColumn(self, label):

        delete = []
        if label == ['phone', 'subset', '==', 'syllabic'] or label == ['phone', 'alignment', 'Right aligned with', 'word']:
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                delete.append(match.widget())
            if len(delete) > 0:
                for i in range(len(delete)):
                    todelete = delete[i]
                    self.mainLayout.removeWidget(todelete)
                    todelete.setParent(None)
                    todelete.deleteLater()

        if len(label) > 5 and label != ['phone', 'subset', '==', 'syllabic', 'delete', 'delete2'] and label != ['phone', 'alignment', 'Right aligned with', 'word', 'delete', 'delete2']:
            unchecked = []   
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                if match.widget().attributeWidget.mainLayout.itemAt(1) != None:
                    checkdefault = match.widget().attributeWidget.mainLayout.itemAt(1).widget().currentText()
                    if label[1] == 'alignment':
                        checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                        checkdefault3 = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                        if checkdefault2 == label[2] and checkdefault == label[1] and checkdefault3 == label[0]:
                            unchecked.append(match.widget())
                    if label[1] == 'following':
                        checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                        checkdefault3 = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                        if checkdefault2 == label[3] and checkdefault == label[1] and checkdefault3 == label[0] and label[4] != 'syllabic':
                            unchecked.append(match.widget())
                        elif checkdefault == label[2] and checkdefault2 == label[3] and checkdefault3 == label[1]:
                            unchecked.append(match.widget())
                    if label[0] == 'syllable':
                        checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                        checkdefault3 = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                        if checkdefault2 == label[3] and checkdefault == label[2] and checkdefault3 == label[1]:
                            unchecked.append(match.widget())
                else:
                    checkdefault = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                    if label[1] == 'alignment':
                        checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                        if checkdefault2 == label[2] and checkdefault == label[1]:
                            unchecked.append(match.widget())
                    if label[1] == 'following':
                        checkdefault2 = match.widget().valueWidget.mainLayout.itemAt(0).widget().currentText()
                        if checkdefault2 == label[3] and checkdefault == label[1]:
                            unchecked.append(match.widget())
                    if label[0] == 'syllable':
                        checkdefault2 = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                        if checkdefault == label[1] and checkdefault2 == label[2]:
                            unchecked.append(match.widget())

            if len(unchecked) > 0:
                for i in range(len(unchecked)):
                    todelete = unchecked[i]
                    self.mainLayout.removeWidget(todelete)
                    todelete.setParent(None)
                    todelete.deleteLater()

        if len(label) > 5 and label == ['phone', 'subset', '==', 'syllabic', 'delete', 'delete2'] or label == ['phone', 'alignment', 'Right aligned with', 'word', 'delete', 'delete2']:
            self.clearFilters()

class BasicQuery(QtWidgets.QWidget):
    needsHelp = QtCore.pyqtSignal(object)
    changetofind = QtCore.pyqtSignal(object)
    changeconfig = QtCore.pyqtSignal(object)
    def __init__(self):
        super(BasicQuery, self).__init__()
        mainLayout = QtWidgets.QFormLayout()
        mainLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.toFindWidget = QtWidgets.QComboBox()
        self.toFindWidget.currentIndexChanged.connect(self.updateToFind)

        self.filterWidget = FilterBox()
        self.basicFilterWidget = BasicFilterBox()

        self.changetofind.connect(self.filterWidget.clearFilters)
        self.changeconfig.connect(self.basicFilterWidget.store)
        self.changetofind.connect(self.basicFilterWidget.disable)
        self.basicFilterWidget.deletecomplex.connect(self.filterWidget.clearFilters)
        self.basicFilterWidget.toFindToAdd.connect(self.checkboxUpdateToFind)
        self.basicFilterWidget.filterToAdd.connect(self.filterWidget.addFilter)
        self.basicFilterWidget.filterToAdd2.connect(self.filterWidget.addFilter)
        self.basicFilterWidget.filterToAdd3.connect(self.filterWidget.addFilter)
        self.basicFilterWidget.labelout.connect(self.filterWidget.fillInColumn)
        self.filterWidget.checkboxToUncheck.connect(self.basicFilterWidget.uncheck)

        self.filterWidget.needsHelp.connect(self.needsHelp.emit)
        mainLayout.addRow('Linguistic objects to find', self.toFindWidget)
        mainLayout.addRow(self.filterWidget)
        mainLayout.addRow(self.basicFilterWidget)

        self.setLayout(mainLayout)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)

    def updateToFind(self, annotation_types):
        to_find = self.toFindWidget.currentText()
        self.filterWidget.setToFind(to_find)
        self.changetofind.emit([to_find, annotation_types])

    def checkboxUpdateToFind(self, to_find):
        to_find = to_find[0]
        self.filterWidget.setToFind(to_find)
        index = self.toFindWidget.findText(to_find)
        self.toFindWidget.setCurrentIndex(index)

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
        self.updateToFind(self.hierarchy.annotation_types)
        self.changeconfig.emit((self.hierarchy.annotation_types, self.hierarchy.subset_tokens, self.hierarchy.subset_types))

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
