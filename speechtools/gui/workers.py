import time
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.gui.workers import FunctionWorker

from speechtools.corpus import CorpusContext

from speechtools.utils import update_sound_files, gp_language_stops

from speechtools.acoustics.analysis import get_pitch

class QueryWorker(FunctionWorker):
    def run(self):
        time.sleep(0.1)
        try:
            a_type = self.kwargs['annotation_type']
            config = self.kwargs['config']

            with CorpusContext(config) as c:
                a_type = getattr(c, a_type)
                query = c.query_graph(a_type)
                query = query.times().columns(a_type.discourse.column_name('discourse'))
                results = query.all()
        except Exception as e:
            self.errorEncountered.emit(e)
            return

        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        self.dataReady.emit((query, results))

class Lab1QueryWorker(QueryWorker):
    def run(self):
        time.sleep(0.1)
        print('beginning')
        try:
            config = self.kwargs['config']
            try:
                stops = gp_language_stops[config.corpus_name]
            except KeyError:
                print('Couldn\'t find corpus name in stops, defaulting to p, t, k, b, d, g')
                stops = ['p','t','k','b','d','g']
            with CorpusContext(config) as c:
                a_type = c.hierarchy.lowest
                w_type = c.hierarchy[a_type]
                utt_type = c.hierarchy.highest
                a_type = getattr(c, a_type)
                w_type = getattr(a_type, w_type)
                utt_type = getattr(a_type, utt_type)
                q = c.query_graph(a_type)
                q = q.filter(a_type.phon4lab1 == True)
                #print('Number found: {}'.format(q.count()))
                q = q.columns(a_type.label.column_name('Stop'),
                            a_type.begin.column_name('Begin'),
                            a_type.end.column_name('End'),
                            w_type.label.column_name('Word'),
                            a_type.checked.column_name('Annotated'),
                            a_type.speaker.name.column_name('Speaker'),
                            a_type.discourse.name.column_name('Discourse'))
                #q = q.limit(100)
                results = q.all()
        except Exception as e:
            raise
            self.errorEncountered.emit(e)
            return
        print('finished')
        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return

        self.dataReady.emit((q, results))

class AnnotatedQueryWorker(QueryWorker):
    pass

class ExportQueryWorker(QueryWorker):
    def run(self):
        time.sleep(0.1)
        print('beginning export')
        try:
            config = self.kwargs['config']
            export_path = self.kwargs['path']
            try:
                stops = gp_language_stops[config.corpus_name]
            except KeyError:
                print('Couldn\'t find corpus name in stops, defaulting to p, t, k, b, d, g')
                stops = ['p','t','k','b','d','g']
            with CorpusContext(config) as c:
                a_type = c.hierarchy.lowest
                w_type = c.hierarchy[a_type]
                utt_type = c.hierarchy.highest
                a_type = getattr(c, a_type)
                w_type = getattr(a_type, w_type)
                utt_type = getattr(a_type, utt_type)
                q = c.query_graph(a_type)
                q = q.filter(a_type.phon4lab1 == True)
                #print('Number found: {}'.format(q.count()))
                q = q.columns(a_type.label.column_name('Stop'),
                            a_type.begin.column_name('Begin'),
                            a_type.end.column_name('End'),
                            a_type.duration.column_name('Duration'))
                if 'burst' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    q = q.columns(a_type.burst.begin.column_name('Burst_begin'),
                            a_type.burst.end.column_name('Burst_end'),
                            a_type.burst.duration.column_name('Burst_duration'))
                if 'voicing' in c.hierarchy.subannotations[c.hierarchy.lowest]:
                    q = q.columns(a_type.voicing.begin.column_name('Voicing_begin'),
                                a_type.voicing.end.column_name('Voicing_end'),
                                a_type.voicing.duration.column_name('Voicing_duration'))

                q = q.columns(w_type.label.column_name('Word'),
                            w_type.begin.column_name('Word_begin'),
                            w_type.end.column_name('Word_end'),
                            w_type.duration.column_name('Word_duration'),
                            w_type.transcription.column_name('Word_transcription'),
                            #a_type.following.label.column_name('Following_segment'),
                            #a_type.following.begin.column_name('Following_segment_begin'),
                            #a_type.following.end.column_name('Following_segment_end'),
                            #a_type.following.duration.column_name('Following_segment_duration'),
                            a_type.following.following.label.column_name('Following_following_segment'),
                            a_type.following.following.begin.column_name('Following_following_segment_begin'),
                            a_type.following.following.end.column_name('Following_following_segment_end'),
                            a_type.following.following.duration.column_name('Following_following_segment_duration'),
                            a_type.checked.column_name('Annotated'),
                            a_type.speaker.name.column_name('Speaker'),
                            a_type.discourse.name.column_name('Discourse'))
                #q = q.limit(100)
                print(q.cypher())
                results = q.to_csv(export_path)
        except Exception as e:
            raise
            self.errorEncountered.emit(e)
            return
        print('finished')
        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return

        self.dataReady.emit((q, results))

class DiscourseQueryWorker(QueryWorker):
    audioReady = QtCore.pyqtSignal(object)
    annotationsReady = QtCore.pyqtSignal(object)
    def run(self):
        print('beginning discourse query')
        time.sleep(0.1)
        try:
            a_type = self.kwargs['word_type']
            s_type = self.kwargs['seg_type']
            config = self.kwargs['config']
            discourse = self.kwargs['discourse']
            with CorpusContext(config) as c:
                audio_file = c.discourse_sound_file(discourse)
                self.audioReady.emit(audio_file)
                word = getattr(c,a_type)
                q = c.query_graph(word).filter(word.discourse.name == discourse)
                preloads = []
                if a_type in c.hierarchy.subannotations:
                    for s in c.hierarchy.subannotations[t]:
                        preloads.append(getattr(word, s))
                for t in c.hierarchy.get_lower_types(a_type):
                    preloads.append(getattr(word, t))
                q = q.preload(*preloads)
                q = q.order_by(word.begin)
                #annotations = c.query_acoustics(q).pitch('reaper').all()
                annotations = q.all()
        except Exception as e:
            raise
            self.errorEncountered.emit(e)
            print(e)
            return

        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        self.annotationsReady.emit(annotations)
        print('done!')
        print('finished discourse query')

class BoundaryGeneratorWorker(QueryWorker):
    pass

class SpectrogramGeneratorWorker(QueryWorker):
    pass

class FormantGeneratorWorker(QueryWorker):
    pass

class PitchGeneratorWorker(QueryWorker):
    def run(self):
        print('beginning pitch work')
        config = self.kwargs['config']
        algorithm = self.kwargs['algorithm']
        sound_file = self.kwargs['sound_file']
        with CorpusContext(config) as c:
            pitch_list = get_pitch(c, sound_file, algorithm)
            pitch_list = np.array([[x.time, x.F0] for x in pitch_list])
        self.dataReady.emit(pitch_list)
        print('finished pitch work')

class AudioFinderWorker(QueryWorker):
    def run(self):
        print('beginning audio finding')
        config = self.kwargs['config']
        directory = self.kwargs['directory']
        with CorpusContext(config) as c:
            update_sound_files(c, directory)
            all_found = c.has_all_sound_files()
        self.dataReady.emit(all_found)
        print('finished audio finding')

class AudioCheckerWorker(QueryWorker):
    def run(self):
        print('beginning audio checking')
        config = self.kwargs['config']
        with CorpusContext(config) as c:
            all_found = c.has_all_sound_files()
        self.dataReady.emit(all_found)
        print('finished audio checking')

