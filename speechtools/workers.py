
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
from polyglotdb.io.enrichment import enrich_lexicon_from_csv, enrich_features_from_csv, enrich_speakers_from_csv

from polyglotdb.utils import update_sound_files, gp_language_stops, gp_speakers

from polyglotdb.acoustics.analysis import acoustic_analysis
from polyglotdb.graph.discourse import LongSoundFile

class FunctionWorker(QtCore.QThread):
    updateProgress = QtCore.pyqtSignal(object)
    updateMaximum = QtCore.pyqtSignal(object)
    updateProgressText = QtCore.pyqtSignal(str)
    errorEncountered = QtCore.pyqtSignal(object)
    finishedCancelling = QtCore.pyqtSignal()
    actionCompleted= QtCore.pyqtSignal(object)

    dataReady = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FunctionWorker, self).__init__()
        self.stopped = False
        self.finished = True

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
        finished = False
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
                except (ConnectionError, NetworkAddressError, TemporaryConnectionError) as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    e = ''.join(traceback.format_exception(exc_type, exc_value,exc_traceback))
                    print(e)
                    tries += 1
                    if tries == 2:
                        self.connectionIssues.emit()

            if not success:
                raise(ConnectionError('The query could not be completed.  Please check your internet connectivity.'))

        
        except Exception as e:
            if not isinstance(e, PGError):
                exc_type, exc_value, exc_traceback = sys.exc_info()
                e = ''.join(traceback.format_exception(exc_type, exc_value,exc_traceback))
            self.finished = True
            self.errorEncountered.emit(e)
            return
        if self.stopped:
            time.sleep(0.1)
            self.finished = True
            self.finishedCancelling.emit()
            return
        print('finished')
        self.dataReady.emit(results)
        
        self.finished = True
        
    def run_query(self):
        profile = self.kwargs['profile']
        config = self.kwargs['config']
        with CorpusContext(config) as c:
            a_type = getattr(c, profile.to_find)
            query = c.query_graph(a_type)
            query.call_back = self.kwargs['call_back']
            query.stop_check = self.kwargs['stop_check']
            query = query.filter(*profile.for_polyglot(c))
            query = query.preload(getattr(a_type, 'speaker'), getattr(a_type,'discourse'))
            print(query.cypher())

            results = query.all()
            if results is not None:
                print(len(results))
        self.actionCompleted.emit('query')
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
            self.actionCompleted.emit('importing corpus') 
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
            query.call_back = self.kwargs['call_back']
            query.stop_check = self.kwargs['stop_check']
            filters = profile.for_polyglot(c)
            query = query.filter(*filters)
            columns = export_profile.for_polyglot(c, to_find = profile.to_find)
            query = query.columns(*columns)
            print(query.cypher())
            try:
                results = query.to_csv(export_path)
            except PermissionError:
                raise(PGError('The file you specified could not be written to. Please ensure you have proper permissions and programs that lock the file (i.e., Excel) do not have it open.'))
            self.actionCompleted.emit('exporting') 
        return True

class DiscourseQueryWorker(QueryWorker):
    def run_query(self):
        begin = self.kwargs['begin']
        end = self.kwargs['end']
        config = self.kwargs['config']
        discourse = self.kwargs['discourse']
        with CorpusContext(config) as c:
            discourse = c.inspect_discourse(discourse, begin, end)
        return discourse, begin, end

class AudioFinderWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        directory = self.kwargs['directory']
        with CorpusContext(config) as c:
            update_sound_files(c, directory)
            all_found = c.has_all_sound_files()
        return all_found

class AudioCheckerWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        with CorpusContext(config) as c:
            all_found = c.has_all_sound_files()
        return all_found

class AcousticAnalysisWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        acoustics = self.kwargs['acoustics']
        with CorpusContext(config) as c:
            acoustic_analysis(c,
                            stop_check = self.kwargs['stop_check'],
                            call_back = self.kwargs['call_back'],
                            acoustics = acoustics)
            self.actionCompleted.emit('analysing acousics')         
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
            self.actionCompleted.emit('encoding pauses') 
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
            self.actionCompleted.emit('encoding utterances') 
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
            self.actionCompleted.emit('encoding speech rate') 
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
            self.actionCompleted.emit('encoding utterance position')            
            if stop_check():
                call_back('Resetting utterance positions...')
                call_back(0, 0)
                c.reset_utterance_position()
                return False
        return True

class SyllabicEncodingWorker(QueryWorker):
    def run_query(self):
        print("syllablics encoded")
        config = self.kwargs['config']
        segments = self.kwargs['segments']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding syllabics...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            c.reset_class('syllabic')
            c.encode_class(segments, 'syllabic')
            self.actionCompleted.emit('encoding syllabics')
            if stop_check():
                call_back('Resetting syllabics...')
                call_back(0, 0)
                c.reset_class('syllabic')
                return False
        return True

class SyllableEncodingWorker(QueryWorker):
    def run_query(self):
        print("syllables encoded")
        config = self.kwargs['config']
        algorithm = self.kwargs['algorithm']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding syllables...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            c.encode_syllables(algorithm = algorithm, call_back = call_back, stop_check = stop_check)
            self.actionCompleted.emit('encoding syllables')

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
            self.actionCompleted.emit('encoding '+ self.kwargs['label'].replace('_',' '))
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
            self.actionCompleted.emit('enriching lexicon')
            if stop_check():
                call_back('Resetting lexicon...')
                call_back(0, 0)
                c.reset_lexicon()
                
                print("emitted {}".format(actionCompleted))
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
            self.actionCompleted.emit('enriching phonological inventory')
            if stop_check():
                call_back('Resetting phonological inventory...')
                call_back(0, 0)
                c.reset_lexicon()
                return False
        return True


class SpeakerEnrichmentWorker(QueryWorker):
    def run_query(self):
        config = self.kwargs['config']
        path = self.kwargs['path']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Enriching speakers...')
        call_back(0,0)
        with CorpusContext(config) as c:
            enrich_speakers_from_csv(c, path)
            self.actionCompleted.emit('enriching speakers')
            
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
            self.actionCompleted.emit('encoding '+ self.kwargs['name'].replace('_',' '))
            if stop_check():
                return False
        return True

class RelativizedMeasuresWorker(QueryWorker):
    def run_query(self):
        res  = ""
        data_type = 'word'
        config = self.kwargs['config']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding {}...'.format(self.kwargs['measure']))
        call_back(0, 0)
        with CorpusContext(config) as c:
            string = "!"
            if self.kwargs['measure'] == 'word_median':
                res = c.word_median()
            elif self.kwargs['measure'] == 'all_word_median':
                res = c.all_word_median()
            elif self.kwargs['measure'] == 'word_mean_duration':
                res = c.word_mean_duration()
            elif self.kwargs['measure'] == 'word_std_dev':
                res = c.word_std_dev()
            elif self.kwargs['measure'] == 'baseline_duration':
                res = c.baseline_duration()
            elif self.kwargs['measure'] == 'phone_mean':
                data_type = 'phone'
                res = c.phone_mean_duration()
            elif self.kwargs['measure'] == 'phone_median':
                data_type = 'phone'
                res = c.phone_median()
            elif self.kwargs['measure'] == 'phone_std_dev':
                data_type = 'phone'
                res = c.phone_std_dev()
            elif self.kwargs['measure'] == 'all_word_median':
                res = c.all_word_median()
            elif self.kwargs['measure'] == 'phone_mean_duration_with_speaker':
                data_type = 'speaker'
                res = c.phone_mean_duration_with_speaker()
            elif self.kwargs['measure'] == 'word_mean_by_speaker':
                data_type = 'speaker'
                res = c.word_mean_duration_with_speaker()
            elif self.kwargs['measure'] == 'all_phone_median':
                data_type = 'phone'
                res = c.all_phone_median()
            elif self.kwargs['measure'] == 'syllable_mean':
                data_type = 'syllable'
                res = c.syllable_mean_duration()
            elif self.kwargs['measure'] == 'syllable_median':
                data_type = 'syllable'
                res = c.syllable_median()
            elif self.kwargs['measure'] == 'syllable_std_dev':
                data_type = 'syllable'
                res = c.syllable_std_dev()
            elif self.kwargs['measure'] == 'mean_speech_rate':
                data_type = 'speaker'
                res = c.average_speech_rate()

            else:
                print("error")
            c.encode_measure(res, data_type)
            self.actionCompleted.emit('encoding '+ self.kwargs['measure'].replace('_',' '))
            if stop_check():
                return False
        return True




