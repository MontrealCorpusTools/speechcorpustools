
from PyQt5 import QtGui, QtCore, QtWidgets

class NonScrollingComboBox(QtWidgets.QComboBox):
    def __init__(self, parent = None):
        super(NonScrollingComboBox, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()

class DetailedMessageBox(QtWidgets.QMessageBox):
    # Adapted from http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    def __init__(self, *args, **kwargs):
        super(DetailedMessageBox, self).__init__(*args, **kwargs)
        self.setWindowTitle('Error encountered')
        self.setIcon(QtWidgets.QMessageBox.Critical)
        self.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.setText("Something went wrong!")
        self.setInformativeText("Please copy the text below and send to Michael.")

        self.setFixedWidth(200)

    def resizeEvent(self, event):
        result = super(DetailedMessageBox, self).resizeEvent(event)
        details_box = self.findChild(QtWidgets.QTextEdit)
        if details_box is not None:
            details_box.setFixedHeight(details_box.sizeHint().height())
        return result

class CollapsibleWidgetPair(QtWidgets.QSplitter):
    def __init__(self, orientation, widgetOne, widgetTwo, collapsible = 1, parent = None):
        super(CollapsibleWidgetPair, self).__init__(orientation, parent)
        self.collapsible = collapsible
        self.addWidget(widgetOne)
        self.addWidget(widgetTwo)
        self.setCollapsible(0, False)
        self.setCollapsible(1, False)

        if self.orientation() == QtCore.Qt.Horizontal:
            if self.collapsible == 1:
                self.uncollapsed_arrow = QtCore.Qt.RightArrow
                self.collapsed_arrow = QtCore.Qt.LeftArrow
            else:
                self.uncollapsed_arrow = QtCore.Qt.LeftArrow
                self.collapsed_arrow = QtCore.Qt.RightArrow
        else:
            if self.collapsible == 1:
                self.uncollapsed_arrow = QtCore.Qt.DownArrow
                self.collapsed_arrow = QtCore.Qt.UpArrow
            else:
                self.uncollapsed_arrow = QtCore.Qt.UpArrow
                self.collapsed_arrow = QtCore.Qt.DownArrow

        #size_unit = get_system_font_height()
        #handle = self.handle(1)
        #self.button = QtWidgets.QToolButton(handle)
        #if self.orientation() == QtCore.Qt.Horizontal:
        #    self.button.setMinimumHeight(8 * size_unit)
        #    layout = QtWidgets.QVBoxLayout()
        #    self.button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        #else:
        #    self.button.setMinimumWidth(8 * size_unit)
        #    layout = QtWidgets.QHBoxLayout()
        #    self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)

        #self.button.setArrowType(self.uncollapsed_arrow)
        #layout.setContentsMargins(0, 0, 0, 0)
        #self.button.clicked.connect(self.onCollapse)
        #layout.addWidget(self.button)
        #handle.setLayout(layout)
        #self.setHandleWidth(size_unit)

    #def onCollapse(self):
    #    if self.collapsible == 1:
    #        collapsed_size = [1, 0]
    #        uncollapsed_size = [1000,1]
    #    else:
    #        collapsed_size = [0, 1]
    #        uncollapsed_size = [1, 1000]
    #    if self.sizes()[self.collapsible]:
    #        self.setSizes(collapsed_size)
    #        self.button.setArrowType(self.collapsed_arrow)
    #    else:
    #        self.setSizes(uncollapsed_size)
    #        self.button.setArrowType(self.uncollapsed_arrow)


class DataListWidget(QtWidgets.QListWidget):
    def __init__(self, plot, plot_type, parent = None):
        super(DataListWidget, self).__init__(parent)
        self.plot = plot
        self.plot_type = plot_type
        self.itemSelectionChanged.connect(self.update_plot)

    def selectAll(self):
        for i in range(self.count()): self.item(i).setSelected(True)

    def update_plot(self):
        labels = [i.text() for i in self.selectedItems()]
        self.plot.update_data(labels, self.plot_type)


class RadioSelectWidget(QtWidgets.QGroupBox):
    def __init__(self,title, options, actions=None, enabled=None,parent=None):
        super(RadioSelectWidget, self).__init__(title, parent)
        self.is_enabled = True
        self.actions = None
        self.enabled = None
        self.setLayout(QtWidgets.QFormLayout())
        self.setOptions(options, actions, enabled)

    def initOptions(self):
        self.widgets = []
        for key in self.options.keys():
            w = QtWidgets.QRadioButton(key)
            if self.actions is not None:
                w.clicked.connect(self.actions[key])
            if self.enabled is not None:
                w.setEnabled(self.enabled[key])
            if not self.is_enabled:
                w.setEnabled(False)
            self.widgets.append(w)
            self.layout().addRow(w)
        self.widgets[0].setChecked(True)

    def setOptions(self, options, actions = None, enabled = None):
        for i in reversed(range(self.layout().count())):
            w = self.layout().itemAt(i).widget()
            self.layout().removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self.options = options
        if actions is not None:
            self.actions = actions
        if enabled is not None:
            self.enabled = enabled
        self.initOptions()


    def initialClick(self):
        self.widgets[0].click()

    def click(self,index):
        if index >= len(self.widgets):
            return
        self.widgets[index].click()

    def value(self):
        for w in self.widgets:
            if w.isChecked():
                return self.options[w.text()]
        return None

    def displayValue(self):
        for w in self.widgets:
            if w.isChecked():
                return w.text()
        return ''

    def disable(self):
        self.is_enabled = False
        for w in self.widgets:
            w.setEnabled(False)

    def enable(self):
        self.is_enabled = True
        for w in self.widgets:
            if self.enabled is not None:
                w.setEnabled(self.enabled[key])
            else:
                w.setEnabled(True)
