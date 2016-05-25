******************************************
Speech Corpus Tools: Tutorial and examples
******************************************



.. _example2:

Example 2	
###################

Step 1: Query profile
*********************

In this case, we want to make a query for:

* Word-initial syllables 
* \.\.\.which are also primary-stressed
* \.\.\.only in words at the end of utterances (fixed prosodic position)

For this query profile:

* "Linguistic objects to find" = "syllables"
* Filters are needed to restrict to:
    * Word-initial syllables
    * Utterance-final words
    * Primary-stressed syllables

This corresponds to the following query profile, which has been saved (in this screenshot) as "PSS: first syllable" in SCT:

	.. image:: ex2Fig1.png
		:width: 450px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser


The first and second filters are similar to those in Example 1:

* *Restrict to word-initial syllables*
    * ``alignment``: something about the syllable's alignment
    * ``left aligned with`` ``word``: what it sas
* *Restrict to utterance-final words*
    * ``word``: word containing the syllable
    * ``right aligned with`` utterance``: the word and utterance have the same ending.
    
The third filter involves a regular expression:

* *Restrict to initial-stressed words*
    * ``word``: word containing the syllable
    * ``stress pattern``: a pattern such as \#1002\#, \#1020\#, \#1\# describing the canonical stress pattern (1, 2, 0 = primary, secondary, none).
    * ``regexp``: a regular expression describing the desired stress pattern. (Here: the string "\#1" followed by any other characters.)

You should **input this query profile**, then **run it** (optionally saving first).  This will take a minute or two.

Step 2: Export profile
**********************

This query has found all word-initial stressed syllables for words in utterance-final position. We now want to export information about these linguistic objects to a CSV file, for which we again need to construct a query profile.  (You should now **Start a new export profile**.)

We want it to contain everything we need to examine how syllable duration (in seconds) depends on word length (which could be defined in several ways):

* The *duration* of the syllable
* Various word duration measures: the *number of syllables* and *number of phones* in the word containing the syllable, as well as the *duration* (in seconds) of the word.

We also export other information which may be useful (as in Example 1): the *syllable label*, the *speaker name*, the *file name*, the *time* the token occurs in the file, and the *word label* (its orthography). 

The following export profile contains these seven variables:

TODO

After you **enter these rows** in the export profile, **run the export** (optionally saving the export profile first).  I exported it as ``polysyllabic.csv``.

Step 3: examine the data
************************

In R\: load in the data\:

	
Exclude a few outliers (must be errors): syllables with durations > 1.5 sec; points from words with duration > 5 sec. We also exclude  points from words with 5 syllables (there are only 2 such points):

	


Plot of the duration of the initial stressed syllable as a function of word duration (in syllables):

	.. image:: ex2Fig2.png
		:width: 450px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser

	

Here we see a clear polysyllabic shortening effect from 1 to 2 syllables, and possibly one from 2 to 3 syllables. Nothing is clear between 3 and 4 syllables.

This plot suggests that the effect is pretty robust across speakers:
	.. image:: ex2Fig3.png
		:width: 450px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser

	
**Exercise**: Try to make a plot like the penultimate one, using word duration on the x axis instead of number of syllables.  (You'll need to use ``geom_smooth()`` instead of ``geom_boxplot()``, if you are using ggplot.)  What issues do you run into?  After these are resolved, do you see the expected pattern? 

Initial syllable duration
##########################

**Exercise**: Try to instead export a CSV like the one just exported, but for all utterance-final words (not just restricting to those with initial stress).  I saved this as ``polysyllabic2.csv``.   

The plot of initial syllable duration as a function of word length (in number of syllables) should now look like:

	.. image:: ex2Fig4.png
		:width: 450px
		:align: center
		:height: 300px
		:alt: Image cannot be displayed in your browser


This plot is quite similar for 1-4 sylalbles to the plot where only initial-stressed words are considered (NB: initial-stressed words make up about 82\% of tokens). For 4-5 syllables, there is no clear change  So at least at this coarse level, it looks like polysyllabic shortening effects for English initial syllables are restricted to relatively short words.




`Vignette <http://sct.readthedocs.io/en/latest/tutorial/vignetteMain.html>`_

`Next <http://sct.readthedocs.io/en/latest/tutorial/tutorial2.html>`_ 			`Previous <http://sct.readthedocs.io/en/latest/tutorial/vignetteMain.html>`_



