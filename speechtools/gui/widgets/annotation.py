
from PyQt5 import QtGui, QtCore, QtWidgets

class SubannotationDialog(QtWidgets.QDialog):
    def __init__(self, type = None,
                subannotation_types = None, parent = None):
        super(SubannotationDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()

        if subannotation_types is None:
            subannotation_types = ['burst', 'closure', 'voicing', 'preaspiration']

        self.typeEdit = QtWidgets.QComboBox()
        for sa in subannotation_types:
            self.typeEdit.addItem(sa)

        layout.addRow('Type', self.typeEdit)

        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Save')
        self.acceptButton.clicked.connect(self.accept)
        self.rejectButton = QtWidgets.QPushButton('Cancel')
        self.rejectButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.rejectButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

        self.setWindowTitle('Add subannotation')

    def value(self):
        return self.typeEdit.currentText()

class NoteDialog(QtWidgets.QDialog):
    def __init__(self, annotation, parent = None):
        super(NoteDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()

        self.typeEdit = QtWidgets.QLineEdit()
        self.typeEdit.setText('notes')
        self.typeEdit.setEnabled(False)

        self.notesEdit = QtWidgets.QLineEdit()
        if annotation.notes is not None:
            self.notesEdit.setText(annotation.notes)

        layout.addRow('Note type', self.typeEdit)
        layout.addRow('Note contents', self.notesEdit)

        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addLayout(layout)

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Save')
        self.acceptButton.clicked.connect(self.accept)
        self.rejectButton = QtWidgets.QPushButton('Cancel')
        self.rejectButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.rejectButton)

        mainlayout.addLayout(aclayout)

        self.setLayout(mainlayout)

        self.setWindowTitle('Add note')

    def accept(self):
        contents = self.notesEdit.text()
        if not contents:
            self.reject()
        else:
            super(NoteDialog, self).accept()

    def value(self):
        type = self.typeEdit.text()
        if not type:
            type = 'notes'
        contents = self.notesEdit.text()
        return {type: contents}
