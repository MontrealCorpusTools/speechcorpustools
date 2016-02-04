
import sys
import traceback
import time
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.gui.workers import FunctionWorker

from polyglotdb.exceptions import ConnectionError, NetworkAddressError, TemporaryConnectionError, PGError

from speechtools.corpus import CorpusContext

from speechtools.utils import update_sound_files, gp_language_stops

from speechtools.acoustics.analysis import get_pitch

class QueryWorker(FunctionWorker):
    connectionIssues = QtCore.pyqtSignal()
    def run(self):
        time.sleep(0.1)
        print('beginning')
        try:
            success = False
            tries = 0
            max_tries = 5
            while not success and tries < max_tries:
                try:
                    results = self.run_query()
                    success = True
                except (ConnectionError, NetworkAddressError, TemporaryConnectionError):
                    tries += 1
                    if tries == 2:
                        self.connectionIssues.emit()
            if not success:
                raise(ConnectionError('The query could not be completed.  Please check your internet connectivity.'))
        except Exception as e:
            if not isinstance(e, PGError):
                exc_type, exc_value, exc_traceback = sys.exc_info()
                e = ''.join(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback))
            self.errorEncountered.emit(e)
            return
        print('finished')
        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return

        self.dataReady.emit(results)

    def run_query(self):
        a_type = self.kwargs['annotation_type']
        config = self.kwargs['config']

        with CorpusContext(config) as c:
            a_type = getattr(c, a_type)
            query = c.query_graph(a_type)
            query = query.times().columns(a_type.discourse.column_name('discourse'))
            results = query.all()
        return query, results

class Lab1QueryWorker(QueryWorker):
    def run_query(self):
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
        return q, results



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
                            a_type.following.label.column_name('Following_segment'),
                            a_type.following.begin.column_name('Following_segment_begin'),
                            a_type.following.end.column_name('Following_segment_end'),
                            a_type.following.duration.column_name('Following_segment_duration'),
                            a_type.following.following.label.column_name('Following_following_segment'),
                            a_type.following.following.begin.column_name('Following_following_segment_begin'),
                            a_type.following.following.end.column_name('Following_following_segment_end'),
                            a_type.following.following.duration.column_name('Following_following_segment_duration'),
                            a_type.checked.column_name('Annotated'),
                            a_type.speaker.name.column_name('Speaker'),
                            a_type.discourse.name.column_name('Discourse'),
                            w_type.utterance.phones.rate.column_name('Speaking_rate'))
                #q = q.limit(100)
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

class DiscourseAudioWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        discourse = self.kwargs['discourse']
        with CorpusContext(config) as c:
            audio_file = c.discourse_sound_file(discourse)
            if audio_file is not None:
                c.sql_session.expunge(audio_file)
        return audio_file

class DiscourseQueryWorker(QueryWorker):
    def run_query(self):
        a_type = self.kwargs['word_type']
        s_type = self.kwargs['seg_type']
        config = self.kwargs['config']
        discourse = self.kwargs['discourse']
        with CorpusContext(config) as c:
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
        return annotations

class BoundaryGeneratorWorker(QueryWorker):
    pass

class SpectrogramGeneratorWorker(QueryWorker):
    pass

class FormantGeneratorWorker(QueryWorker):
    pass

class PitchGeneratorWorker(QueryWorker):
    def run(self):
        return
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
        config = self.kwargs['config']
        directory = self.kwargs['directory']
        with CorpusContext(config) as c:
            update_sound_files(c, directory)
            all_found = c.has_all_sound_files()
        self.dataReady.emit(all_found)

class AudioCheckerWorker(QueryWorker):
    def run(self):
        config = self.kwargs['config']
        with CorpusContext(config) as c:
            all_found = c.has_all_sound_files()
        self.dataReady.emit(all_found)

