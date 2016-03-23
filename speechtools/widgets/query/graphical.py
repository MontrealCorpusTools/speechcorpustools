import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum, Count

from ..base import NonScrollingComboBox

class AnnotationRect(QtWidgets.QGraphicsTextItem):
    clicked = QtCore.pyqtSignal(object)
    def __init__(self, text, hierarchy, pos = 0):
        super(AnnotationRect, self).__init__(text)
        self.linear_position = pos
        self.hierarchy = hierarchy
        for i, at in enumerate(self.hierarchy.lowest_to_highest):
            if at == text:
                self.hierarchy_position = i
                break

    def paint(self, painter, option, widget = 0):
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtGui.QColor(230,230,230))
        r = option.rect
        mod = 50 * self.hierarchy_position
        r.setWidth(r.width() + mod)
        r.setX(0 - r.width() / 2)
        painter.drawRect(r)
        super(AnnotationRect, self).paint(painter, option, widget)

    def mousePressEvent(self, event):
        super(AnnotationRect, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.toPlainText())

class FilterWidgetItem(QtWidgets.QWidget):
    def __init__(self, column, value):
        super(FilterWidgetItem, self).__init__()

        self.column = column
        self.value = value

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(column))

        if value in (int, float):
            self.compWidget = NonScrollingComboBox()
            self.compWidget.addItem('=')
            self.compWidget.addItem('!=')
            self.compWidget.addItem('>')
            self.compWidget.addItem('>=')
            self.compWidget.addItem('<')
            self.compWidget.addItem('<=')
            layout.addWidget(self.compWidget)
            self.valueWidget = QtWidgets.QLineEdit()
            layout.addWidget(self.valueWidget)
        self.setLayout(layout)

class SubsetWidgetItem(QtWidgets.QWidget):
    def __init__(self):
        super(SubsetWidgetItem, self).__init__()

        self.subsetList = NonScrollingComboBox()
        self.subsetList.addItem('')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Subset'))
        layout.addWidget(self.subsetList)
        self.setLayout(layout)

    def clear(self):
        self.subsetList.clear()
        self.subsetList.addItem('')

    def addItems(self, items):
        for i in items:
            self.subsetList.addItem(i)

class FilterWidget(QtWidgets.QGroupBox):
    def __init__(self):
        self.hierarchy = None
        super(FilterWidget, self).__init__('Filters')

        mainlayout = QtWidgets.QVBoxLayout()

        self.filterLayout = QtWidgets.QVBoxLayout()

        self.subsetWidget = SubsetWidgetItem()

        self.filterLayout.addWidget(self.subsetWidget)

        self.attributeBox = QtWidgets.QGroupBox('Attributes')

        self.attributeBox.setLayout(self.filterLayout)

        mainlayout.addWidget(self.attributeBox)

        self.speakerBox = QtWidgets.QGroupBox('Speakers')

        mainlayout.addWidget(self.speakerBox)
        self.discourseBox = QtWidgets.QGroupBox('Discourses')

        mainlayout.addWidget(self.discourseBox)

        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(mainlayout)

        layout = QtWidgets.QVBoxLayout()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(mainWidget)
        scroll.setMinimumHeight(200)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        layout.addWidget(scroll)

        self.acceptButton = QtWidgets.QPushButton('Add filters')

        layout.addWidget(self.acceptButton)

        self.setLayout(layout)

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy

    def updateAnnotation(self, text):
        while self.filterLayout.count():
            item = self.filterLayout.takeAt(0)
            if item.widget() is None:
                continue
            item.widget().deleteLater()

        self.subsetWidget = SubsetWidgetItem()

        self.filterLayout.addWidget(self.subsetWidget)
        subsets = []
        if text in self.hierarchy.subset_tokens:
            for s in self.hierarchy.subset_tokens[text]:
                subsets.append(s)
        if text in self.hierarchy.subset_types:
            for s in self.hierarchy.subset_types[text]:
                subsets.append(s)
        self.subsetWidget.addItems(subsets)
        if text in self.hierarchy.type_properties:
            for p, v in self.hierarchy.type_properties[text]:
                self.filterLayout.addWidget(FilterWidgetItem(p, v))
        if text in self.hierarchy.token_properties:
            for p, v in self.hierarchy.token_properties[text]:
                self.filterLayout.addWidget(FilterWidgetItem(p, v))

class GraphicalQuery(QtWidgets.QWidget):
    vert_step = 50
    horz_step = 200
    def __init__(self):
        super(GraphicalQuery, self).__init__()
        self.hierarchy = None
        visualLayout = QtWidgets.QHBoxLayout()

        self.filterWidget = FilterWidget()

        self.queryScene = QtWidgets.QGraphicsScene()
        self.queryView = QtWidgets.QGraphicsView(self.queryScene)
        self.queryView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.queryView.customContextMenuRequested.connect(self.showMenu)

        visualLayout.addWidget(self.queryView)
        visualLayout.addWidget(self.filterWidget)

        self.setLayout(visualLayout)

    def showMenu(self, pos):

        menu = QtWidgets.QMenu()
        items = self.queryView.items(pos)
        if not items:
            return
        previous_action = QtWidgets.QAction('Add previous annotation', self)
        following_action = QtWidgets.QAction('Add following annotation', self)

        menu.addAction(previous_action)
        menu.addAction(following_action)

        action = menu.exec_(self.mapToGlobal(pos))
        if action == previous_action:
            new_pos = items[0].linear_position - 1
        elif action == following_action:
            new_pos = items[0].linear_position + 1
        else:
            return
        self.addNew(items[0].toPlainText(), new_pos)

    def addNew(self, text, pos):
        for i, at in enumerate(self.hierarchy.highest_to_lowest):
            if at == text:
                break
        ar = AnnotationRect(text, self.hierarchy)
        ar.clicked.connect(self.filterWidget.updateAnnotation)
        ar.setPos(self.horz_step * pos, self.vert_step*i)

        br = ar.boundingRect()
        br.setWidth(br.width() + self.vert_step*i)
        self.queryScene.addItem(ar)

    def setHierarchy(self, hierarchy):
        self.hierarchy = hierarchy
        self.filterWidget.setHierarchy(hierarchy)
        self.queryScene.clear()

        for i, at in enumerate(hierarchy.highest_to_lowest):
            ar = AnnotationRect(at, hierarchy)
            ar.clicked.connect(self.filterWidget.updateAnnotation)
            ar.setPos(0, self.vert_step*i)
            br = ar.boundingRect()
            br.setWidth(br.width() + self.vert_step*i)
            self.queryScene.addItem(ar)
