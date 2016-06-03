.. _enrichment:

**********
Enrichment
**********

Databases can be enriched by encoding various elements. Usually, the database starts off with just words and phones, but by using enrichment options a diverse range of options will become available to the user. Here are some of the options:

* **Non-speech elements** this allows the user to specify for a given database what should not count as speech
* **Utterances** After encoding non-speech elements, we can use them to define utterances (segments of speech separated by a .15-.5 second pause)
* **syllabic segments** This allows the user to specify which segments in the corpus are  counted as syllabic
* **Syllables** if the user has encoded syllabic segments, syllables can now be encoded using maximum attested onset
* **Hierarchical properties** These allow the user to encode such properties as number of syllables in each utterance, or rate of syllables per second
* **Lexicon** This allows the user to assign certain properties to specific words. For example the user might want to encode word frequency. This can be done by having words in one column and corresponding frequencies in the other column of a column-delimited text file.
* **phonological inventory** Similar to lexical enrichment, this allows the user to add certain helpful features to phonological properties -- for example, adding 'fricative' to 'manner_of_articulation' for some phones
* **subsets** Similar to how syllabic phones were encoded into subsets, the user can encode other phones in the corpus into subsets as well
* **analyze acousticcs** This will encode pitch and formants into the corpus. This is necessary to view the waveforms and spectrogram. 
