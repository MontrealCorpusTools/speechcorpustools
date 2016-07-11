

import collections

from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from ...profiles import available_export_profiles, ExportProfile, Column

from .basic import AttributeSelect as QueryAttributeSelect, SpeakerAttributeSelect

import collections

class PauseSelect(QueryAttributeSelect):
    def __init__(self):
        QtWidgets.QComboBox.__init__(self)
        self.addItem('following')
        self.addItem('previous')
        self.addItem('duration')

class AcousticSelect(QueryAttributeSelect):
    def __init__(self):
        QtWidgets.QComboBox.__init__(self)
        self.addItem('mean')
        self.addItem('max')
        self.addItem('min')

class AttributeSelect(QueryAttributeSelect):
    def __init__(self, hierarchy, to_find):
        QtWidgets.QComboBox.__init__(self)
        if to_find != 'pause':

            present = []
            for k,t in sorted(hierarchy.token_properties[to_find]):
                if k == 'id':
                    continue
                present.append(k)
                self.addItem(k)
            for k,t in sorted(hierarchy.type_properties[to_find]):
                if k == 'id':
                    continue
                if k in present:
                    continue
                self.addItem(k)
            self.addItem('following')
            self.addItem('previous')
            self.addItem('duration')
            if to_find == 'word':
                self.addItem('pause')
            for k in hierarchy.highest_to_lowest:
                if k != to_find:
                    self.addItem(k)
            self.addItem('speaker')
            self.addItem('discourse')
            if to_find in hierarchy.subannotations:
                for s in sorted(hierarchy.subannotations[to_find]):
                    self.addItem(s)
            self.addItem('pitch')

class AttributeWidget(QtWidgets.QWidget):
    finalChanged = QtCore.pyqtSignal(object)

    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(AttributeWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0,5,0,5)

        self.setLayout(self.mainLayout)
        self.initWidget()

    def initWidget(self):
        while self.mainLayout.count():
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            w = item.widget()
            w.setParent(None)
            w.deleteLater()

        select = AttributeSelect(self.hierarchy, self.to_find)
        select.currentIndexChanged.connect(self.updateAttribute)

        self.mainLayout.addWidget(select)
        self.finalChanged.emit(self.mainLayout.itemAt(self.mainLayout.count() - 1).widget().label())

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
            w = item.widget()
            w.setParent(None)
            w.deleteLater()
        current_annotation_type = self.annotationType()
        if combobox.currentText() in self.hierarchy.annotation_types:
            widget = AttributeSelect(self.hierarchy, combobox.currentText())
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif current_annotation_type == 'pause':
            widget = PauseSelect()
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif combobox.currentText() == 'pitch':
            widget = AcousticSelect()
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif combobox.currentText() in ['previous','following']:
            widget = AttributeSelect(self.hierarchy, current_annotation_type)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif combobox.currentText() in ['speaker', 'discourse']:
            widget = SpeakerAttributeSelect(self.hierarchy)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        self.finalChanged.emit('_'.join(self.attribute()[1:]))

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

    def attribute(self):
        att = [self.to_find]
        for i in range(self.mainLayout.count()):
            widget = self.mainLayout.itemAt(i).widget()
            if not isinstance(widget, QueryAttributeSelect):
                continue
            text = widget.currentText()
            att.append(text)
        return tuple(att)

    def setAttribute(self, attribute):
        self.initWidget()
        to_iter = []
        for a in attribute:
            if a.endswith('_name'):
                a = getattr(self.hierarchy, a)
            to_iter.append(a)
        if to_iter[0] == self.to_find:
            to_iter = to_iter[1:]
        for a in to_iter:
            ind = self.mainLayout.count() - 1
            widget = self.mainLayout.itemAt(ind).widget()
            ind = widget.findText(a)
            if ind == -1:
                raise(AttributeError)
            widget.setCurrentIndex(ind)

