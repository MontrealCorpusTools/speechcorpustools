.. _tutintroduction:

Tutorial
########

.. _PGDB website: http://montrealcorpustools.github.io/PolyglotDB/

.. _GitHub repository: https://https://github.com/mmcauliffe/speechcorpustools

Speech Corpus Tools is a system for going from a raw speech corpus to a data file (CSV) ready for further analysis (e.g. in R), which conceptually consists of a pipeline of four steps:

1. **Import** the corpus into SCT
    * Result: a structured database of linguistic objects (words, phones, discourses).

2. **Enrich** the database
    * Result: Further linguistic objects (utterances, syllables), and information about objects (e.g. speech rate, word frequencies).

3. **Query** the database
    * Result: A set of linguistic objects of interest (e.g. utterance-final words ending with a stop),

4. **Export** the results
    * Result: A CSV file containing information about the set of objects of interest

Ideally, the import and enrichment steps are only performed once for a given corpus.  The typical use case of SCT is performing a query and export corresponding to some linguistic question(s) of interest.

This tutorial is structured as follows:

*  :ref:`Installation <installation_tutorial>`: Install necessary
   software -- :ref:`Neo4j <neo4j_install>` and :ref:`SCT <sct_install>`.

* :ref:`Librispeech database <librispeech>`: Obtain a database for the
  Librispeech Corpus where the *import* and *enrichment* steps have
  been completed , either by using a :ref:`premade <premade>` version,
  or doing the import and enrichment steps :ref:`yourself <buildownlibrispeech>`.

