******************************************
Speech Corpus Tools: Tutorial and examples
******************************************



.. _tutintroduction:

Introduction to Tutorial
########################

.. _PGDB website: http://montrealcorpustools.github.io/PolyglotDB/

.. _GitHub repository: https://https://github.com/mmcauliffe/speechcorpustools

Speech Corpus Tools is a system for going from a raw speech corpus to a data file (CSV) ready for further analysis (e.g. in R), which conceptually consists of a pipeline of four steps:

1. **Import** the corpus into SCT
	* Result: a structured database of linguistic objects (words, phones, discourses).

2. **Enrich** the database
    * Result: Further linguistic objects (utterances, syllables), and information about objects (e.g. speech rate, word frequencies). 

3. **Query** the database
    * Result: A set of linguistic objects of interest (e.g. utterance-final *words* ending with a stop), 

4. **Export** the results
    * Result: A CSV file containing information about the set of objects of interest

Ideally, the import and enrichment steps are only performed once for a given corpus.  The typical use case of SCT is performing a query and export corresponding to some linguistic question(s) of interest.

This document is structured as follows:

* `Installation <http://sct.readthedocs.io/en/latest/tutorial/installation.html>`_: Install necessary software

* `Librispeech database <http://sct.readthedocs.io/en/latest/tutorial/buckeye.html>`_: Obtain a database for the Librispeech Corpus where the *import* and *enrichment* steps have been completed , either by using `premade <http://sct.readthedocs.io/en/latest/tutorial/premade.html>`_ or doing the import and enrichment steps `yourself <http://sct.readthedocs.io/en/latest/tutorial/buildown.html>`_.

* `Examples <http://sct.readthedocs.io/en/latest/tutorial/vignetteMain.html>`_: Two worked examples illustrating the *Query* and *Export* steps, including creating "Query profiles" and "Export profiles".

* `Next steps <http://sct.readthedocs.io/en/latest/tutorial/nextsteps.html>`_ : Next steps with SCT after the tutorial: pointers to different places in the documentation and presentations where SCT is described.  Intended to kickstart carrying out your own analyses, or applying SCT to your own corpus.

`Next <http://sct.readthedocs.io/en/latest/tutorial/installation.html>`_