class ColumnWidget(QtWidgets.QWidget):
    needsDelete = QtCore.pyqtSignal()
    exportHelpBroadcast = QtCore.pyqtSignal(object)
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(ColumnWidget, self).__init__()

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(0,0,0,0)

        self.attributeWidget = AttributeWidget(self.hierarchy, self.to_find)
        self.attributeWidget.finalChanged.connect(self.updateColumnName)
        mainLayout.addWidget(self.attributeWidget)

        label = QtWidgets.QLabel('Output name:')
        mainLayout.addWidget(label)

        self.nameWidget = QtWidgets.QLineEdit()
        self.attributeWidget.setToFind(to_find)
        mainLayout.addWidget(self.nameWidget)

        self.deleteButton = QtWidgets.QPushButton()
        self.deleteButton.setIcon(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.deleteButton.clicked.connect(self.needsDelete.emit)
        self.deleteButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        mainLayout.addWidget(self.deleteButton)

        self.helpButton = QtWidgets.QPushButton()
        self.helpButton.setText("help")
        self.helpButton.clicked.connect(self.sendForHelp)
        self.helpButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)

        mainLayout.addWidget(self.helpButton)

        self.setLayout(mainLayout)

    def updateColumnName(self, name):
        if any(name.endswith(x) for x in ['_mean', '_min', '_max']):
            self.nameWidget.setEnabled(False)
        else:
            self.nameWidget.setEnabled(True)
        self.nameWidget.setText(name)

    def setToFind(self, to_find):
        self.to_find = to_find
        self.attributeWidget.setToFind(to_find)

    def toColumn(self):
        att = self.attributeWidget.attribute()
        name = self.nameWidget.text().replace(' ', '_')

        return Column(att, name)

    def fromColumn(self, column):
        attribute = column.attribute
        try:
            self.attributeWidget.setAttribute(attribute)
        except AttributeError:
            self.needsDelete.emit()
        self.nameWidget.setText(column.name)

    def sendForHelp(self, to_find):
        options = self.attributeWidget.attribute()
        self.exportHelpBroadcast.emit(options)

