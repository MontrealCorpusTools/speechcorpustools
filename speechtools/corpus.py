import os
import re
import logging
import time

from sqlalchemy import create_engine

from polyglotdb.sql import Session, get_or_create
from polyglotdb.graph.func import Max, Min
from polyglotdb.corpus import CorpusContext as BaseContext
from speechtools.io.graph import time_data_to_csvs, import_utterance_csv

from .graph.query import GraphQuery

from .sql.models import (Base, SoundFile, Discourse)

from .acoustics.io import add_acoustic_info

from .acoustics import acoustic_analysis

from .acoustics.query import AcousticQuery

from .exceptions import NoSoundFileError, CorpusConfigError, GraphQueryError

class CorpusContext(BaseContext):
    """
    Context manager for connecting to corpora.
    """
    def __init__(self, *args, **kwargs):
        super(CorpusContext, self).__init__(*args, **kwargs)
        self._has_sound_files = None

    def init_sql(self):
        self.engine = create_engine(self.config.sql_connection_string)
        Session.configure(bind=self.engine)
        if not os.path.exists(self.config.db_path):
            Base.metadata.create_all(self.engine)

    def query_graph(self, annotation_type):
        if annotation_type.type not in self.annotation_types:
            raise(GraphQueryError('The graph does not have any annotations of type \'{}\'.  Possible types are: {}'.format(annotation_type.name, ', '.join(sorted(self.annotation_types)))))
        return GraphQuery(self, annotation_type)

    def discourse_sound_file(self, discourse):
        q = self.sql_session.query(SoundFile).join(SoundFile.discourse)
        q = q.filter(Discourse.name == discourse)
        sound_file = q.first()
        return sound_file

    @property
    def has_sound_files(self):
        if self._has_sound_files is None:
            self._has_sound_files = self.sql_session.query(SoundFile).first() is not None
        return self._has_sound_files

    def query_acoustics(self, graph_query):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        return AcousticQuery(self, graph_query)

    def analyze_acoustics(self):
        if not self.has_sound_files:
            raise(NoSoundFileError)
        acoustic_analysis(self)

    def encode_pauses(self, pause_words):
        """
        Set words to be pauses, as opposed to speech.

        Parameters
        ----------
        pause_words : str or list
            Either a list of words that are pauses or a string containing
            a regular expression that specifies pause words
        """
        self.reset_pauses()
        q = self.query_graph(self.word)
        if isinstance(pause_words, (list, tuple, set)):
            q = q.filter(self.word.label.in_(pause_words))
        elif isinstance(pause_words, str):
            q = q.filter(self.word.label.regex(pause_words))
        else:
            raise(NotImplementedError)
        q.set_pause()

        statement = '''MATCH (prec:{corpus}:word:speech)
        WHERE not (prec)-[:precedes]->()
        WITH prec
        MATCH p = (prec)-[:precedes_pause*]->(foll:{corpus}:word:speech)
        WITH prec, foll, p
        WHERE NONE (x in nodes(p)[1..-1] where x:speech)
        MERGE (prec)-[:precedes]->(foll)'''.format(corpus = self.corpus_name)

        self.execute_cypher(statement)
        self.annotation_types.add('pause')

    def reset_pauses(self):
        """
        Revert all words marked as pauses to regular words marked as speech
        """
        statement = '''MATCH (n:{corpus}:word:speech)-[r:precedes]->(m:{corpus}:word:speech)
        WHERE (n)-[:precedes_pause]->()
        DELETE r'''.format(corpus=self.corpus_name)
        self.graph.cypher.execute(statement)
        statement = '''MATCH (n:{corpus}:word)-[r:precedes_pause]->(m:{corpus}:word)
        MERGE (n)-[:precedes]->(m)
        DELETE r'''.format(corpus=self.corpus_name)
        self.graph.cypher.execute(statement)
        statement = '''MATCH (n:pause:{corpus})
        SET n :speech
        REMOVE n:pause'''.format(corpus=self.corpus_name)
        self.graph.cypher.execute(statement)
        try:
            self.annotation_types.remove('pause')
        except KeyError:
            pass


    def reset_utterances(self):
        """
        Remove all utterance annotations.
        """
        try:
            q = self.query_graph(self.utterance)
            q.delete()
            self.annotation_types.remove('utterance')
        except GraphQueryError:
            pass

    def encode_utterances(self, min_pause_length = 0.5, min_utterance_length = 0):
        """
        Encode utterance annotations based on minimum pause length and minimum
        utterance length.  See `get_pauses` for more information about
        the algorithm.

        Once this function is run, utterances will be queryable like other
        annotation types.

        Parameters
        ----------
        min_pause_length : float, defaults to 0.5
            Time in seconds that is the minimum duration of a pause to count
            as an utterance boundary

        min_utterance_length : float, defaults to 0.0
            Time in seconds that is the minimum duration of a stretch of
            speech to count as an utterance
        """
        #initialize_csv('utterance', self.config.temporary_directory('csv'))
        self.graph.cypher.execute('CREATE INDEX ON :utterance(begin)')
        self.graph.cypher.execute('CREATE INDEX ON :utterance(end)')
        self.reset_utterances()
        for d in self.discourses:
            utterances = self.get_utterances(d, min_pause_length, min_utterance_length)
            time_data_to_csvs('utterance', self.config.temporary_directory('csv'), d, utterances)
            import_utterance_csv(self, d)

        self.hierarchy['word'] = 'utterance'
        self.hierarchy['utterance'] = None
        self.annotation_types.add('utterance')

    def get_utterances(self, discourse,
                min_pause_length = 0.5, min_utterance_length = 0):
        """
        Algorithm to find utterance boundaries in a discourse.

        Pauses with duration less than the minimum will
        not count as utterance boundaries.  Utterances that are shorter
        than the minimum utterance length (such as 'okay' surrounded by
        silence) will be merged with the closest utterance.

        Parameters
        ----------
        discourse : str
            String identifier for a discourse

        min_pause_length : float, defaults to 0.5
            Time in seconds that is the minimum duration of a pause to count
            as an utterance boundary

        min_utterance_length : float, defaults to 0.0
            Time in seconds that is the minimum duration of a stretch of
            speech to count as an utterance
        """
        statement = '''MATCH p = (prev_node_word:word:speech:{corpus}:{discourse})-[:precedes_pause*1..]->(foll_node_word:word:speech:{corpus}:{discourse})

WITH nodes(p)[1..-1] as ns,foll_node_word, prev_node_word
WHERE foll_node_word.begin - prev_node_word.end >= {{node_pause_duration}}
AND NONE (x in ns where x:speech)
WITH foll_node_word, prev_node_word
RETURN prev_node_word.end AS begin, foll_node_word.begin AS end, foll_node_word.begin - prev_node_word.end AS duration
ORDER BY begin'''.format(corpus = self.corpus_name, discourse = discourse)
        results = self.execute_cypher(statement, node_pause_duration = min_pause_length)

        collapsed_results = []
        for i, r in enumerate(results):
            if len(collapsed_results) == 0:
                collapsed_results.append(r)
                continue
            if r.begin == collapsed_results[-1].end:
                collapsed_results[-1].end = r.end
            else:
                collapsed_results.append(r)
        utterances = []
        q = self.query_graph(self.word).filter(self.word.discourse.name == discourse)
        times = q.aggregate(Min(self.word.begin), Max(self.word.end))
        if len(results) < 2:
            begin = times.min_begin
            if len(results) == 0:
                return [(begin, times.max_end)]
            if results[0].begin == 0:
                return [(results[0].end, times.max_end)]
            if results[0].end == times.max_end:
                return [(begin, results[0].end)]

        if results[0].begin != 0:
            current = 0
        else:
            current = None
        for i, r in enumerate(collapsed_results):
            if current is not None:
                if r.begin - current > min_utterance_length:
                    utterances.append((current, r.begin))
                elif i == len(results) - 1:
                    utterances[-1] = (utterances[-1][0], r.begin)
                elif len(utterances) != 0:
                    dist_to_prev = current - utterances[-1][1]
                    dist_to_foll = r.end - r.begin
                    if dist_to_prev <= dist_to_foll:
                        utterances[-1] = (utterances[-1][0], r.begin)
            current = r.end
        if current < times.max_end:
            if times.max_end - current > min_utterance_length:
                utterances.append((current, times.max_end))
            else:
                utterances[-1] = (utterances[-1][0], times.max_end)
        if utterances[-1][1] > times.max_end:
            utterances[-1] = (utterances[-1][0], times.max_end)
        if utterances[0][0] < times.min_begin:
            utterances[0] = (times.min_begin, utterances[0][1])
        return utterances


    def add_discourse(self, data):
        super(CorpusContext, self).add_discourse(data)
        add_acoustic_info(self, data)
