import pytest
import os

from polyglotdb.io.textgrid import inspect_discourse_textgrid, load_discourse_textgrid

from speechtools.corpus import CorpusContext
from polyglotdb.config import CorpusConfig


@pytest.fixture(scope='session')
def test_dir():
    return os.path.abspath('tests/data')

@pytest.fixture(scope='session')
def textgrid_test_dir(test_dir):
    return os.path.join(test_dir, 'textgrids')

@pytest.fixture(scope='session')
def graph_user():
    return 'neo4j'

@pytest.fixture(scope='session')
def graph_pw():
    return 'test'

@pytest.fixture(scope='session')
def graph_host():
    return 'localhost'

@pytest.fixture(scope='session')
def graph_port():
    return 7474

@pytest.fixture(scope='session')
def graph_db(graph_host, graph_port, graph_user, graph_pw):
    return dict(graph_host = graph_host, graph_port = graph_port)

@pytest.fixture(scope='session')
def acoustic_config(graph_db, textgrid_test_dir):
    config = CorpusConfig('acoustic', **graph_db)

    acoustic_path = os.path.join(textgrid_test_dir, 'acoustic_corpus.TextGrid')
    with CorpusContext(config) as c:
        c.reset()
        annotation_types = inspect_discourse_textgrid(acoustic_path)
        load_discourse_textgrid(c, acoustic_path, annotation_types)
        c.analyze_acoustics()
    return config
