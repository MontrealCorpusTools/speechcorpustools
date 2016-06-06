.. _buildingqueries:

*****************
Building Queries
*****************


Now you're ready to start building queries. Here's an overview of what each dropdown item signifies

Linguistic Objects
##################

* **Utterance**: An utterance is (loosely) a group of sounds delimited by relatively long pauses on either side. This could be a clause, sentence, or phrase. 
* **Syllables** Syllables currently have to be encoded before this option is available. The encoding is done through maximum attested onset
* **Word**: A word is an element on the word-tier.
* **Phone**: A phone is a single speech segment. 

Filters
#######
Filters are conditions that must be satisfied for data to pass through. For example
	.. image:: filter.png
		:width: 910px
		:height: 31px
		:alt: Image cannot be displayed in your browser
		:align: center
is a filter

Many filters have dropdown menus. These look like this:
	.. image:: dropdown.png
		:width: 926px
		:height: 232px
		:alt: Image cannot be displayed in your browser
		:align: center
Generally speaking, the first dropdown menu is used to target a property. Possible properties are:

* **alignment** The position of the object in a super-object (i.e. a word in an utterance, a phone in a word...) 
* **following** Specifies the object after the current object
* **previous** Specifies the object before the current object
* **subset** Used to delineate classes of phones and words. Certain classes come premade. Others are avaiable through enrichment 
* **duration** How much time the object occupies 
* **begin** The start of the object in time (seconds)
* **end** The end of the object in time (seconds)
* **label** The orthographic contents of an object
* **word** Specifies a word (only available for Utterance, Syllable, and Phone)
* **syllable** Specifies a syllable
* **phone** Specifies a phone
* **speaker** Specifies the speaker 
* **discourse** Specifies the discourse, or file
* **category** Only available for words, specifies the word category
* **num_phones** Only available for words, specifies the number of phones in a word
* **num_syllables** Only available for words, specifies the number of syllables in a word
* **frequency** Only available for words, specifies the word frequency in the corpus
* **position_in_utterance** Only available for words, specifies the word's index in the utterance
* **neighborhood_density** Only available for words, specifies the number of phonological neighbours of a given word.
* **stress_pattern** Only available for words, specifies the stress patter for a word
* **transcription** Only available for words, specifies the phonetic transcription of the word in the corpus
* **utterance** Available for all objects except utterance, specifies the utterance that the object came from 
* **syllable_position** Only available for phones, specifies the phone's position in a syllable
* **manner_of_articulation** Only available for phones
* **place_of_articulation** Only available for phones
* **voicing** Only available for phones
* **vowel_backness** Only available for phones
* **vowel_rounding** Only available for phones
* **vowel_height** Only available for phones

The second filter will depend on which filter you chose in the first column. For example, if you chose **phone** you will get all of the phone options specified above. However if you choose **label** you will be presented with a different type of dropdown menu. This section covers some of these possibilities.
	* **alignment**
		* **right aligned with** This will filter for objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus (**utterance**, **syllable**, **word**, or **phone**).
		* **left aligned with** This will filter for objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus (**utterance**, **syllable**, **word**, or **phone**).
		* **not right aligned with** This will exclude objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus (**utterance**, **syllable**, **word**, or **phone**).
		* **not left aligned with** This will exclude objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus (**utterance**, **syllable**, **word**, or **phone**).
	* **subset**
		* **==** This will filter for objects that are in the class that you select in the third dropdown menu.
	* **begin**/**end**/**num_phones**/**num_syllables**/**position_in_utterance**/**frequency**/**neighborhood_density**/**duration**
		* **==** This will filter for objects whose property is equal to what you have specified in the text box following this menu.
		* **!=** This will exclude objects whose property is equal to what you have specified in the text box following this menu.
		* **>=** This will filter for objects whose property is greater than or equal to what you have specified in the text box following this menu.
		* **<=** This will filter for objects whose property is less than or equal to what you have specified in the text box following this menu.
		* **>** This will filter for objects whose property is greater than what you have specified in the text box following this menu.
		* **<** This will filter for objects whose property is less than what you have specified in the text box following this menu.
	* **stress_pattern**/**category**/**label**/**speaker** \+ **name**/**discourse** \+ **name**/**transcription**/**vowel_height**/**vowel_backness**/**vowel_rounding**/**manner_of_articulation**/**place_of_articulation**/**voicing**
		* **==** This will filter for objects whose property is equivalent to what you have specified in the text box or dropdown menu following this menu.
		* **!=** This will exclude objects whose property name is equivalent to what you have specified in the text box or dropdown menu following this menu.
		* **regex** This option allows you to input a regular expression to match certain properties.

Experiment with combining these filters. Remember that each time you add a filter, you are applying further restrictions on the data. 
