.. _librispeech:

******************************************
Speech Corpus Tools: Tutorial and examples
******************************************

LibriSpeech database
####################

To do the examples below, you will need a SCT database for the LibriSpeech
corpus.  Technically, this is a PolyglotDB database, which consists of
two sub-databases: a Neo4j database (which contains the hierarchical
representation of discourses), and a SQL database (which contains lexical
and featural information, and cached acoustic measurements). Instructions
are below for either using pre-made copies of these, or for making your own.

Use pre-made database
*********************

Make sure you have opened the SCT application and started Neo4j, at least once.  This creates
folders for Neo4j databases and for all SCT's local files (including SQL databases):

* OS X: ``/Users/username/Documents/Neo4j``, ``/Users/username/Documents/SCT``
* Windows: ``C:\Users\username\Documents\Neo4j``, ``C:\Users\username\Documents\SCT``

Unzip the ``librispeechDatabases.zip`` file.  It contains two folders,
``librispeech.graphdb`` and ``LibriSpeech``. Move these (using Finder on
OS X, or File Explorer on Windows) to the ``Neo4j`` and ``SCT`` folders.
After doing so, these directories should exist:

* ``/Users/username/Documents/Neo4j/librispeech.graphdb``
* ``/Users/username/Documents/SCT/LibriSpeech``

When starting the Neo4j server the next time, select the ``librispeech.graphdb`` rather
than the default folder.

Some important information about the database (to replicate if you are building your own):

* Utterances have been defined as speech chunks separated by non-speech
  (pauses, disfluencies, other person talking) chunks of at least 150 msec.

* Syllabification has been performed using maximal onset.


Build your own database
***********************

Import
======

SCT currently supports the following corpus formats:

* Buckeye
* TIMIT
* Force-aligned TextGrids
    * FAVE (multiple talkers okay)
    * LaBB-CAT TextGrid export
    * Prosodylab


To import one of those corpora, press the "Import local corpus" button
below the "Available corpora" list.  Once it has been pressed, select one
of the three main options to import.  From there, you will have to select
where on the local computer the corpus files live and they will be imported
into the local server.

At the moment, importing ignores any connections to remote servers, and
requires that a local version of Neo4j is running.  Sound files will be detected
based on sharing a name with a text file or TextGrid.  If the location of the
sound files is changed, you can update where SCT thinks they are through the
"Find local audio files" button.

See :ref:`enrichmen_tutorial` for more details on how to further enrich your database


:doc:`Next <vignetteMain>`           :doc:`Previous <installation>`


