.. _enrichment:

**********
Enrichment
**********

Databases can be enriched by encoding various elements. Usually, the database starts off with just words and phones, but by using enrichment options a diverse range of options will become available to the user. Here are some of the options:

* **Encode non-speech elements** this allows the user to specify for a given database what should not count as speech
* **Encode utterances** After encoding non-speech elements, we can use them to define utterances (segments of speech separated by a .15-.5 second pause)
* **Encode syllabic segments** This allows the user to specify which segments in the corpus are  counted as syllabic
* **Encode syllables** if the user has encoded syllabic segments, syllables can now be encoded using maximum attested onset
* **Encode hierarchical properties** These allow the user to encode such properties as number of syllables in each utterance, or rate of syllables per second
* **Enrich lexicon** This allows the user to assign certain properties to specific words using a CSV file. For example the user might want to encode word frequency. This can be done by having words in one column and corresponding frequencies in the other column of a column-delimited text file.
* **Enrich phonological inventory** Similarly to lexical enrichment, this allows the user to add certain helpful features to phonological properties -- for example, adding 'fricative' to 'manner_of_articulation' for some phones
* **Enrich speakers** Like phonological and lexial enrichment, this allows the user to add speaker metadata from a CSV such as sex and age. 
* **Encode subsets** Similarly to how syllabic phones were encoded into subsets, the user can encode other phones in the corpus into subsets as well
* **Encode relativized measures** This permits the user to encode the following statistics

	* **Phone**
		* Mean duration
		* Median duration
		* Standard deviation of duration
	* **Word**
		* Mean duration
		* Median duration
		* Standard deviation of duration
		* Baseline duration - this is the sum of the mean durations of the constituent phones
	* **Syllable**
		* Mean duration
		* Median duration
		* Standard deviation of duration
	* **Speaker**
		* Average speech rate
* **Encode stress/tone** Certain corpus alphabets will come with stress or tone information embedded in vowel characters. For example, in some CMUdict corpora primary stress on the vowel "AA" is represented by "AA1". This enrichment function allows the user to specify a regular expression to split this information off of the vowel and encode it onto the syllable. The default expressions are for LibriSpeech (stress) and GlobalPhone (tone)
* **Analyze acousticcs** This will encode pitch and formants into the corpus. This is necessary to view the waveforms and spectrogram. 
