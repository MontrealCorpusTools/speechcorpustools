
from PyQt5 import QtGui, QtCore, QtWidgets



from .plot import SCTAudioWidget


from speechtools.corpus import CorpusContext


class ViewWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(ViewWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()

        self.discourseList = QtWidgets.QListWidget()
        self.discourseList.setMaximumWidth(300)
        self.discourseList.currentItemChanged.connect(self.loadDiscourse)

        layout.addWidget(self.discourseList)
        self.plotWidget = SCTAudioWidget()

        layout.addWidget(self.plotWidget.native)

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
        self.plotWidget.plot(audio_file, annotations)


    def updateConfig(self, config):
        self.config = config
        self.discourseList.clear()
        if self.config.corpus_name == '':
            return
        with CorpusContext(self.config) as c:
            for d in sorted(c.discourses):
                self.discourseList.addItem(d)
