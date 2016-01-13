
from PyQt5 import QtGui, QtCore, QtWidgets



from .plot import SCTAudioWidget, SCTSummaryWidget


from speechtools.corpus import CorpusContext


class ViewWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(ViewWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()

        self.discourseList = QtWidgets.QListWidget()
        self.discourseList.currentItemChanged.connect(self.loadDiscourse)
        
        tabs = QtWidgets.QTabWidget()

        self.discourseWidget = SCTAudioWidget()

        self.summaryWidget = SCTSummaryWidget(self)

        self.dataTabs = QtWidgets.QTabWidget()

        self.phoneList = DataListWidget(self.summaryWidget, 'p')
        self.phoneList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.wordList = DataListWidget(self.summaryWidget, 'w')
        self.wordList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.dataTabs.addTab(self.phoneList, 'Phones')
        self.dataTabs.addTab(self.wordList, 'Words')

        summaryTab = CollapsibleWidgetPair(self, self.summaryWidget.native, self.dataTabs)
        discourseTab = CollapsibleWidgetPair(self, self.discourseWidget.native, self.discourseList, both_open = True)

        tabs.addTab(discourseTab, 'Discourse')
        tabs.addTab(summaryTab, 'Summary')

        layout.addWidget(tabs, 1)

        self.setLayout(layout)

    def loadDiscourse(self):
        discourse = self.discourseList.currentItem().text()
        with CorpusContext(self.config) as c:
            q = c.query_graph(c.word).filter(c.word.discourse == discourse).times()
            q = q.order_by(c.word.begin)

            phone_annotation = c.lowest_annotation

            word_sub_phone = getattr(c.word, phone_annotation.type)

            q.columns(word_sub_phone.label.column_name('phones'),
                    word_sub_phone.begin.column_name('phone_begins'),
                    word_sub_phone.end.column_name('phone_ends'))

            #annotations = c.query_acoustics(q).pitch('reaper').all()
            annotations = q.all()
            audio_file = c.discourse_sound_file(discourse).filepath
        print(annotations[0])
        self.discourseWidget.plot(audio_file, annotations)
        self.summaryWidget.plot(annotations)

        self.phoneList.selectAll()
        self.wordList.selectAll()


    def updateConfig(self, config):
        self.config = config
        self.discourseList.clear()
        if self.config.corpus_name == '':
            return
        with CorpusContext(self.config) as c:
            for d in sorted(c.discourses):
                self.discourseList.addItem(d)


class CollapsibleWidgetPair(QtWidgets.QWidget):
    def __init__(self, parent, leftWidget, rightWidget, both_open = False):
        super(CollapsibleWidgetPair, self).__init__(parent)
        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.addWidget(leftWidget)
        self.splitter.addWidget(rightWidget)
        self.splitter.setSizes([1000,1] if both_open else [1,0])
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.splitter)
        handle = self.splitter.handle(1)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.button = QtWidgets.QToolButton(handle)
        self.button.setArrowType(QtCore.Qt.RightArrow)
        self.button.clicked.connect(self.onCollapse)
        layout.addWidget(self.button)
        handle.setLayout(layout)

    def onCollapse(self):
        if self.splitter.sizes()[1]:
            self.splitter.setSizes([1,0])
            self.button.setArrowType(QtCore.Qt.RightArrow)
        else:
            self.splitter.setSizes([1000, 1])
            self.button.setArrowType(QtCore.Qt.LeftArrow)


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
