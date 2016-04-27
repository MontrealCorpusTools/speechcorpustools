


from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from ...profiles import available_export_profiles, ExportProfile, Column

from .basic import AttributeSelect as QueryAttributeSelect, SpeakerAttributeSelect

class AttributeSelect(QueryAttributeSelect):
    def __init__(self, hierarchy, to_find):
        QtWidgets.QComboBox.__init__(self)
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
        for k in hierarchy.highest_to_lowest:
            if k != to_find:
                self.addItem(k)
        self.addItem('speaker')
        self.addItem('discourse')
        if to_find in hierarchy.subannotations:
            for s in sorted(hierarchy.subannotations[to_find]):
                self.addItem(s)

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

        self.setLayout(mainLayout)

    def updateColumnName(self, name):
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

class ColumnBox(QtWidgets.QGroupBox):
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

    def deleteWidget(self):
        widget = self.sender()
        self.mainLayout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()

    def setToFind(self, to_find):
        self.to_find = to_find
        for i in range(self.mainLayout.count()):
            self.mainLayout.itemAt(i).widget().setToFind(to_find)

    def addNewColumn(self):
        widget = ColumnWidget(self.hierarchy, self.to_find)
        widget.needsDelete.connect(self.deleteWidget)
        self.mainLayout.addWidget(widget)

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

        layout = QtWidgets.QFormLayout()
        mainlayout = QtWidgets.QVBoxLayout()
        layout.addRow('Linguistic objects to find', self.toFindWidget)

        self.columnWidget = ColumnBox(hierarchy, to_find)
        layout.addRow(self.columnWidget)

        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Run')
        self.saveButton = QtWidgets.QPushButton('Save as...')
        self.cancelButton = QtWidgets.QPushButton('Cancel')

        self.acceptButton.clicked.connect(self.accept)
        self.saveButton.clicked.connect(self.saveAs)
        self.cancelButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.saveButton)
        aclayout.addWidget(self.cancelButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

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