class PrecedingCacheWorker(QueryWorker):
    def run_query(self):
        print('starting to cache preceding')
        config = self.kwargs['config']
        discourse = self.kwargs['discourse']
        begin = self.kwargs['begin']
        end = self.kwargs['end']
        with CorpusContext(config) as c:
            h_type = c.hierarchy.highest
            highest = getattr(c, h_type)
            q = c.query_graph(highest)
            q = q.filter(highest.discourse.name == discourse)
            q = q.filter(highest.begin < end)
            q = q.filter(highest.end > begin)
            preloads = []
            if h_type in c.hierarchy.subannotations:
                for s in c.hierarchy.subannotations[h_type]:
                    preloads.append(getattr(highest, s))
            for t in c.hierarchy.get_lower_types(h_type):
                preloads.append(getattr(highest, t))
            preloads.append(highest.speaker)
            preloads.append(highest.discourse)
            q = q.preload(*preloads)
            q = q.order_by(highest.begin)
            results = [x for x in q.all()]
        print('finished query')
        return results

class FollowingCacheWorker(QueryWorker):
    def run_query(self):
        print('starting to cache following')
        config = self.kwargs['config']
        discourse = self.kwargs['discourse']
        begin = self.kwargs['begin']
        end = self.kwargs['end']
        with CorpusContext(config) as c:
            h_type = c.hierarchy.highest
            highest = getattr(c, h_type)
            q = c.query_graph(highest)
            q = q.filter(highest.discourse.name == discourse)
            q = q.filter(highest.begin < end)
            q = q.filter(highest.end > begin)
            preloads = []
            if h_type in c.hierarchy.subannotations:
                for s in c.hierarchy.subannotations[h_type]:
                    preloads.append(getattr(highest, s))
            for t in c.hierarchy.get_lower_types(h_type):
                preloads.append(getattr(highest, t))
            preloads.append(highest.speaker)
            preloads.append(highest.discourse)
            q = q.preload(*preloads)
            q = q.order_by(highest.begin)
            print('getting results')
            results = [x for x in q.all()]
        print('finished query')
        return results

class AudioCacheWorker(QueryWorker):
    def run_query(self):
        print('beginning audio caching')
        sound_file = self.kwargs['sound_file']
        begin = self.kwargs['begin']
        end = self.kwargs['end']
        f = LongSoundFile(sound_file, begin, end)
        print('finished audio caching')
        return f

class StressEncodingWorker(QueryWorker):
    def run_query(self):
       
        config = self.kwargs['config']
        encode_type = self.kwargs['type']
        regex = self.kwargs['regex']
        stop_check = self.kwargs['stop_check']
        call_back = self.kwargs['call_back']
        call_back('Encoding stress/tone...')
        call_back(0, 0)
        with CorpusContext(config) as c:
            if encode_type == 'stress':
                if regex == "":
                    enrich_dict = c.encode_stress('[0-9]')
                else:
                    enrich_dict = c.encode_stress(regex)
            else:
                enrich_dict = c.encode_tone(regex)

            call_back("Removing extraneous info")
            call_back(0,0)
            c.remove_pattern(regex)
            c.enrich_syllables(enrich_dict)
            c.encode_hierarchy()
            c.refresh_hierarchy()
            self.actionCompleted.emit('encoding stress')
        return True
