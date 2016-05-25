******************************************
Speech Corpus Tools: Tutorial and examples
******************************************



.. _example1:

Example 1	
###################

Step 1: Creating a query profile
********************************

Based on the motivation in `vignettes <http://sct.readthedocs.io/en/latest/tutorial/vignetteMain.html>`_, we want to make a query for:

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
		:width: 450px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser

	


3. **Add filters** to the query.  A single filter is added by pressing "+" and constructing it, by making selections from drop-down menus which appear.
   
The first three filters are: 

	.. image:: ex1Fig2.png
		:width: 450px
		:align: center
		:height: 300px
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
		:width: 450px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser

	

These do the following:

* *Restrict to phones preceded by a consonant*

* *Restrict to phones which are the second phone in a word*
    * ``previous``: refer to the preceding phone
    * ``alignment``, ``left aligned with``, ``word``: the preceding phone should be left-aligned with (= begin at the same time as) the word containing the *target* phone.  (So in this case, this ensures both that V is preceded by a word-initial C in the same word: #CV.)

* *Restrict to phones which precede a word-final phone*

These filters together form a query corresponding to the desired set of linguistic objects (vowels in utterance-final CVC words, where C\ :sub:`2` \ is a stop).  

You should now:

4. **Save the query** : Selecting ``Save query profile``, and entering a name, such as "Buckeye CVC".

5. **Run the query** : Select "Run query".

This will take a while (probably several minutes).

Step 2: Creating an export profile
**********************************

The next step is to export information about each vowel token as a CSV file.  We would like the vowel's *duration* and *identity*, as well as the following factors which are expected to affect the vowel's duration:

* *Voicing* of the following consonant

* The word's *frequency* and *neighborhood density*

* The utterance's *speech rate*

In addition, we want some identifying information (to debug, and potentially for building statistical models):

* What *speaker* and *file* each token is from

* The *time* where the token occurs in the file

* The *orthography* of the word.

* The identity of the *preceding* and *following* consonants.

Each of these 12 variables we would like to export corresponds to one row in an *export profile*. 

To **create a new export profile**:

1. Select "New export profile" from the "Export query results" menu.  

2. Add one row per variable to be exported, as follows:

    * Press "+" (create a new row)

    * Make selections from drop-down menus to describe the variable.

    * Put the name of the variable in the `Output name` field.  (This will be the name of the corresponding column in the exported CSV. You can use whatever name makes sense to you.)

The twelve rows to be added for the variables above result in the following export profile:

	.. figure:: ex1Fig4.png
		:width: 600px
		:align: center
		:height: 450px
		:alt: Image cannot be displayed in your browser



Some explanation of these rows, for a single token:  (We use the [u] in /but/ as a running example)

* Rows 1, 2, 9 are the ``duration``, ``label``, and the beginning time (``time``) of the *phone object* (the [u]), in the containing file.

* Row 8 refers to the *name* of this file` (called a "discourse" in SCT).

* Rows 3 and 12 refer to the *following phone* object (the [t]): its ``label``, and its ``voicing`` (whether it is voiced or voiceless).
    * Note that "following" automatically means "following phone"" (i.e., ``phone`` doesn't need to put put after `following`) because the linguistic objects being found are phones. If the linguistic objects being found were syllabes (as in Example 2 below), "following" would automatically mean "following syllable".
    
* Row 11 refers, analogously, to the ``label`` of the *preceding phone* object (the [b]).

* Rows 4, 5, and 10 refer to properties of the *word which contains the phone* object: its ``label`` (= orthography, here "boot"), ``neighborhood_density``, and ``frequency``.
    
* Row 6 refers to the *utterance which contains the phone*: its ``speech_rate``, defined as syll`ables per second over the utterance.

* Row 7 refers to the *speaker* (their ``name``) whose speech contains this phone.


Each case can be thought of as a property (shown in ``teletype``) of a linguistic object or organizational unit (shown in *italics*).


You can now:

3. **Save the export profile** : Select "Save as...", then enter a name, such as "Buckeye CVC export".

4. **Perform the export** : Select "Run".  You will be prompted to enter a filename to export to; make sure it ends in ``.csv`` (e.g. ``buckeyeCvc.csv``).

This will take a while (probably several minutes).

Step 3: Examine the data file; basic analysis
*********************************************

Here are the first few rows of the resulting data file, in Excel:
	.. figure:: ex1Fig5.png
		:width: 600px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser

	
For example, row 2 TODO. (comes at the end of the utterance "not ever been taught")


TODO: R code to load data and see the basic results (big speech rate and frequency effects; small stop voicing effect; no neighborhood density effect).


`Next <http://sct.readthedocs.io/en/latest/tutorial/example2.html>`_ 			`Previous <http://sct.readthedocs.io/en/latest/tutorial/vignetteMain.html>`_