class BasicColumnBox(QtWidgets.QGroupBox):
    columnToAdd = QtCore.pyqtSignal(object)

    def __init__(self, hierarchy, to_find):
        super(BasicColumnBox, self).__init__('Columns')

        self.to_find = to_find
        self.hierarchy = hierarchy

        self.ColumnBox = ColumnBox(self.hierarchy, self.to_find)
        self.checked = []

        hierarchydict = collections.OrderedDict()
        for i in sorted(hierarchy.annotation_types):
            properties = []
            for j in sorted(hierarchy.token_properties[i]):
                if j[0] != 'id':
                    properties.append(j[0])
            for k in sorted(hierarchy.type_properties[i]):
                    if k[0] != 'id' and k[0] not in properties:
                        properties.append(k[0])
            hierarchydict[i] = properties
        for i in hierarchydict.values():
            i.append('duration')

        dictlengths = []
        for key in hierarchydict:
            dictlengths.append(len(hierarchydict[key]))
        self.maxboxes = max(dictlengths)
        self.numcolumns = self.maxboxes + 1

        self.names = []
        for i in hierarchydict:
            self.names.append(i)
            valuelength = len(hierarchydict[i])
            for j in hierarchydict[i]:
                self.names.append(j)
            if valuelength < self.maxboxes:
                filler = self.maxboxes - valuelength
                for num in range(filler):
                    self.names.append('')
        self.names.append('discourse')
        for i in range(self.maxboxes):
            self.names.append('')
        self.names.append('speaker')

        self.complexnames = ['syllable position of previous phone', 'duration of the second syllable after the current one']

        self.positions = [(i, j) for i in range(len(hierarchydict)+2) for j in range(self.numcolumns)]
        self.positions2 = [(i, j) for i in range(2) for j in range(1)]

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()

        self.tab_widget.addTab(self.tab1, 'Simple exports')
        self.tab_widget.addTab(self.tab2, 'Complex exports')

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
        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(150)
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

        for position, name in zip(self.positions, self.names):

            if name == '':
                continue
            labelposition = self.names.index(name)/self.numcolumns

            if labelposition != int(labelposition) and name != 'discourse' and name != 'speaker':
                widget = QtWidgets.QCheckBox(name)
                widget.setMinimumSize(175, 35)
                widget.toggled.connect(self.addColumn)
            elif name == 'discourse' or name == 'speaker':
                widget = QtWidgets.QCheckBox(name)
                widget.setMinimumSize(175, 35)
                widget.toggled.connect(self.addColumn)
            else:
                widget = QtWidgets.QLabel(name, self)
                widget.setMinimumSize(175, 35)
            self.grid.addWidget(widget, *position)

        self.selectall = QtWidgets.QPushButton('Select All', self)
        self.grid.addWidget(self.selectall, 5, 1, 20, 1)
        self.selectall.clicked.connect(self.checkAll)

        self.setGeometry(300, 300, 1000, 300)
        self.show()

    def tab2UI(self):

        layout = QtWidgets.QVBoxLayout()
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
        if sender != 'syllable position of previous phone' and sender != 'duration of the second syllable after the current one':
            idx = self.grid.indexOf(senderwidget)
            location = self.grid.getItemPosition(idx)
            rowcol = location[:2]
            for i in self.positions:
                if rowcol == i:
                    correctposition = self.positions.index(i)
                    item = self.names[correctposition]
                    for j in self.positions:
                        if i[0] == j[0] and j[1] == 0:
                            ind = self.positions.index(j)
                            category = self.names[ind]
            if category != sender:
                label = [category, sender]
            else:
                label = [sender]
            if label[0] == self.to_find:
                label = [sender]

        if sender == 'syllable position of previous phone':
            label = ['previous', 'phone', 'syllable_position']
        if sender == 'duration of the second syllable after the current one':
            label = ['following', 'following', 'syllable', 'duration']


        if label not in self.checked:
            self.checked.append(label)
            self.columnToAdd.emit(label)
        else:
            self.checked.remove(label)
            label.append('delete')
            label.append('delete2')
            self.columnToAdd.emit(label)

    def checkAll(self):
        unchecked = []
        for i in range(len(self.grid)):
            w = self.grid.itemAt(i).widget()
            if isinstance(w, QtWidgets.QCheckBox) and w.isChecked() == False:
                unchecked.append(w)
        if unchecked == []:
            for i in range(len(self.grid)):
                w = self.grid.itemAt(i).widget()
                if isinstance(w, QtWidgets.QCheckBox):
                    w.setChecked(False)
        else:
            for i in range(len(self.grid)):
                w = self.grid.itemAt(i).widget()
                if isinstance(w, QtWidgets.QCheckBox):# and w.isChecked() == False:
                    w.setChecked(True)

    def uncheck(self, to_uncheck):
        category = to_uncheck[0]
        if category != 'previous' and category != 'following':
            categoryindex = self.names.index(category)
            categoryposition = self.positions[categoryindex][0]
            for i in range(len(self.grid)):
                wcheckbox = self.grid.itemAt(i).widget()
                if wcheckbox.text() == to_uncheck[1]:
                    correctcheckbox = wcheckbox.text()
                    idx = self.grid.indexOf(wcheckbox)
                    location = self.grid.getItemPosition(idx)
                    rowcol = location[:2]
                    for j in self.positions:
                        if rowcol == j and j[0] == categoryposition:
                            correctposition = self.positions.index(j)
                            item = self.names[correctposition]
                            correctwidget = self.grid.itemAt(i).widget()
                            correctwidget.setChecked(False)
            if to_uncheck[0] == 'discourse':
                for i in range(len(self.grid)):
                    wcheckbox = self.grid.itemAt(i).widget()
                    if wcheckbox.text() == 'discourse':
                        wcheckbox.setChecked(False)
            if to_uncheck[0] == 'speaker':
                for i in range(len(self.grid)):
                    wcheckbox = self.grid.itemAt(i).widget()
                    if wcheckbox.text() == 'speaker':
                        wcheckbox.setChecked(False)
        elif to_uncheck[0] == 'previous':
            for i in range(len(self.grid2)):
                wcheckbox = self.grid2.itemAt(i).widget()
                if wcheckbox.text() == 'syllable position of previous phone':
                    wcheckbox.setChecked(False)
        elif to_uncheck[0] == 'following':
            for i in range(len(self.grid2)):
                wcheckbox = self.grid2.itemAt(i).widget()
                if wcheckbox.text() == 'duration of the second syllable after the current one':
                    wcheckbox.setChecked(False)

