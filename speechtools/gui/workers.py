import time

from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.gui.workers import FunctionWorker

from speechtools.corpus import CorpusContext

class QueryWorker(FunctionWorker):

    def run(self):
        time.sleep(0.1)
        try:
            a_type = self.kwargs['annotation_type']
            config = self.kwargs['config']

            with CorpusContext(config) as c:
                a_type = getattr(c, a_type)
                query = c.query_graph(a_type)
                results = query.all()
        except Exception as e:
            self.errorEncountered.emit(e)
            return

        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        self.dataReady.emit((query, results))


class DiscourseQueryWorker(QueryWorker):
    audioReady = QtCore.pyqtSignal(object)
    annotationsReady = QtCore.pyqtSignal(object)
    def run(self):
        time.sleep(0.1)
        try:
            a_type = self.kwargs['word_type']
            s_type = self.kwargs['seg_type']
            config = self.kwargs['config']
            discourse = self.kwargs['discourse']

            with CorpusContext(config) as c:
                audio_file = c.discourse_sound_file(discourse).filepath
                self.audioReady.emit(audio_file)
                word = getattr(c,a_type)
                q = c.query_graph(word).filter(word.discourse == discourse).times()
                q = q.order_by(word.begin)

                word_sub_phone = getattr(word, s_type)

                q.columns(word_sub_phone.label.column_name('phones'),
                        word_sub_phone.begin.column_name('phone_begins'),
                        word_sub_phone.end.column_name('phone_ends'))

                #annotations = c.query_acoustics(q).pitch('reaper').all()
                annotations = q.all()
        except Exception as e:
            self.errorEncountered.emit(e)
            print(e)
            return

        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        self.annotationsReady.emit(annotations)
        print('done!')
