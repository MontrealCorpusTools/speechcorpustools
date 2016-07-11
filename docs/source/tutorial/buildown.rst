.. _buildown:

******************************************
Speech Corpus Tools: Tutorial and examples
******************************************

Build your own database
#######################

Import
******

SCT currently supports the following corpus formats:

* Buckeye
* TIMIT
* Force-aligned TextGrids
    * FAVE (multiple talkers okay)
    * LaBB-CAT TextGrid export
    * Prosodylab 


To import one of those corpora, press the "Import local corpus" button below the "Available corpora" list.  Once it has been pressed, select one of the three main options to import.  From there, you will have to select where on the local computer the corpus files live and they will be imported into the local server.

At the moment, importing ignores any connections to remote servers, and requires that a local version of Neo4j is running.  Sound files will be detected based on sharing a name with a text file or TextGrid.  If the location of the sound files is changed, you can update where SCT thinks they are through the "Find local audio files" button.

:ref:`Previous <buckeye>`
