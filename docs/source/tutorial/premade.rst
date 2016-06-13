******************************************
Speech Corpus Tools: Tutorial and examples
******************************************



.. _premade:

Premade database
################

Make sure you have opened the SCT application and started Neo4j, at least once.  This creates folders for Neo4j databases and for all SCT's local files (including SQL databases):

* OS X: ``/Users/username/Documents/Neo4j``, ``/Users/username/Documents/SCT``
* Windows: ``C:\Users\username\Documents\Neo4j``, ``C:\Users\username\Documents\SCT``

Unzip the ``buckeyeDatabases.zip`` file.  It contains two folders,  ``buckeye.graphdb`` and ``buckeye``. Move these (using Finder on OS X, or File Explorer on Windows) to the ``Neo4j`` and ``SCT`` folders. After doing so, these directories should exist:

* ``/Users/username/Documents/Neo4j/buckeye.graphdb``
* ``/Users/username/Documents/SCT/buckeye``

Some important information about the database (to replicate if you are building your own):

* Utterances have been defined as speech chunks separated by non-speech (pauses, disfluencies, other person talking) chunks of at least 150 msec.

* Syllabification has been performed using maximal onset.


`Previous <http://sct.readthedocs.io/en/latest/tutorial/buckeye.html>`_