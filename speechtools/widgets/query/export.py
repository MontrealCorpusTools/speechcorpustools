


from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from ...profiles import available_export_profiles, ExportProfile, Column


class AttributeSelect(QtWidgets.QComboBox):
    def __init__(self, hierarchy, to_find):
        super(AttributeSelect, self).__init__()
        for k,t in sorted(hierarchy.token_properties[to_find]):
            self.addItem(k)
        for k,t in sorted(hierarchy.type_properties[to_find]):
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

    def label(self):
        return self.currentText()

class AttributeWidget(QtWidgets.QWidget):
    finalChanged = QtCore.pyqtSignal(object)
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(AttributeWidget, self).__init__()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(0,5,0,5)
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
            item.widget().deleteLater()
        current_annotation_type = self.annotationType()
        if combobox.currentText() in self.hierarchy.annotation_types:
            widget = AttributeSelect(self.hierarchy, combobox.currentText())
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        elif combobox.currentText() in ['previous','following']:
            widget = AttributeSelect(self.hierarchy, current_annotation_type)
            widget.currentIndexChanged.connect(self.updateAttribute)
            self.mainLayout.addWidget(widget)
        self.finalChanged.emit(self.mainLayout.itemAt(self.mainLayout.count() - 1).widget().label())

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
            if not isinstance(widget, AttributeSelect):
                continue
            text = widget.currentText()
            att.append(text)
        return tuple(att)

    def setAttribute(self, attribute):
        self.initWidget()
        for a in attribute[1:]:
            ind = self.mainLayout.count() - 1
            widget = self.mainLayout.itemAt(ind).widget()
            widget.setCurrentIndex(widget.findText(a))

class ColumnWidget(QtWidgets.QWidget):
    def __init__(self, hierarchy, to_find):
        self.hierarchy = hierarchy
        self.to_find = to_find
        super(ColumnWidget, self).__init__()

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        self.attributeWidget = AttributeWidget(self.hierarchy, self.to_find)
        self.attributeWidget.finalChanged.connect(self.updateColumnName)
        mainLayout.addWidget(self.attributeWidget)

        label = QtWidgets.QLabel('Output name:')
        mainLayout.addWidget(label)

        self.nameWidget = QtWidgets.QLineEdit()
        self.attributeWidget.setToFind(to_find)
        mainLayout.addWidget(self.nameWidget)
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
        self.attributeWidget.setAttribute(attribute)
        self.nameWidget.setText(column.name)

class ColumnBox(QtWidgets.QGroupBox):
    def __init__(self, hierarchy, to_find):
        super(ColumnBox, self).__init__('Columns')
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.hierarchy = hierarchy
        self.to_find = to_find
        self.addButton = QtWidgets.QPushButton('+')
        self.addButton.clicked.connect(self.addNewColumn)
        self.mainLayout.addWidget(self.addButton)
        self.setLayout(self.mainLayout)

    def setToFind(self, to_find):
        self.to_find = to_find
        for i in range(self.mainLayout.count() - 1):
            self.mainLayout.itemAt(i).widget().setToFind(to_find)

    def addNewColumn(self):
        widget = ColumnWidget(self.hierarchy, self.to_find)
        self.mainLayout.insertWidget(self.mainLayout.count() - 1, widget)

    def setColumns(self, columns):
        #Clear columns somehow
        while self.mainLayout.count() > 1:
            item = self.mainLayout.takeAt(self.mainLayout.count() - 2)
            if item.widget() is None:
                continue
            item.widget().deleteLater()
        for c in columns:
            widget = ColumnWidget(self.hierarchy, self.to_find)
            widget.fromColumn(c)
            self.mainLayout.insertWidget(0, widget)

    def columns(self):
        columns = []
        for i in range(self.mainLayout.count()):
            widget = self.mainLayout.itemAt(i).widget()
            if not isinstance(widget, ColumnWidget):
                continue
            columns.append(widget.toColumn())
        return columns

class NewExportProfileDialog(QtWidgets.QDialog):
    def __init__(self, config, to_find, parent):
        super(NewExportProfileDialog, self).__init__(parent)

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
        layout.addRow('Profile name', self.nameWidget)
        layout.addRow('Linguistic objects to find', self.toFindWidget)

        self.columnWidget = ColumnBox(hierarchy, to_find)
        layout.addRow(self.columnWidget)

        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Save and run')
        self.cancelButton = QtWidgets.QPushButton('Cancel')

        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.cancelButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

        self.setWindowTitle('New export profile')

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

    def accept(self):
        self.profile().save_profile()
        super(NewExportProfileDialog, self).accept()
