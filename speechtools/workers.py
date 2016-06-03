
import sys
import traceback
import time
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb.exceptions import ConnectionError, NetworkAddressError, TemporaryConnectionError, PGError

from polyglotdb.graph.func import Sum

from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig

from polyglotdb.io import (inspect_buckeye, inspect_textgrid, inspect_timit,
                        inspect_labbcat, inspect_mfa, inspect_fave,
                        guess_textgrid_format)
from polyglotdb.io.enrichment import enrich_lexicon_from_csv, enrich_features_from_csv

from polyglotdb.utils import update_sound_files, gp_language_stops, gp_speakers

from polyglotdb.acoustics.analysis import get_pitch, get_formants, acoustic_analysis

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

    def emitProgress(self, *args):
        if isinstance(args[0],str):
            self.updateProgressText.emit(args[0])
        elif isinstance(args[0],dict):
            self.updateProgressText.emit(args[0]['status'])
        else:
            progress = args[0]
            if len(args) > 1:
                self.updateMaximum.emit(args[1])
            self.updateProgress.emit(progress)

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
        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        print('finished')
        self.dataReady.emit(results)

    def run_query(self):
        profile = self.kwargs['profile']
        config = self.kwargs['config']

        with CorpusContext(config) as c:
            a_type = getattr(c, profile.to_find)
            query = c.query_graph(a_type)
            query = query.filter(*profile.for_polyglot(c))
            query = query.preload(getattr(a_type, 'speaker'), getattr(a_type,'discourse'))
            print(query.cypher())

            results = query.all()
            print(len(results))
        return query, results


class ImportCorpusWorker(QueryWorker):
    def run_query(self):
        time.sleep(0.1)
        name = self.kwargs['name']
        directory = self.kwargs['directory']
        reset = True
        config = CorpusConfig(name, graph_host = 'localhost', graph_port = 7474)
        with CorpusContext(config) as c:
            if name == 'buckeye':
                parser = inspect_buckeye(directory)
            elif name == 'timit':
                parser = inspect_timit(directory)
            else:
                form = guess_textgrid_format(directory)
                if form == 'labbcat':
                    parser = inspect_labbcat(directory)
                elif form == 'mfa':
                    parser = inspect_mfa(directory)
                elif form == 'fave':
                    parser = inspect_fave(directory)
                else:
                    parser = inspect_textgrid(directory)

            parser.call_back = self.kwargs['call_back']
            parser.stop_check = self.kwargs['stop_check']
            parser.call_back('Resetting corpus...')
            if reset:
                c.reset(call_back = self.kwargs['call_back'], stop_check = self.kwargs['stop_check'])
            could_not_parse = c.load(parser, directory)
        return could_not_parse

class ExportQueryWorker(QueryWorker):
    def run_query(self):
        profile = self.kwargs['profile']
        export_profile = self.kwargs['export_profile']
        config = self.kwargs['config']
        export_path = self.kwargs['path']

        with CorpusContext(config) as c:
            a_type = getattr(c, profile.to_find)
            query = c.query_graph(a_type)
            filters = profile.for_polyglot(c)
            query = query.filter(*filters)
            columns = export_profile.for_polyglot(c, to_find = profile.to_find)
            query = query.columns(*columns)
            print(query.cypher())
            results = query.to_csv(export_path)
        return True

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
        sound_file = self.kwargs['sound_file']
        with CorpusContext(config) as c:
            formant_list = get_formants(c, sound_file, calculate = False)
            formant_dict = {'F1': np.array([[x.time, x.F1] for x in formant_list]),
                            'F2': np.array([[x.time, x.F2] for x in formant_list]),
                            'F3': np.array([[x.time, x.F3] for x in formant_list])}
        self.dataReady.emit(formant_dict)
        print('finished formants work')

class PitchGeneratorWorker(QueryWorker):
    def run(self):
        print('beginning pitch work')
        config = self.kwargs['config']
        sound_file = self.kwargs['sound_file']
        with CorpusContext(config) as c:
            pitch_list = get_pitch(c, sound_file, calculate = False)
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
        with CorpusContext(config) as c:
            acoustic_analysis(c,
                            stop_check = self.kwargs['stop_check'],
                            call_back = self.kwargs['call_back'])
        return True

class PauseEncodingWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        pause_words = self.kwargs['pause_words']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        with CorpusContext(config) as c:
            c.encode_pauses(pause_words,
                            stop_check = stop_check,
                            call_back = call_back)
            if stop_check():
                call_back('Resetting pauses...')
                call_back(0, 0)
                c.reset_pauses()
                return False
        return True

class UtteranceEncodingWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        min_pause_length = self.kwargs['min_pause_length']
        min_utterance_length = self.kwargs['min_utterance_length']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        with CorpusContext(config) as c:
            c.encode_utterances(min_pause_length, min_utterance_length,
                            stop_check = stop_check,
                            call_back = call_back)
            if stop_check():
                call_back('Resetting utterances...')
                call_back(0, 0)
                c.reset_utterances()
                return False
        return True

class SpeechRateWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        to_count = self.kwargs['to_count']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        with CorpusContext(config) as c:
            c.encode_speech_rate(to_count, stop_check = stop_check,
                            call_back = call_back)
            if stop_check():
                call_back('Resetting speech rate...')
                call_back(0, 0)
                c.reset_speech_rate()
                return False
        return True

class UtterancePositionWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        with CorpusContext(config) as c:
            c.encode_utterance_position(stop_check = stop_check,
                            call_back = call_back)
            if stop_check():
                call_back('Resetting utterance positions...')
                call_back(0, 0)
                c.reset_utterance_position()
                return False
        return True

class SyllabicEncodingWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        segments = self.kwargs['segments']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding syllabics...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            c.reset_class('syllabic')
            c.encode_class(segments, 'syllabic')
            if stop_check():
                call_back('Resetting syllabics...')
                call_back(0, 0)
                c.reset_class('syllabic')
                return False
        return True

class SyllableEncodingWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        algorithm = self.kwargs['algorithm']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding syllables...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            c.encode_syllables(algorithm = algorithm, call_back = call_back, stop_check = stop_check)
            if stop_check():
                call_back('Resetting syllables...')
                call_back(0, 0)
                c.reset_syllables()
                return False
        return True

class PhoneSubsetEncodingWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        segments = self.kwargs['segments']
        label = self.kwargs['label']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Resetting {}s...'.format(label))
        call_back(0, 0)
        with CorpusContext(config) as c:
            c.reset_class(label)
            c.encode_class(segments, label)
            if stop_check():
                call_back('Resetting {}s...'.format(label))
                call_back(0, 0)
                c.reset_class(label)
                return False
        return True

class LexiconEnrichmentWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        case_sensitive = self.kwargs['case_sensitive']
        path = self.kwargs['path']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Enriching lexicon...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            enrich_lexicon_from_csv(c, path)
            if stop_check():
                call_back('Resetting lexicon...')
                call_back(0, 0)
                c.reset_lexicon()
                return False
        return True

class FeatureEnrichmentWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        path = self.kwargs['path']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Enriching phonological inventory...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            enrich_features_from_csv(c, path)
            if stop_check():
                call_back('Resetting phonological inventory...')
                call_back(0, 0)
                c.reset_lexicon()
                return False
        return True

class HierarchicalPropertiesWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding {}...'.format(self.kwargs['name']))
        call_back(0, 0)
        with CorpusContext(config) as c:
            if self.kwargs['type'] == 'count':
                c.encode_count(self.kwargs['higher'], self.kwargs['lower'],
                            self.kwargs['name'], subset = self.kwargs['subset'])
            elif self.kwargs['type'] == 'position':
                c.encode_position(self.kwargs['higher'], self.kwargs['lower'],
                            self.kwargs['name'], subset = self.kwargs['subset'])
            elif self.kwargs['type'] == 'rate':
                c.encode_rate(self.kwargs['higher'], self.kwargs['lower'],
                            self.kwargs['name'], subset = self.kwargs['subset'])
            if stop_check():
                return False
        return True
