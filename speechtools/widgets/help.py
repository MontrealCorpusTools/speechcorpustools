
from PyQt5 import QtGui, QtCore, QtWidgets

class HelpWidget(QtWidgets.QWidget):
    def __init__(self):
        super(HelpWidget, self).__init__()

        

        self.layout = QtWidgets.QHBoxLayout()

        

        self.setLayout(self.layout)
        

    def getHelpInfo(self, info):#word":"Specifies a word (only available for Utterance, Syllable, and Phone)",
    #	helpInfo = {"utterance":": An utterance is (loosely) a group of sounds delimited by relatively long pauses on either side. This could be a clause, sentence, or phrase.","syllables":"Syllables currently have to be encoded before this option is available. The encoding is done through maximum attested onset","word":": A word is an element on the word-tier.","phone":": A phone is a single speech segment.","alignment":"The position of the object in a super-object (i.e. a word in an utterance, a phone in a word...)","following":"Specifies the object after the current object","previous":"Specifies the object before the current object","subset":"Used to delineate classes of phones and words. Certain classes come premade. Others are avaiable through enrichment","duration":"How much time the object occupies","begin":"The start of the object in time (seconds)","end":"The end of the object in time (seconds)","label":"The orthographic contents of an object","word":"Specifies a word (only available for Utterance, Syllable, and Phone)","syllable":"Specifies a syllable","phone":"Specifies a phone","speaker":"Specifies the speaker","discourse":"Specifies the discourse, or file","category":"Only available for words, specifies the word category","num_phones":"Only available for words, specifies the number of phones in a word","num_syllables":"Only available for words, specifies the number of syllables in a word","frequency":"Only available for words, specifies the word frequency in the corpus","position_in_utterance":"Only available for words, specifies the word's index in the utterance","neighborhood_density":"Only available for words, specifies the number of phonological neighbours of a given word.","stress_pattern":"Only available for words, specifies the stress patter for a word","transcription":"Only available for words, specifies the phonetic transcription of the word in the corpus","syllable_position":"Only available for phones, specifies the phone's position in a syllable","manner_of_articulation":"Only available for phones","place_of_articulation":"Only available for phones","voicing":"Only available for phones","vowel_backness":"Only available for phones","vowel_rounding":"Only available for phones","vowel_height":"Only available for phones"}
    	#clear all previous help
    	for i in reversed(range(self.layout.count())):
    		self.layout.itemAt(i).widget().setParent(None)
    	helpInfo = {"utterance":": An utterance is (loosely) a group of sounds delimited by relatively long pauses on either side. This could be a clause, sentence, or phrase.","syllables":"Syllables currently have to be encoded before this option is available. The encoding is done through maximum attested onset","word":": A word is an element on the word-tier.","phone":": A phone is a single speech segment.","alignment":"The position of the object in a super-object (i.e. a word in an utterance, a phone in a word...)","following":"Specifies the object after the current object","previous":"Specifies the object before the current object","subset":"Used to delineate classes of phones and words. Certain classes come premade. Others are avaiable through enrichment","duration":"How much time the object occupies","begin":"The start of the object in time (seconds)","end":"The end of the object in time (seconds)","label":"The orthographic contents of an object","syllable":"Specifies a syllable","speaker":"Specifies the speaker","discourse":"Specifies the discourse, or file","category":"Only available for words, specifies the word category","num_phones":"Only available for words, specifies the number of phones in a word","num_syllables":"Only available for words, specifies the number of syllables in a word","frequency":"Only available for words, specifies the word frequency in the corpus","position_in_utterance":"Only available for words, specifies the word's index in the utterance","neighborhood_density":"Only available for words, specifies the number of phonological neighbours of a given word.","stress_pattern":"Only available for words, specifies the stress patter for a word","transcription":"Only available for words, specifies the phonetic transcription of the word in the corpus","utterance":"Available for all objects except utterance, specifies the utterance that the object came from","syllable_position":"Only available for phones, specifies the phone's position in a syllable","manner_of_articulation":"Only available for phones","place_of_articulation":"Only available for phones","voicing":"Only available for phones","vowel_backness":"Only available for phones","vowel_rounding":"Only available for phones","vowel_height":"Only available for phones","right aligned with":"This will filter for objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus","left aligned with":"This will filter for objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus (","not right aligned with":"This will exclude objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus (","not left aligned with":"This will exclude objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus ","==":"This will filter for objects that are in the class that you select in the third dropdown menu.","==":"This will filter for objects whose property is equal to what you have specified in the text box following this menu.","!=":"This will exclude objects whose property is equal to what you have specified in the text box following this menu.",">=":"This will filter for objects whose property is greater than or equal to what you have specified in the text box following this menu.","<=":"This will filter for objects whose property is less than or equal to what you have specified in the text box following this menu.",">":"This will filter for objects whose property is greater than what you have specified in the text box following this menu.","<":"This will filter for objects whose property is less than what you have specified in the text box following this menu.","stress_pattern":"/","==":"This will filter for objects whose property is equivalent to what you have specified in the text box or dropdown menu following this menu.","!=":"This will exclude objects whose property name is equivalent to what you have specified in the text box or dropdown menu following this menu.","regex":"This option allows you to input a regular expression to match certain properties."}

    	self.scroll = QtWidgets.QScrollArea()
    	done = []
    	infoString = ""
    	print(info)
    	for tup in info:
    		try:
    			if isinstance(tup, str) and tup not in done:
    				done.append(tup)
    				infoString+="%s: %s\n\n"%(tup, helpInfo[tup.lower().replace("_name", "")])
    		except:
    			print("not in the dict")
    		if isinstance(tup, tuple):
    			for element in tup:
    				if element not in done:
	    				try:
    						infoString+="%s: %s\n\n"%(element.lower().replace("_name",""), helpInfo[element.lower().replace("word_name","word")])
    						done.append(element)
    					except Exception:
    						print("%s\n"%(element))
    		

    	self.information = QtWidgets.QLabel(infoString)
    	#information.setMinimumSize(200, 200)
    	self.information.setWordWrap(True)
    	self.scroll.setWidget(self.information)
    	self.layout.addWidget(self.scroll)
    
    def getEnrichHelp(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        self.scroll = QtWidgets.QScrollArea()

        infoString = "Encode non-speech elements: this allows the user to specify for a given database what should not count as speech\nEncode utterances: After encoding non-speech elements, we can use them to define utterances (segments of speech separated by a .15-.5 second pause)\nEncode syllabic segments: This allows the user to specify which segments in the corpus are  counted as syllabic\nowEncode syllables: if the user has encoded syllabic segments, syllables can now be encoded using maximum attested onset\nEncode hierarchical properties: These allow the user to encode such properties as number of syllables in each utterance, or rate of syllables per second\nEnrich lexicon: This allows the user to assign certain properties to specific words. For example the user might want to encode word frequency. This can be done by having words in one column and corresponding frequencies in the other column of a column-delimited text file.\nEnrich phonological inventory: Similar to lexical enrichment, this allows the user to add certain helpful features to phonological properties -- for example, adding 'fricative' to 'manner_of_articulation' for some phones\nEncode subsets: Similar to how syllabic phones were encoded into subsets, the user can encode other phones in the corpus into subsets as well\nAnalyze acousticcs: This will encode pitch and formants into the corpus. This is necessary to view the waveforms and spectrogram. "
        self.information = QtWidgets.QLabel(infoString)
        #information.setMinimumSize(200, 200)
        self.information.setWordWrap(True)
        self.scroll.setWidget(self.information)
        self.layout.addWidget(self.scroll)

    def getDiscourseHelp(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        self.scroll = QtWidgets.QScrollArea()

        infoString="This is discourse help"
        self.information = QtWidgets.QLabel(infoString)
        #information.setMinimumSize(200, 200)
        self.information.setWordWrap(True)
        self.scroll.setWidget(self.information)
        self.layout.addWidget(self.scroll)


