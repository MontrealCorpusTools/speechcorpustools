Speech Corpus Tools
===================

[![Build Status](https://travis-ci.org/MontrealCorpusTools/speechcorpustools.svg?branch=master)](https://travis-ci.org/MontrealCorpusTools/speechcorpustools)
[![Coverage Status](https://coveralls.io/repos/MontrealCorpusTools/speechcorpustools/badge.svg?branch=master&service=github)](https://coveralls.io/github/MontrealCorpusTools/speechcorpustools?branch=master)
[![Documentation Status](https://readthedocs.org/projects/speech-corpus-tools/badge/?version=latest)](http://speech-corpus-tools.readthedocs.org/en/latest/?badge=latest)

Speech Corpus Tools is a software tool built to ease the analysis of large speech corpora.

Please see the online documentation (http://speech-corpus-tools.readthedocs.io/) for more information and installation instructions.

This application is under development, please report any issues to
michael.e.mcauliffe@gmail.com.

To install from source (or to set up a development environment):

1. Download or clone the repository
2. Install Python requirements (`pip install -r requirements.txt`)
3. Install Neo4j and set it up (see http://speech-corpus-tools.readthedocs.io/en/latest/tutorial/tutorial.html#installation-tutorial)
4. Run the debug script from the root of repository (`python bin/qt_debug.py`)
5. To build an executable run `freezing/freeze.sh` (for Mac/Linux) or `freezing/freeze.bat` (for Windows)
