******************************************
Speech Corpus Tools: Tutorial and examples
******************************************



.. _enrichment:

Enriching databases
###################

SCT supports an array of enrichments on what is imported.  Typically a corpus starts off with just words and phones, but higher level information about utterances and intermediate information about syllables is useful for corpus research.  In this section, there will be a pipeline that you should follow for enriching your corpus.

Non-speech elements
*******************

The first aspect of enrichment to run is encoding whether some annotations are not speech.  These can be things like silence, coughs, laughter, etc.  To encode non-speech elements:

1. Go to the "Enhance corpus" menu
2. Select the "Encode non-speech elements..." option
3. Replace the default regular expression if needed
  * The default is the regular expression for the Buckeye corpus
  * It matches all annotations for silence, the interviewer, laughter and other such elements
  * For FAVE, set it to ``^sp$``
  * For TIMIT and other force-aligned TextGrids, set it to ``^<SIL>$``
4. Press Encode and wait for it to finish



Utterances
**********

The primary function of encoding non-speech elements is to use them as the boundaries of utterances.  In general, we define pauses between utterances to be a non-speech element (usually silence) of greater than some duration, usually 0.15 or 0.5 seconds.  

To encode utterances:

1. Go to the "Enhance corpus" menu
2. Select the "Encode utterances..." option
3. Replace the default values if needed
  * The default is set to 0 (every non speech element is a pause between utterances), change to 0.15 to encode pauses as 150 ms
4. Press Encode and wait for it to finish

Syllables
*********

Syllables are encoded in two steps.  First, the set of syllabic segments in the phonological inventory have to be specified.

To specify segments as syllablic:

1. Go to the "Enhance corpus" menu
2. Select the "Encode syllabic segments..." option
3. Change the default values as necessary
  *  By default it selects segments that contain the characters `i e a o u`, which covers a number of machine readable/non-ipa alphabets
4. Press Encode and wait for it to finish

Once syllabic segments have been encoded as such, you can encode the syllables themselves. In addition, queries will allow you to filter based on phones subset being ``syllabic``.

To do so:

1. Go to the "Enhance corpus" menu
2. Select the "Encode syllables..." option
3. Select the desired algorithm
  *  At the moment only a "maximum attested onset" algorithm is implemented
    *  This algorithm finds all the onsets at the beginnings of words
    *  Any consonantal string between two vowels is split up in such a way that as many segments are put into the onset as possible given the attested onsets at the beginnings of words
  *  Other algorithms will be implemented in the future
4. Press Encode and wait for it to finish

Hierarchical properties
***********************

Useful information is available once the hierarchy has been fleshed out beyond words and phones.  For instance, once utterances and syllables are encoded, you can count all of the syllables in each utterance, or get the rate of them per second (a common definition of speech rate).  These properties are useful to cache before queries because their calculation is time intensive, but the results do not change. An utterance, once encoded, will always have the same number of syllables in it.

To encode a hierarchical property:

1. Go to the "Enhance corpus" menu
2. Select the "Encode hierarchical properties..." option
3. Select the higher annotation

  * For speech rate, this would be ``utterance``
  * For number of syllables in a word, this would be ``word``
  * For a word's position in its utterance, this would be ``utterance``
  
4. Select the lower annotation

  * For both speech rate and word, this would be ``syllable``
  * For a word's position in its utterance, this would be ``word``
  
5. Select the type of property

  * For speech rate, this would be ``rate``
  * For number of syllables in a word, this would be ``count``
  * For a word's position in its utterance, this would be ``position``
  
6. Enter a name for the property

  * The default is intended to be descriptive, but overly so
  
7. Press Encode and wait for it to finish

Enriching the lexicon
*********************

Often we would like to query based on properties of words gathered from outside the corpus itself. For instance, part of speech is often not encoded in corpora when they're imported, but could be a criteria to search for or to exclude.  Likewise, if a particular set of words is needed, they can be encoded with a property offline to facilitate queries later.

The format of files for enriching the lexicon requires a named column-delimited text file (CSV, tab-delimited text file, etc) with headers.  The first column should be the orthography of the word, the name of the column is not used.  Subsequent columns correspond to properties to be encoded, where the sanitized name of the column with used as the name of the property in the database.  For instance, a column named "Frequency" with a column of numerical values will become a numeric property named "Frequency" that can be filtered on.

The words specified in the text file does not have to be exhaustive, it will set properties for each word that is found, and leave the other ones alone.  If you have a specific set of words you'd like to search for, you can create a text file with the first column having the orthography, and the second column a property named "Desired" with every word having a corresponding "True" value in that column.  Then you can do a search for every word that has a value of ``True`` for its ``Desired`` property.

To enrich the lexicon:

#. Go to the "Enhance corpus" menu
#. Select the "Encode lexicon..." option
#. If you would like to ensure case-sensitivity, press the corresponding check box.
#. Press "Encode" and select a text file on your computer and wait for it to finish


Enriching the phonological inventory
************************************

Similar to lexicons, it is often useful to enrich the phonological inventories of corpora.  These can be features such as ``+`` for a feature ``anterior`` or a value of ``fricative`` for a property such as ``manner_of_articulation``.

The format of files that are used for inventory enrichment mirrors that for lexicon enrichment.  They should be column-delimited text files with headers where the first column corresponds to the segment label and subsequent columns are properties to be encoded on the segments.


#. Go to the "Enhance corpus" menu
#. Select the "Encode phonological inventory..." option
#. Press "Encode" and select a text file on your computer and wait for it to finish

Encode phone subsets/classes
****************************

You can encode some arbitrary subset of phones as a particular label, similar to how syllabic segments were encoded with the subset label of ``syllabic``.

#. Go to the "Enhance corpus" menu
#. Select the "Encode phone subsets (classes)..." option
#. Enter in a label for the subset/class
#. Select the phones to be classified
#. Press Encode and wait for it to finish

Analyze acoustics
*****************

Acoustics (pitch and formants) can be encoded to enrich the corpus.  At the moment, such encoding is only relevant for when inspecting the waveform/spectrogram, as their is currently no way to query acoustics.  The encoding for acoustics will also take a while depending on the size of the sound files/corpus, so I do not recommend using this option in the current state of SCT.




`Next <http://sct.readthedocs.io/en/latest/tutorial/vignetteMain.html>`_ 			`Previous <http://sct.readthedocs.io/en/latest/tutorial/buckeye.html>`_