* :ref:`Examples <vignetteMain>`:
      * Two worked examples (:ref:`1 <example1>`, :ref:`2 <example2>`)
        illustrating the *Query* and *Export* steps, as well as
        (optional) basic analysis of the resulting data files (CSV's) in R.

      * One additional example (:ref:`3 <example3>`) left as an exercise.


..
   * :ref:`Next steps <nextsteps>`: Next steps with SCT after the tutorial: pointers to different places in the documentation and presentations where SCT is described.  Intended to kickstart carrying out your own analyses, or applying SCT to your own corpus.



.. _installation_tutorial:

Installation
************

.. _neo4j_install:

Installing Neo4j
================

SCT currently requires that `Neo4j <https://neo4j.com/>`_ version 3.0 be installed locally and running.
To install Neo4j, please use the following links:

* `Mac version <http://info.neotechnology.com/download-thanks.html?edition=community&release=3.0.3&flavour=dmg>`_
* `Windows version <http://info.neotechnology.com/download-thanks.html?edition=community&release=3.0.3&flavour=winstall64>`_

Once downloaded, just run the installer and it'll install the database software that SCT uses locally.

SCT currently requires you to change the configuration for Neo4j, by
doing the following **once**, before running SCT:

* Open the Neo4j application/executable (Mac/Windows)
* Click on ``Options ...``
* Click on the ``Edit...`` button for ``Database configuration``
* Replace the text in the window that comes up with the following,
  then save the file:

::

    #***************************************************************
    # Server configuration
    #***************************************************************

    # This setting constrains all `LOAD CSV` import files to be under the `import` directory. Remove or uncomment it to
    # allow files to be loaded from anywhere in filesystem; this introduces possible security problems. See the `LOAD CSV`
    # section of the manual for details.
    #dbms.directories.import=import

    # Require (or disable the requirement of) auth to access Neo4j
    dbms.security.auth_enabled=false

    #
    # Bolt connector
    #
    dbms.connector.bolt.type=BOLT
    dbms.connector.bolt.enabled=true
    dbms.connector.bolt.tls_level=OPTIONAL
    # To have Bolt accept non-local connections, uncomment this line:
    # dbms.connector.bolt.address=0.0.0.0:7687

    #
    # HTTP Connector
    #
    dbms.connector.http.type=HTTP
    dbms.connector.http.enabled=true
    #dbms.connector.http.encryption=NONE
    # To have HTTP accept non-local connections, uncomment this line:
    #dbms.connector.http.address=0.0.0.0:7474

    #
    # HTTPS Connector
    #
    # To enable HTTPS, uncomment these lines:
    #dbms.connector.https.type=HTTP
    #dbms.connector.https.enabled=true
    #dbms.connector.https.encryption=TLS
    #dbms.connector.https.address=localhost:7476

    # Certificates directory
    # dbms.directories.certificates=certificates

    #*****************************************************************
    # Administration client configuration
    #*****************************************************************


    # Comma separated list of JAX-RS packages containing JAX-RS resources, one
    # package name for each mountpoint. The listed package names will be loaded
    # under the mountpoints specified. Uncomment this line to mount the
    # org.neo4j.examples.server.unmanaged.HelloWorldResource.java from
    # neo4j-examples under /examples/unmanaged, resulting in a final URL of
    # http://localhost:${default.http.port}/examples/unmanaged/helloworld/{nodeId}
    #dbms.unmanaged_extension_classes=org.neo4j.examples.server.unmanaged=/examples/unmanaged

    #*****************************************************************
    # HTTP logging configuration
    #*****************************************************************

    # HTTP logging is disabled. HTTP logging can be enabled by setting this
    # property to 'true'.
    dbms.logs.http.enabled=false

    # Logging policy file that governs how HTTP log output is presented and
    # archived. Note: changing the rollover and retention policy is sensible, but
    # changing the output format is less so, since it is configured to use the
    # ubiquitous common log format
    #org.neo4j.server.http.log.config=neo4j-http-logging.xml

    # Enable this to be able to upgrade a store from an older version.
    #dbms.allow_format_migration=true

    # The amount of memory to use for mapping the store files, in bytes (or
    # kilobytes with the 'k' suffix, megabytes with 'm' and gigabytes with 'g').
    # If Neo4j is running on a dedicated server, then it is generally recommended
    # to leave about 2-4 gigabytes for the operating system, give the JVM enough
    # heap to hold all your transaction state and query context, and then leave the
    # rest for the page cache.
    # The default page cache memory assumes the machine is dedicated to running
    # Neo4j, and is heuristically set to 50% of RAM minus the max Java heap size.
    #dbms.memory.pagecache.size=10g

    #*****************************************************************
    # Miscellaneous configuration
    #*****************************************************************

    # Enable this to specify a parser other than the default one.
    #cypher.default_language_version=3.0

    # Determines if Cypher will allow using file URLs when loading data using
    # `LOAD CSV`. Setting this value to `false` will cause Neo4j to fail `LOAD CSV`
    # clauses that load data from the file system.
    dbms.security.allow_csv_import_from_file_urls=true

    # Retention policy for transaction logs needed to perform recovery and backups.
    dbms.tx_log.rotation.retention_policy=false

    # Enable a remote shell server which Neo4j Shell clients can log in to.
    #dbms.shell.enabled=true
    # The network interface IP the shell will listen on (use 0.0.0.0 for all interfaces).
    #dbms.shell.host=127.0.0.1
    # The port the shell will listen on, default is 1337.
    #dbms.shell.port=1337

    # Only allow read operations from this Neo4j instance. This mode still requires
    # write access to the directory for lock purposes.
    #dbms.read_only=false

    # Comma separated list of JAX-RS packages containing JAX-RS resources, one
    # package name for each mountpoint. The listed package names will be loaded
    # under the mountpoints specified. Uncomment this line to mount the
    # org.neo4j.examples.server.unmanaged.HelloWorldResource.java from
    # neo4j-server-examples under /examples/unmanaged, resulting in a final URL of
    # http://localhost:7474/examples/unmanaged/helloworld/{nodeId}
    #dbms.unmanaged_extension_classes=org.neo4j.examples.server.unmanaged=/examples/unmanaged

.. _sct_install:

Installing SCT
==============

Once Neo4j is set up as above, the latest version of SCT can be downloaded from
the `SCT releases
<https://github.com/MontrealCorpusTools/speechcorpustools/releases>`_
page. As of 12 July 2016, the most current release is v0.5.

Windows
-------

1. Download the zip archive for Windows
2. Extract the folder
3. Double click on the executable to run SCT.

.. note:
   One possible issue that might arise with Windows computers is related
   to graphics drivers. On the Windows version, a console output will pop
   up in addition to the main SCT window. If you notice a string of
   output containing something like “RuntimeError: OpenGL got errors”
   then your graphics driver is probably a couple of years old. In which
   case, please follow the instructions on
   http://www.wikihow.com/Update-Your-Video-Card-Drivers-on-Windows-7 to update
   them. Macs tend to be better about keeping
   the graphics drivers up to date, and shouldn’t have this issue. SCT
   should run on Windows 7+ and Mac OS X 10.11+

Mac
---

1. Download the DMG file.
2. Double-click on the DMG file.
3. Drag the `sct` icon to your Applications folder.
4. Double click on the SCT application to run.


.. _librispeech:

LibriSpeech database
********************

The examples in this tutorial use a subset of the `LibriSpeech ASR
corpus <http://www.openslr.org/12/>`_, a corpus of read English speech
prepared by Vassil Panayotov, Daniel Povey, and collaborators. The
subset used here is the ``test-clean`` subset, consisting of **5.4
hours of speech** from **40 speakers**.  This subset was force-aligned
using the `Montreal Forced Aligner
<https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner>`_,
and the pronunciation dictionary provided with this corpus.  This
procedure results in one Praat TextGrid per sentence in the corpus,
with phone and word boundaries. We refer to the resulting dataset as
the *LibriSpeech dataset*: 5.4 hours of read sentences with
force-aligned phone and word boundaires.

The examples require constructing a *Polyglot DB* database for the LibriSpeech
dataset, in two steps: [#f2]_

1. *Importing* the LibriSpeech dataset using SCT, into a database containing information about words, phones, speakers, and files.
2. *Enriching* the database to include additional information about other linguistic objects (utterances, syllables) and properties of objects (e.g. speech rate).

.. _`librispeechDatabase.zip`: https://github.com/MontrealCorpusTools/speechcorpustools/releases/download/v0.5/librispeechDatabase.zip

Instructions are below for using a premade copy of the
LibriSpeech database, where steps (1) and (2) have been carried out
for you.  Instructions for :ref:`making your own
<buildownlibrispeech>` are coming soon. (For **BigPhon 2016**
tutorial, just use the pre-made copy.)

.. _premade:

Use pre-made database
=====================


Make sure you have opened the SCT application and started Neo4j, at least once.  This creates
folders for Neo4j databases and for all SCT's local files (including SQL databases):

* OS X: ``/Users/username/Documents/Neo4j``, ``/Users/username/Documents/SCT``
* Windows: ``C:\Users\username\Documents\Neo4j``, ``C:\Users\username\Documents\SCT``

Download and unzip the `librispeechDatabase.zip`_ file.  It contains two folders,
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

.. _buildownlibrispeech:

Building your own Librispeech database
======================================

**Coming soon!**  Some general information on building a database in
SCT (= importing data) is :any:`here <../additional/buildown>`.



.. _vignetteMain:

Examples
********

Several worked examples follow, which demonstrate the workflow of SCT
and how to construct queries and exports. You should be able to
complete each example by following the steps listed in **bold**. The
examples are designed to be completed in order.

Each example results in a CSV file containing data, which you should
then be able to use to visualize the results. Instructions for basic
visualization in R are given.

:ref:`Example 1 <example1>` : Factors affecting vowel duration

:ref:`Example 2 <example2>` : Polysyllabic shortening

:ref:`Example 3 <example3>` : Menzerath's Law


.. _example1:

Example 1: Factors affecting vowel duration
===========================================

Motivation
----------

A number of factors affect the duration of vowels, including:

1. Following consonant voicing (voiced > voiceless)
2. Speech rate
3. Word frequency
4. Neighborhood density

#1 is said to be particularly strong in varieties of English, compared
to other languages (e.g. Chen, 1970). Here we are interested in
examining whether these factors all affect vowel duration, and in
particular in seeing how large and reliable the effect of consonant
voicing is compared to other factors.


Step 1: Creating a query profile
--------------------------------

Based on the motivation above, we want to make a query for:

* All vowels in CVC words (fixed syllable structure)
* Only words where the second C is a stop (to examine following C voicing)
* Only words at the end of utterances (fixed prosodic position)


To perform a query, you need a *query profile*.  This consists of:

* The type of linguistic object being searched for (currently: phone, word, syllable, utterance)
* Filters which restrict the set of objects returned by the query

Once a query profile has been constructed, it can be saved ("Save query profile"). Thus, to carry out a query, you can either create a new one or select an existing one (under "Query profiles").  We'll assume here that a new profile is being created:

1. **Make a new profile**: Under "Query profiles", select "New Query".

2. **Find phones**: Select "phone" under "Linguistic objects to find". The screen should now look like:

    .. image:: ex1Fig1.png
        :width: 563px
        :align: center
        :alt: Image cannot be displayed in your browser

3. **Add filters** to the query.  A single filter is added by pressing
   "+" and constructing it, by making selections from drop-down menus
   which appear. For more information on filters and the intuition
   behind them, see :any:`here <../additional/filters>`.

The first three filters are:

    .. image:: ex1Fig2.png
        :width: 563px
        :align: center
        :alt: Image cannot be displayed in your browser

These do the following:

* *Restrict to utterance-final words* :

    * ``word``: the word containing the phone
    * ``alignment``: something about the word's alignment with respect to a higher unit
    * ``Right aligned with``, ``utterance``: the word should be right-aligned with its containing utterance

* *Restrict to syllabic phones* (vowels and syllabic consonants):

    * ``subset``: refer to a "phone subset", which has been previously defined. Those available in this example include ``syllabics`` and ``consonants``.
    * ``==``, ``syllabic``: this phone should be a syllabic.

* *Restrict to phones followed by a stop* (i.e., not a syllabic)

    * ``following``: refer to the following phone
    * ``manner_of_articulation``: refer to a property of phones, which has been previously defined. Those available here include "manner_of_articulation" and "place_of_articulation"
    * ``==``, ``stop``: the following phone should be a stop.

Then, add three more filters:

    .. figure:: ex1Fig3.png
        :width: 563px
        :align: center
        :alt: Image cannot be displayed in your browser

These do the following:

* *Restrict to phones preceded by a consonant*
* *Restrict to phones which are the second phone in a word*

      * ``previous``: refer to the preceding phone
      * ``alignment``, ``left aligned with``, ``word``: the preceding phone should be left-aligned with (= begin at the same time as) the word containing the *target* phone.  (So in this case, this ensures both that V is preceded by a word-initial C in the same word: #CV.)
* *Restrict to phones which precede a word-final phone*

These filters together form a query corresponding to the desired set of linguistic objects (vowels in utterance-final CVC words, where C\ :sub:`2` \ is a stop).

You should now:

4. **Save the query** : Selecting ``Save query profile``, and entering a name, such as "LibriSpeech CVC".

5. **Run the query** : Select "Run query".


Step 2: Creating an export profile
----------------------------------

The next step is to export information about each vowel token as a CSV file.  We would like the vowel's *duration* and *identity*, as well as the following factors which are expected to affect the vowel's duration:

* *Voicing* of the following consonant

* The word's *frequency* and *neighborhood density*

* The utterance's *speech rate*

In addition, we want some identifying information (to debug, and potentially for building statistical models):

* What *speaker* each token is from

* The *time* where the token occurs in the file

* The *orthography* of the word.



Each of these 9 variables we would like to export corresponds to one row in an *export profile*.

To **create a new export profile**:

1. Select "New export profile" from the "Export query results" menu.
2. Add one row per variable to be exported, as follows: [#f1]_
    * Press "+" (create a new row)
    * Make selections from drop-down menus to describe the variable.
    * Put the name of the variable in the `Output name` field.  (This will be the name of the corresponding column in the exported CSV. You can use whatever name makes sense to you.)


The nine rows to be added for the variables above result in the following export profile:

    .. figure:: ex1Fig4.png
        :width: 600px
        :align: center
        :alt: Image cannot be displayed in your browser



Some explanation of these rows, for a single token:  (We use the [u] in /but/ as a running example)

* Rows 1, 2, 8 are the ``duration``, ``label``, and the beginning time (``time``) of the *phone object* (the [u]), in the containing file.

* Row 3 refers to the ``voicing`` of the *following phone* object(the
  [t])

  * Note that "following" automatically means "following phone"" (i.e., ``phone`` doesn't need to put put after `following`) because the linguistic objects being found are phones. If the linguistic objects being found were syllabes (as in Example 2 below), "following" would automatically mean "following syllable".

* Rows 4, 5, and 9 refer to properties of the *word which contains the
  phone* object: its ``frequency``, ``neighborhood density``, and ``label`` (= orthography, here "boot")

* Row 6 refers to the *utterance which contains the phone*: its ``speech_rate``, defined as syll`ables per second over the utterance.

* Row 7 refers to the *speaker* (their ``name``) whose speech contains this phone.

..
   * Row 8 refers to the *name* of this file` (called a "discourse" in SCT).

Each case can be thought of as a property (shown in ``teletype``) of a linguistic object or organizational unit (shown in *italics*).

You can now:

3. **Save the export profile** : Select "Save as...", then enter a name, such as "LibriSpeech CVC export".

4. **Perform the export** : Select "Run".  You will be prompted to
   enter a filename to export to; make sure it ends in ``.csv`` (e.g. ``librispeechCvc.csv``).


Step 3: Examine the data
------------------------


Here are the first few rows of the resulting data file, in Excel:

    .. figure:: ex1Fig5.png
        :width: 600px
        :align: center
        :alt: Image cannot be displayed in your browser

.. highlight:: r

.. include:: example1Analysis.rst


.. _example2:

Example 2: Polysyllabic shortening
==================================

Motivation
----------

*Polysyllabic shortening* refers to the "same" rhymic unit (syllable or vowel) becoming shorter as the size of the containing domain (word or prosodic domain) increases. Two classic examples:

* English: *stick*, *stick*\y, *stick*\iness (Lehiste, 1972)
* French: \p\ *â*\te, \p\ *â*\té, \p\ *â*\tisserie (Grammont, 1914)

Polysyllabic shortening is often -- but not always -- defined as being
restricted to accented syllables.  (As in the English, but not the
French example.)  Using SCT, we can check whether a couple simple
versions of polysyllabic shortening holds in the LibriSpeech corpus:

1. Considering all utterance-final words, does the initial syllable duration decrease as word length increases?

2. Considering just utterance-final words with primary stress on the *initial* syllable, does the initial syllable duration decrease as word length increases?

We show (1) here, and leave (2) as an exercise.



Step 1: Query profile
---------------------

In this case, we want to make a query for:

* Word-initial syllables
* \.\.\.only in words at the end of utterances (fixed prosodic position)

For this query profile:

* "Linguistic objects to find" = "syllables"
* Filters are needed to restrict to:
    * Word-initial syllables
    * Utterance-final words

This corresponds to the following query profile, which has been saved (in this screenshot) as "PSS: first syllable" in SCT:

    .. image:: ex2Fig1.png
        :width: 614px
        :align: center
        :alt: Image cannot be displayed in your browser


The first and second filters are similar to those in Example 1:

* *Restrict to word-initial syllables*

    * ``alignment``: something about the syllable's alignment
    * ``left aligned with`` ``word``: what it says
* *Restrict to utterance-final words*

    * ``word``: word containing the syllable
    * ``right aligned with`` utterance``: the word and utterance have
      the same end time.

You should **input this query profile**, then **run it** (optionally
saving first).

Step 2: Export profile
----------------------

This query has found all word-initial stressed syllables for words in utterance-final position. We now want to export information about these linguistic objects to a CSV file, for which we again need to construct a query profile.  (You should now **Start a new export profile**.)

We want it to contain everything we need to examine how syllable duration (in seconds) depends on word length (which could be defined in several ways):

* The *duration* of the syllable
* Various word duration measures: the *number of syllables* and *number of phones* in the word containing the syllable, as well as the *duration* (in seconds) of the word.

We also export other information which may be useful (as in Example
1): the *syllable label*, the *speaker name*, the
*time* the token occurs in the file, the *word label* (its
orthography), and the word's *stress pattern*.

The following export profile contains these nine variables:

    .. image:: ex2Fig2.png
        :width: 614px
        :align: center
        :alt: Image cannot be displayed in your browser

After you **enter these rows** in the export profile, **run the export** (optionally saving the export profile first).  I exported it as ``librispeechCvc.csv``.

Step 3: Examine the data
------------------------

.. include:: example2Analysis.rst





.. _example3:

Example 3: Menzerath's Law
==========================

**Motivation**: Menzerath's Law (Menzerath 1928, 1954) refers to the general finding that segments and syllables are shorter in longer words, both in terms of

* duration per unit
* number of units (i.e. segments per syllable)

(Menzerath's Law is related to polysyllabic shortening, but not the same.)

For example, Menzerath's Law predicts that for English:

1. The average duration of syllables in a word (in seconds) should decrease as the number of syllables in the word increases.

2. `` `` for *segments* in a word.

3. The average number of phones per syllable in a word should decrease as the number of syllables in the word increases.

**Exercise**: Build a query profile and export profile to export a
data file which lets you test Menzerath's law for the LibriSpeech corpus.  For example, for prediction (1), you could:

* Find all utterance-final words (to hold prosodic position somewhat constant)
* Export word duration (seconds), number of syllables, anything else necessary.

(This exercise should be possible using pieces covered in Examples 1 and 2, or minor extensions.)

.. [#f1] Note that it is also possible to input some of these rows automatically, using the checkboxes in the `Simple exports` tab.

.. [#f2] Technically, this database consists of two sub-databases: a
     Neo4j database (which contains the hierarchical
     representation of discourses), and a SQL database (which contains lexical and featural information, and cached acoustic measurements).











