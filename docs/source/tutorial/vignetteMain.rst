.. _vignetteMain:

Tutorial: Examples
###################

Several worked examples follow, which demonstrate the workflow of SCT
and how to construct queries and exports. You should be able to
complete each example by following the steps listed in **bold**. The
examples are designed to be completed in order.

Each example results in a CSV file containing data, which you should
then be able to use to visualize the results. Instructions for basic
visualization in R are given (but using another program, such as
Excel, should be possible).

:ref:`Example 1 <example1>` : Factors affecting vowel duration

:ref:`Example 2 <example2>` : Polysyllabic shortening

:ref:`Example 3 <example3>` : Menzerath's Law


.. _example1:

Example 1: Factors affecting vowel duration
*******************************************

Motivation
==========

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
================================

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

3. **Add filters** to the query.  A single filter is added by pressing "+" and constructing it, by making selections from drop-down menus which appear. For more information on filters, see :any:`this page <../additional/filters>`.

The first three filters are:

    .. image:: ex1Fig2.png
        :width: 563px
        :align: center
        :alt: Image cannot be displayed in your browser

These do the following:

* *Restrict to utterance-final words*:
    * ``word``: the word containing the phone
    * ``alignment``: something about the word's alignment with respect to a higher unit
    * ``Right aligned with``, ``utterance``: the word should be right-aligned with its containing utterance

* *Restrict to syllabic phones* (vowels and syllabic consonants):
    * ``subset``: refer to a "phone subset", which has been previously defined. Those available in this example include ``syllabics`` and ``consonants``.
    * ``==``, ``syllabic``: this phone should be a syllabic.

* *Restrict to phones followed by a stop*
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

This will take a while (0.5-2 minutes).

Step 2: Creating an export profile
==================================

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

..
   * Row 8 refers to the *name* of this file` (called a "discourse" in SCT).

* Row 3 refers to the ``voicing`` of the *following phone* object (the [t])
    * Note that "following" automatically means "following phone"" (i.e., ``phone`` doesn't need to put put after `following`) because the linguistic objects being found are phones. If the linguistic objects being found were syllabes (as in Example 2 below), "following" would automatically mean "following syllable".

* Rows 4, 5, and 9 refer to properties of the *word which contains the
  phone* object: its ``frequency``, ``neighborhood density``, and ``label`` (= orthography, here "boot")

* Row 6 refers to the *utterance which contains the phone*: its ``speech_rate``, defined as syll`ables per second over the utterance.

* Row 7 refers to the *speaker* (their ``name``) whose speech contains this phone.

Each case can be thought of as a property (shown in ``teletype``) of a linguistic object or organizational unit (shown in *italics*).

You can now:

3. **Save the export profile** : Select "Save as...", then enter a name, such as "LibriSpeech CVC export".

4. **Perform the export** : Select "Run".  You will be prompted to
   enter a filename to export to; make sure it ends in ``.csv`` (e.g. ``librispeechCvc.csv``).

This will take a while (probably several minutes).

Step 3: Examine the data file; basic analysis
=============================================

Here are the first few rows of the resulting data file, in Excel:
    .. figure:: ex1Fig5.png
        :width: 600px
        :align: center
        :alt: Image cannot be displayed in your browser

.. highlight:: r

.. include:: example1Analysis.rst


.. _example2:

Example 2: Polysyllabic shortening
**********************************

**Motivation**:  *Polysyllabic shortening* refers to the "same" rhymic unit (syllable or vowel) becoming shorter as the size of the containing domain (word or prosodic domain) increases. Two classic examples:

* English: *stick*, *stick*\y, *stick*\iness (Lehiste, 1972)
* French: \p\ *â*\te, \p\ *â*\té, \p\ *â*\tisserie (Grammont, 1914)

Polysyllabic shortening is often -- but not always -- defined as being restricted to accented syllables.  (As in the English, but not the French example.)  Using SCT, we can check whether a couple simple versions of polysyllabic shortening holds in the Buckeye corpus:

1. Considering all utterance-final words, does the initial syllable duration decrease as word length increases?

2. Considering just utterance-final words with primary stress on the *initial* syllable, does the initial syllable duration decrease as word length increases?

We show (1) here, and leave (2) as an exercise.



Step 1: Query profile
=====================

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
======================

This query has found all word-initial stressed syllables for words in utterance-final position. We now want to export information about these linguistic objects to a CSV file, for which we again need to construct a query profile.  (You should now **Start a new export profile**.)

We want it to contain everything we need to examine how syllable duration (in seconds) depends on word length (which could be defined in several ways):

* The *duration* of the syllable
* Various word duration measures: the *number of syllables* and *number of phones* in the word containing the syllable, as well as the *duration* (in seconds) of the word.

We also export other information which may be useful (as in Example
1): the *syllable label*, the *speaker name*, the
*time* the token occurs in the file, the *word label* (its
orthography), and the word's *stress pattern*

The following export profile contains these nine variables:

    .. image:: ex2Fig2.png
        :width: 614px
        :align: center
        :alt: Image cannot be displayed in your browser

After you **enter these rows** in the export profile, **run the export** (optionally saving the export profile first).  I exported it as ``polysyllabic.csv``.

Step 3: examine the data
========================

.. include:: example2Analysis.rst





.. _example3:

Example 3: Menzerath's Law
**************************

**Motivation**: Menzerath's Law (Menzerath 1928, 1954) refers to the general finding that segments and syllables are shorter in longer words, both in terms of

* duration per unit
* number of units (i.e. segments per syllable)

(Menzerath's Law is related to polysyllabic shortening, but not the same.)

For example, Menzerath's Law predicts that for English:

1. The average duration of syllables in a word (in seconds) should decrease as the number of syllables in the word increases.

2. `` `` for *segments* in a word.

3. The average number of phones per syllable in a word should decrease as the number of syllables in the word increases.

**Exercise**: Build a query profile and export profile to export a data file which lets you test Menzerath's law for the Buckeye corpus.  For example, for prediction (1), you could:

* Find all utterance-final words (to hold prosodic position somewhat constant)
* Export word duration (seconds), number of syllables, anything else necessary.

(This exercise should be possible using pieces covered in Examples 1 and 2, or minor extensions.)

.. [#f1] Note that it is also possible to input some of these rows automatically, using the checkboxes in the `Simple exports` tab.


:any:`Next <nextsteps>`             :any:`Previous <librispeech>`