class ColumnBox(QtWidgets.QGroupBox):
    checkboxToUncheck = QtCore.pyqtSignal(object)
    exportHelpBroadcast = QtCore.pyqtSignal(object)
    def __init__(self, hierarchy, to_find):
        super(ColumnBox, self).__init__('Columns')
        self.hierarchy = hierarchy
        self.to_find = to_find

        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        mainWidget = QtWidgets.QWidget()

        mainWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        mainWidget.setLayout(self.mainLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        #scroll.setMinimumHeight(200)
        scroll.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.addButton = QtWidgets.QPushButton('+')
        self.addButton.clicked.connect(self.addNewColumn)
        layout.addWidget(self.addButton)

        self.setLayout(layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        policy = self.sizePolicy()
        policy.setVerticalStretch(1)
        self.setSizePolicy(policy)

    def sendForHelp(self, to_find):
        options = self.attributeWidget.attribute()
        self.exportHelpBroadcast.emit(options)

    def deleteWidget(self):
        widget = self.sender()
        self.mainLayout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
        categorywidget = widget.attributeWidget.mainLayout.itemAt(0).widget().currentText()
        if len(widget.attributeWidget.mainLayout) > 1:
            infowidget = widget.attributeWidget.mainLayout.itemAt(1).widget().currentText()
            self.checkboxToUncheck.emit([categorywidget, infowidget])
        else:
            self.checkboxToUncheck.emit([self.to_find, categorywidget])

    def setToFind(self, to_find):
        self.to_find = to_find
        for i in range(self.mainLayout.count()):
            self.mainLayout.itemAt(i).widget().setToFind(to_find)

    def addNewColumn(self):
        widget = ColumnWidget(self.hierarchy, self.to_find)
        widget.needsDelete.connect(self.deleteWidget)
        widget.exportHelpBroadcast.connect(self.exportHelpBroadcast.emit)

        self.mainLayout.addWidget(widget)

    def fillInColumn(self, label):
        if len(label) < 3 or label == ['previous', 'phone', 'syllable_position'] or label == ['following', 'following', 'syllable', 'duration']:
            widget = ColumnWidget(self.hierarchy, self.to_find)
            widget.needsDelete.connect(self.deleteWidget)
            self.mainLayout.addWidget(widget)
            defaultwidget = widget.attributeWidget.mainLayout.itemAt(0).widget()
            index = defaultwidget.findText(label[0])
            defaultwidget.setCurrentIndex(index)
            if len(label) > 1:
                defaultwidget2 = widget.attributeWidget.mainLayout.itemAt(1).widget()
                index2 = defaultwidget2.findText(label[1])
                defaultwidget2.setCurrentIndex(index2)
            if defaultwidget.currentText() == 'discourse' or defaultwidget.currentText() == 'speaker':
                defaultwidget2 = widget.attributeWidget.mainLayout.itemAt(1).widget()
                index2 = defaultwidget2.findText('name')
                defaultwidget2.setCurrentIndex(index2)
            if len(label) > 2:
                defaultwidget3 = widget.attributeWidget.mainLayout.itemAt(2).widget()
                index3 = defaultwidget3.findText(label[2])
                defaultwidget3.setCurrentIndex(index3)
            if len(label) > 3:
                defaultwidget4 = widget.attributeWidget.mainLayout.itemAt(3).widget()
                index4 = defaultwidget4.findText(label[3])
                defaultwidget4.setCurrentIndex(index4)

        unchecked = []
        if len(label) > 2 and label != ['previous', 'phone', 'syllable_position'] and label != ['following', 'following', 'syllable', 'duration']:
            #unchecked = []
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                checkdefault = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                if len(label) == 3 and label[0] != 'discourse' and label[0] != 'speaker':
                    if checkdefault == label[0]:
                        unchecked.append(match.widget())
                if len(label) == 4 and match.widget().attributeWidget.mainLayout.itemAt(1) != None:
                    checkdefault2 = match.widget().attributeWidget.mainLayout.itemAt(1).widget().currentText()
                    if checkdefault2 == label[1] and checkdefault == label[0]:
                        unchecked.append(match.widget())
                if label[0] == 'discourse' or label[0] == 'speaker':
                    if checkdefault == label[0]:
                        unchecked.append(match.widget())
        if len(label) > 4:
            #unchecked = []
            for i in range(len(self.mainLayout)):
                match = self.mainLayout.itemAt(i)
                checkdefault = match.widget().attributeWidget.mainLayout.itemAt(0).widget().currentText()
                if checkdefault == label[0]:
                    unchecked.append(match.widget())

        if len(unchecked) > 0:
            todelete = unchecked[0]
            self.mainLayout.removeWidget(todelete)
            todelete.setParent(None)
            todelete.deleteLater()

    def setColumns(self, columns):
        #Clear columns somehow
        while self.mainLayout.count() > 1:
            item = self.mainLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        for c in columns:
            widget = ColumnWidget(self.hierarchy, self.to_find)
            widget.needsDelete.connect(self.deleteWidget)
            self.mainLayout.addWidget(widget)
            widget.fromColumn(c)

    def columns(self):
        columns = []
        for i in range(self.mainLayout.count()):
            widget = self.mainLayout.itemAt(i).widget()
            if not isinstance(widget, ColumnWidget):
                continue
            columns.append(widget.toColumn())
        return columns

class ExportProfileDialog(QtWidgets.QDialog):
    exportHelpBroadcast = QtCore.pyqtSignal(object)
    def __init__(self, config, to_find, parent):
        super(ExportProfileDialog, self).__init__(parent)

        self.nameWidget = QtWidgets.QLineEdit()

        new_default_template = 'Export profile {}'
        index = 1
        while new_default_template.format(index) in available_export_profiles():
            index += 1
        self.nameWidget.setText(new_default_template.format(index))

        with CorpusContext(config) as c:
            hierarchy = c.hierarchy

        if to_find is not None:
            self.toFindWidget = QtWidgets.QLabel(to_find)
        else:
            self.toFindWidget = QtWidgets.QComboBox()
            for i, at in enumerate(hierarchy.highest_to_lowest):
                self.toFindWidget.addItem(at)

            self.toFindWidget.currentIndexChanged.connect(self.updateToFind)

        #self.BasicFilterBox = BasicFilterBox(hierarchy, to_find)

        layout = QtWidgets.QFormLayout()
        mainlayout = QtWidgets.QVBoxLayout()
        layout.addRow('Linguistic objects to find', self.toFindWidget)

        self.BasicColumnBox = BasicColumnBox(hierarchy, to_find)
        self.BasicColumnBox.setMaximumHeight(250)
        layout.addRow(self.BasicColumnBox)

        self.columnWidget = ColumnBox(hierarchy, to_find)

        layout.addRow(self.columnWidget)
        self.BasicColumnBox.columnToAdd.connect(self.columnWidget.fillInColumn)
        self.columnWidget.checkboxToUncheck.connect(self.BasicColumnBox.uncheck)
        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Run')
        self.saveButton = QtWidgets.QPushButton('Save as...')
        self.cancelButton = QtWidgets.QPushButton('Cancel')

        self.acceptButton.clicked.connect(self.accept)
        self.saveButton.clicked.connect(self.saveAs)
        self.cancelButton.clicked.connect(self.reject)

        self.columnWidget.exportHelpBroadcast.connect(self.exportHelpBroadcast.emit)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.saveButton)
        aclayout.addWidget(self.cancelButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

        self.setGeometry(400,100,800,700)
        self.setWindowTitle('Export profile')

    def name(self):
        return self.nameWidget.text()

    def updateToFind(self):
        to_find = self.toFindWidget.currentText()
        self.columnWidget.setToFind(to_find)

    def profile(self):
        profile = ExportProfile()
        profile.name = self.nameWidget.text()
        try:
            profile.to_find = self.toFindWidget.currentText()
        except AttributeError:
            profile.to_find = self.toFindWidget.text()
        profile.columns = self.columnWidget.columns()
        return profile

    def validate(self):
        return True # FIXME
        existing = set()
        for c in self.columnWidget.columns():
            if c.name in existing:
                reply = QtWidgets.QMessageBox.critical(self,
                        "Duplicate column names", 'Multiple columns name \'{}\', please make sure each column has a distinct name.'.format(c.name))
                return False
            existing.add(c.name)
        return True

    def accept(self):
        if self.validate():
            super(ExportProfileDialog, self).accept()

    def saveAs(self):
        from .main import SaveDialog
        dialog = SaveDialog(self.nameWidget.text(), self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            profile = self.profile()
            profile.name = dialog.value()
            profile.save_profile()

    def updateProfile(self, profile):
        self.nameWidget.setText(profile.name)
        if profile.to_find.endswith('_name') and self.hierarchy is not None:
            to_find = getattr(self.hierarchy, profile.to_find)
        else:
            to_find = profile.to_find
        #self.toFindWidget.setText(to_find)
        self.columnWidget.setColumns(profile.columns)
