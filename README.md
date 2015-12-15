Speech Corpus Tools
===================

[![Build Status](https://travis-ci.org/MontrealCorpusTools/speechcorpustools.svg?branch=master)](https://travis-ci.org/MontrealCorpusTools/speechcorpustools)
[![Coverage Status](https://coveralls.io/repos/MontrealCorpusTools/speechcorpustools/badge.svg?branch=master&service=github)](https://coveralls.io/github/MontrealCorpusTools/speechcorpustools?branch=master)
[![Documentation Status](https://readthedocs.org/projects/speech-corpus-tools/badge/?version=latest)](http://speech-corpus-tools.readthedocs.org/en/latest/?badge=latest)

This package is under development, please report any issues to
michael.e.mcauliffe@gmail.com.

Speech Corpus Tools is built on top of PolyglotDB to provide an interface
for complex queries and visualization that are routine in analyzing data
from spoken corpora.

Dependencies:

- PolyglotDB (https://github.com/MontrealCorpusTools/PolyglotDB)
- Neo4j (http://neo4j.com/)
- PyQt5 (https://riverbankcomputing.com/software/pyqt/download5)
- vispy (http://vispy.org/)
- python-acoustic-similarity (https://github.com/mmcauliffe/python-acoustic-similarity)

To install:

1. Download and install PolyglotDB :
   - Download and install Neo4j
   - Clone the PolyglotDB repository
   - In a terminal, install PolyglotDB using ``python setup.py install``
2. Download and install ``vispy``
   - Clone the Vispy repository (https://github.com/vispy/vispy)
   - Install via ``python setup.py develop``
3. Download and install Speech Corpus Tools:
   - Clone the speechcorpustools repository
   - In a terminal install Speech Corpus Tools ``python setup.py install``
