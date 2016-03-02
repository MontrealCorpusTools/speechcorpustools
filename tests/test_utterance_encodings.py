import os
import pytest

from speechtools.corpus import CorpusContext

def test_encode_positions(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_utterance_position()

        q = g.query_graph(g.word).columns(g.word.label.column_name('label'),
                        g.word.position_in_utterance.column_name('pos'))
        q = q.order_by(g.word.begin)
        results = q.all()
        assert(results[0].label == 'this')
        assert(results[0].pos == 1)
