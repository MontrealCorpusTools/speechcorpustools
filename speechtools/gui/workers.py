
import sys
import traceback
import time
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.exceptions import ConnectionError, NetworkAddressError, TemporaryConnectionError, PGError

from polyglotdb.graph.func import Sum

from speechtools.corpus import CorpusContext

from speechtools.utils import update_sound_files, gp_language_stops, gp_speakers

from speechtools.acoustics.analysis import get_pitch, get_formants, acoustic_analysis

class FunctionWorker(QtCore.QThread):
    updateProgress = QtCore.pyqtSignal(object)
    updateMaximum = QtCore.pyqtSignal(object)
    updateProgressText = QtCore.pyqtSignal(str)
    errorEncountered = QtCore.pyqtSignal(object)
    finishedCancelling = QtCore.pyqtSignal()

    dataReady = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FunctionWorker, self).__init__()
        self.stopped = False

    def setParams(self, kwargs):
        self.kwargs = kwargs
        self.kwargs['call_back'] = self.emitProgress
        self.kwargs['stop_check'] = self.stopCheck
        self.stopped = False
        self.total = None

    def stop(self):
        self.stopped = True

    def stopCheck(self):
        return self.stopped

    def emitProgress(self,*args):
        if isinstance(args[0],str):
            self.updateProgressText.emit(args[0])
        elif isinstance(args[0],dict):
            self.updateProgressText.emit(args[0]['status'])
        else:
            progress = args[0]
            if len(args) > 1:
                self.updateMaximum.emit(args[1])
            self.updateProgress.emit(progress)


class ImportCorpusWorker(FunctionWorker):
    def run(self):
        time.sleep(0.1)
        textType = self.kwargs.pop('text_type')
        isDirectory = self.kwargs.pop('isDirectory')
        logging.info('Importing {} corpus named {}'.format(textType, self.kwargs['corpus_name']))
        logging.info('Path: '.format(self.kwargs['path']))
        log_annotation_types(self.kwargs['annotation_types'])
        try:
            if textType == 'spelling':

                if isDirectory:
                    corpus = load_directory_spelling(**self.kwargs)
                else:
                    corpus = load_discourse_spelling(**self.kwargs)
            elif textType == 'transcription':

                if isDirectory:
                    corpus = load_directory_transcription(**self.kwargs)
                else:
                    corpus = load_discourse_transcription(**self.kwargs)
            elif textType == 'ilg':

                if isDirectory:
                    corpus = load_directory_ilg(**self.kwargs)
                else:
                    corpus = load_discourse_ilg(**self.kwargs)
            elif textType == 'textgrid':
                if isDirectory:
                    corpus = load_directory_textgrid(**self.kwargs)
                else:
                    corpus = load_discourse_textgrid(**self.kwargs)
            elif textType == 'csv':
                corpus = load_corpus_csv(**self.kwargs)
            elif textType in ['buckeye', 'timit']:
                self.kwargs['dialect'] = textType
                if isDirectory:
                    corpus = load_directory_multiple_files(**self.kwargs)
                else:
                    corpus = load_discourse_multiple_files(**self.kwargs)
        except PCTError as e:
            self.errorEncountered.emit(e)
            return
        except Exception as e:
            e = PCTPythonError(e)
            self.errorEncountered.emit(e)
            return
        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        self.dataReady.emit(corpus)


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
        filters = self.kwargs['filters']
        columns = self.kwargs['columns']
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
            utt_type = getattr(w_type, utt_type)
            q = c.query_graph(a_type)
            q = q.filter(a_type.label.in_(stops))
            if self.kwargs['query_type'] in ['Lab 1 stops', 'Lab 2 stops']:
                q = q.order_by(a_type.discourse.name)
                q = q.order_by(a_type.begin)
            if filters:
                q = q.filter(*filters)
            if columns:
                q = q.columns(*columns)
            #q = q.limit(100)
            results = q.all()
        return q, results

class ExportQueryWorker(QueryWorker):
    def run(self):
        time.sleep(0.1)
        print('beginning export')
        try:
            config = self.kwargs['config']
            export_path = self.kwargs['path']
            filters = self.kwargs['filters']
            columns = self.kwargs['columns']
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
                if filters:
                    q = q.order_by(a_type.discourse.name)
                    q = q.order_by(a_type.begin)
                    q = q.filter(*filters)
                if columns:
                    q = q.columns(*columns)

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
                for s in c.hierarchy.subannotations[a_type]:
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

class FormantsGeneratorWorker(QueryWorker):
    def run(self):
        print('beginning formants work')
        config = self.kwargs['config']
        algorithm = self.kwargs['algorithm']
        sound_file = self.kwargs['sound_file']
        with CorpusContext(config) as c:
            formant_list = get_formants(c, sound_file, algorithm)
            formant_dict = {'F1': np.array([[x.time, x.F1] for x in formant_list]),
                            'F2': np.array([[x.time, x.F2] for x in formant_list]),
                            'F3': np.array([[x.time, x.F3] for x in formant_list])}
        self.dataReady.emit(formant_dict)
        print('finished formants work')

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

class AcousticAnalysisWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        speakers = gp_speakers[config.corpus_name]
        with CorpusContext(config) as c:
            acoustic_analysis(c, speaker_subset = speakers,
                            stop_check = self.kwargs['stop_check'],
                            call_back = self.kwargs['call_back'])
        return True
