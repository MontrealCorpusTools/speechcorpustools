.. _installation:

************
Installation
************

.. _prerequisites:

Prerequisites
=============

Speech Corpus Tools relies primarily on PolyglotDB to function.  Please refer
to installation instructions for PolyglotDB
(http://polyglotdb.readthedocs.org/en/latest/installation.html).

Additionally, Speech Corpus Tools makes use of Numpy and Scipy, so please
ensure that those packages are installed, either through pip, Anaconda or
precompiled binaries.

If you want to use the graphical interface, installation of PyQt5 is required.
Binaries are available at https://riverbankcomputing.com/software/pyqt/download5.
Anaconda packages are available for some operating systems.

Speech Corpus Tools makes heavy use of the signal processing functions in
`python-acoustic-similarity` (https://github.com/mmcauliffe/python-acoustic-similarity),
 which will be installed automatically during installation.

.. _actual_install:

Installation
============

Clone or download the Git repository
(https://github.com/MontrealCorpusTools/speechcorpustools).  Navigate to
the diretory via command line and install via :code:`python setup.py install`.

