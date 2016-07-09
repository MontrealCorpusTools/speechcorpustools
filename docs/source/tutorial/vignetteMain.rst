.. _vignetteMain:

******************************************
Speech Corpus Tools: Tutorial and examples
******************************************

Vignettes
###################

Several worked examples follow, which demonstrate the workflow of SCT
and how to construct queries and exports. You should be able to
complete each example by following the steps listed in **bold**. The
examples are designed to be completed in order.

Each example results in a CSV file containing data, which you should
then be able to use to visualize the results. Instructions for basic
visualization in R are given (but using another program, such as
Excel, should be possible).


Example 1: Factors affecting vowel duration
*******************************************

:ref:`Example 1 <example1>` : factors affecting vowel duration

Example 2: Polysyllabic shortening
**********************************

**Motivation**:  *Polysyllabic shortening* refers to the "same" rhymic unit (syllable or vowel) becoming shorter as the size of the containing domain (word or prosodic domain) increases. Two classic examples:

* English: *stick*, *stick*\y, *stick*\iness (Lehiste, 1972)
* French: \p\ *â*\te, \p\ *â*\té, \p\ *â*\tisserie (Grammont, 1914)

Polysyllabic shortening is often -- but not always -- defined as being restricted to accented syllables.  (As in the English, but not the French example.)  Using SCT, we can check whether a couple simple versions of polysyllabic shortening holds in the Buckeye corpus:

1. Considering just utterance-final words with primary stress on the *initial* syllable, does the initial syllable duration decrease as word length increases?

2. Considering all utterance-final words, does the initial syllable duration decrease as word length increases?

We show (1) here, and leave (2) as an exercise.

:ref:`Example 2 <example2>`

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

:ref:`Next <example1>` 			:ref:`Previous <enrichment_tutorial>`




