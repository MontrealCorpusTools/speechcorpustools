
from PyQt5 import QtGui, QtCore, QtWidgets





class HelpWidget(QtWidgets.QWidget):
    
    def __init__(self):
        super(HelpWidget, self).__init__()
        self.previousLayouts = []
        
        self.superLayout = QtWidgets.QVBoxLayout()
        self.layout = QtWidgets.QStackedLayout()

        self.forwardButton = Buttons('forward')
        self.backButton = Buttons('back')

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.backButton)
        self.hbox.addWidget(self.forwardButton)

        self.superLayout.addLayout(self.hbox)
        
        self.forwardButton.clicked.connect(self.switchLayouts)
        self.backButton.clicked.connect(self.switchLayouts)
        

        self.superLayout.addLayout(self.layout)
        self.setLayout(self.superLayout)

        self.helpInfo = {"utterance":": An utterance is (loosely) a group of sounds delimited by relatively long pauses on either side. This could be a clause, sentence, or phrase.","syllables":"Syllables currently have to be encoded before this option is available. The encoding is done through maximum attested onset","word":" A word is an element on the word-tier.","phone":": A phone is a single speech segment.","alignment":"The position of the object in a super-object (i.e. a word in an utterance, a phone in a word...)","following":"Specifies the object after the current object","previous":"Specifies the object before the current object","subset":"Used to delineate classes of phones and words. Certain classes come premade. Others are avaiable through enrichment","duration":"How much time the object occupies","begin":"The start of the object in time (seconds)","end":"The end of the object in time (seconds)","label":"The orthographic contents of an object","syllable":"Specifies a syllable","speaker":"Specifies the speaker","discourse":"Specifies the discourse, or file","category":"Only available for words, specifies the word category","num_phones":"Only available for words, specifies the number of phones in a word","num_syllables":"Only available for words, specifies the number of syllables in a word","frequency":"Only available for words, specifies the word frequency in the corpus","position_in_utterance":"Only available for words, specifies the word's index in the utterance","neighborhood_density":"Only available for words, specifies the number of phonological neighbours of a given word.","stress_pattern":"Only available for words, specifies the stress patter for a word","transcription":"Only available for words, specifies the phonetic transcription of the word in the corpus","utterance":"Available for all objects except utterance, specifies the utterance that the object came from","syllable_position":"Only available for phones, specifies the phone's position in a syllable","manner_of_articulation":"Only available for phones","place_of_articulation":"Only available for phones","voicing":"Only available for phones","vowel_backness":"Only available for phones","vowel_rounding":"Only available for phones","vowel_height":"Only available for phones","right aligned with":"This will filter for objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus","left aligned with":"This will filter for objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus (","not right aligned with":"This will exclude objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus (","not left aligned with":"This will exclude objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus ","==":"This will filter for objects that are in the class that you select in the third dropdown menu.","==":"This will filter for objects whose property is equal to what you have specified in the text box following this menu.","!=":"This will exclude objects whose property is equal to what you have specified in the text box following this menu.",">=":"This will filter for objects whose property is greater than or equal to what you have specified in the text box following this menu.","<=":"This will filter for objects whose property is less than or equal to what you have specified in the text box following this menu.",">":"This will filter for objects whose property is greater than what you have specified in the text box following this menu.","<":"This will filter for objects whose property is less than what you have specified in the text box following this menu.","stress_pattern":"/","==":"This will filter for objects whose property is equivalent to what you have specified in the text box or dropdown menu following this menu.","!=":"This will exclude objects whose property name is equivalent to what you have specified in the text box or dropdown menu following this menu.","regex":"This option allows you to input a regular expression to match certain properties."}

        

    def getHelpInfo(self, info):

        self.scroll = QtWidgets.QScrollArea()
        done = []
        infoString = ""
        
        for tup in info:
           
            if isinstance(tup, str) :
                done.append(tup)
                try: 
                    infoString+="%s: %s\n\n"%(tup, self.helpInfo[tup.lower().replace("_name", "")])
                except KeyError:
                    pass
            
            if isinstance(tup, tuple):
                for element in tup:
                    if element not in done:
                        try:
                            infoString+="%s: %s\n\n"%(element.lower().replace("_name",""), self.helpInfo[element.lower().replace("_name","")])
                            done.append(element)
                        except KeyError:
                            pass
                  
        self.information = QtWidgets.QLabel(infoString)
        self.information.setWordWrap(True)

        self.scroll.setWidget(self.information)
        self.layout.addWidget(self.scroll)
        self.layout.setCurrentIndex(self.layout.currentIndex()+1)

        

    def getEnrichHelp(self):

        self.scroll = QtWidgets.QScrollArea()

        infoString = "Encode non-speech elements: this allows the user to specify for a given database what should not count as speech\n\nEncode utterances: After encoding non-speech elements, we can use them to define utterances (segments of speech separated by a .15-.5 second pause)\nEncode syllabic segments: This allows the user to specify which segments in the corpus are  counted as syllabic\n\nEncode syllables: if the user has encoded syllabic segments, syllables can now be encoded using maximum attested onset\n\nEncode hierarchical properties: These allow the user to encode such properties as number of syllables in each utterance, or rate of syllables per second\n\nEnrich lexicon: This allows the user to assign certain properties to specific words. For example the user might want to encode word frequency. This can be done by having words in one column and corresponding frequencies in the other column of a column-delimited text file.\n\nEnrich phonological inventory: Similar to lexical enrichment, this allows the user to add certain helpful features to phonological properties -- for example, adding 'fricative' to 'manner_of_articulation' for some phones\n\nEncode subsets: Similar to how syllabic phones were encoded into subsets, the user can encode other phones in the corpus into subsets as well\n\nAnalyze acoustics: This will encode pitch and formants into the corpus. This is necessary to view the waveforms and spectrogram. "
        self.information = QtWidgets.QLabel(infoString)
        self.information.setWordWrap(True)

        self.scroll.setWidget(self.information)
        self.layout.addWidget(self.scroll)
        self.layout.setCurrentIndex(self.layout.currentIndex()+1)
        
    
    def getDiscourseHelp(self):

        self.scroll = QtWidgets.QScrollArea()

        infoString="The top window shows the waveform of the file as well as the transcriptions of the utterance (if encoded), words, and phones. \n \n The bottom window is a spectrogram. This will only be present if a .wav file has been imported for this discourse. This maps time and frequency on the X and Y axes respectively, while the darkeness of an area indicates the amplitude. Lines generated by the software also indicate pitch and formants when available. \n\n To see pitch and formants, acoustics must be analyzed first. This can be done in the \" Enhance Corpus\" toolbar. \n\n Double click on one of the discourses in the \"Discourse\" tab in the upper right window to view its acoustic information \n\n  Spectrogram, pitch, and formants can be toggled on and off by clicking on them."
        self.information = QtWidgets.QLabel(infoString)
        self.information.setWordWrap(True)
     
        self.scroll.setWidget(self.information)
        self.layout.addWidget(self.scroll)

        self.layout.setCurrentIndex(self.layout.currentIndex()+1)
    
    def getConnectionHelp(self):
        
        self.scroll = QtWidgets.QScrollArea()

        infoString= "To connect to servers, Neo4j must be open and running \n\n Make sure that the port is the same as in your Neo4j window. \n\n If it is your first time using the program, nothing will appear in \"Available Corpora\" \n\n IP address (or localhost): This is the address of the Neo4j server. In most cases, it will be \'localhost\' \n\n Port: This is the port through which a connection to the Neo4j server is made. By default, it is 7474. It must always match the port shown in the Neo4j window. \n\n Username and Password: These are by default not required, but available should you need authentication for your Neo4j server \n\n Connect: This button will actually connect the user to the specified server.\n\n Find local audio files: Pressing this allows the user to browse his/her file system for directories containing audiofiles that correspond to files in a corpus.\n\n Corpora: The user select a corpus (for runnning queries, viewing discourses, enrichment, etc.) by clicking that corpus in the \"Available corpora\" menu. The selected corpus will be highlighted in blue or grey.\n\n Import local corpus: This is strictly for constructing a new relational database in Neo4j that does not already exist. Any corpus that has already been imported can be accessed by pressing \"Connect\" and selecting it instead. Re-importing the same corpus will overwrite the previous corpus of the same name, as well as remove any enrichment the user has done on the corpus. \n When importing a new corpus, the user selects the directory of the overall corpus, not specific files or subdirectories."
        self.information = QtWidgets.QLabel(infoString)
        self.information.setWordWrap(True)

        self.scroll.setWidget(self.information)

        self.layout.addWidget(self.scroll)
        
        self.layout.setCurrentIndex(self.layout.currentIndex()+1)
  

    def switchLayouts(self, direction):
        
        if direction is 'back':
            try:
                self.layout.setCurrentIndex(self.layout.currentIndex()-1)
            except Exception:
                self.layout.setCurrentIndex(self.layout.currentIndex())
                
        if direction is 'forward':
            try: 
                self.layout.setCurrentIndex(self.layout.currentIndex()+1)
            except Exception:
                self.layout.setCurrentIndex(self.layout.currentIndex())

class Buttons(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal(object)
    forward = False
    back = False
    
    def __init__(self, Type, parent = None):
        super(Buttons, self).__init__(parent)
        if Type is 'forward':
            self.forwardButton()
        if Type is 'back' :
            self.backButton()
    
    def forwardButton(self):
        self.setText('>')
        self.forward = True
    
    def backButton(self):
        self.setText('<')
        self.back = True

    def mouseReleaseEvent(self, ev):
        if self.forward:
            self.clicked.emit('forward')
        
        if self.back:
            self.clicked.emit('back')
    
class ExportHelpWidget(QtWidgets.QWidget):
    
    def __init__(self):
        super(ExportHelpWidget, self).__init__()
        self.previousLayouts = []
        
        self.superLayout = QtWidgets.QVBoxLayout()
        self.layout = QtWidgets.QStackedLayout()

        self.forwardButton = Buttons('forward')
        self.backButton = Buttons('back')

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.backButton)
        self.hbox.addWidget(self.forwardButton)

        self.superLayout.addLayout(self.hbox)
        
        self.forwardButton.clicked.connect(self.switchLayouts)
        self.backButton.clicked.connect(self.switchLayouts)
        
        self.setWindowTitle("Help")

        self.superLayout.addLayout(self.layout)
        self.setLayout(self.superLayout)

        self.helpInfo = {"utterance":": An utterance is (loosely) a group of sounds delimited by relatively long pauses on either side. This could be a clause, sentence, or phrase.","syllables":"Syllables currently have to be encoded before this option is available. The encoding is done through maximum attested onset","word":": A word is an element on the word-tier.","phone":": A phone is a single speech segment.","alignment":"The position of the object in a super-object (i.e. a word in an utterance, a phone in a word...)","following":"Specifies the object after the current object","previous":"Specifies the object before the current object","subset":"Used to delineate classes of phones and words. Certain classes come premade. Others are avaiable through enrichment","duration":"How much time the object occupies","begin":"The start of the object in time (seconds)","end":"The end of the object in time (seconds)","label":"The orthographic contents of an object","syllable":"Specifies a syllable","speaker":"Specifies the speaker","discourse":"Specifies the discourse, or file","category":"Only available for words, specifies the word category","num_phones":"Only available for words, specifies the number of phones in a word","num_syllables":"Only available for words, specifies the number of syllables in a word","frequency":"Only available for words, specifies the word frequency in the corpus","position_in_utterance":"Only available for words, specifies the word's index in the utterance","neighborhood_density":"Only available for words, specifies the number of phonological neighbours of a given word.","stress_pattern":"Only available for words, specifies the stress patter for a word","transcription":"Only available for words, specifies the phonetic transcription of the word in the corpus","utterance":"Available for all objects except utterance, specifies the utterance that the object came from","syllable_position":"Only available for phones, specifies the phone's position in a syllable","manner_of_articulation":"Only available for phones","place_of_articulation":"Only available for phones","voicing":"Only available for phones","vowel_backness":"Only available for phones","vowel_rounding":"Only available for phones","vowel_height":"Only available for phones","right aligned with":"This will filter for objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus","left aligned with":"This will filter for objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus (","not right aligned with":"This will exclude objects whose rightmost boundary lines up with the rightmost boundary of the object you will select in the third column of dropdown menus","not left aligned with":"This will exclude objects whose leftmost boundary lines up with the left most boundary of the object you will select in the third column of dropdown menus ","==":"This will filter for objects that are in the class that you select in the third dropdown menu.","==":"This will filter for objects whose property is equal to what you have specified in the text box following this menu.","!=":"This will exclude objects whose property is equal to what you have specified in the text box following this menu.",">=":"This will filter for objects whose property is greater than or equal to what you have specified in the text box following this menu.","<=":"This will filter for objects whose property is less than or equal to what you have specified in the text box following this menu.",">":"This will filter for objects whose property is greater than what you have specified in the text box following this menu.","<":"This will filter for objects whose property is less than what you have specified in the text box following this menu.","stress_pattern":"/","==":"This will filter for objects whose property is equivalent to what you have specified in the text box or dropdown menu following this menu.","!=":"This will exclude objects whose property name is equivalent to what you have specified in the text box or dropdown menu following this menu.","regex":"This option allows you to input a regular expression to match certain properties."}


        

    def exportHelp(self, options):
        self.scroll = QtWidgets.QScrollArea()
        done = []
        infoString = ""
        for element in options:
            if element not in done:
                try:
                    infoString+="%s: %s\n\n"%(element.lower().replace("_name",""), self.helpInfo[element.lower().replace("_name","")])
                    done.append(element)
                except KeyError:
                    pass
                  
        self.information = QtWidgets.QLabel(infoString)
        self.information.setWordWrap(True)

        self.scroll.setWidget(self.information)
        self.layout.addWidget(self.scroll)
        self.layout.setCurrentIndex(self.layout.currentIndex()+1)   

        self.show()
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.activateWindow()

    def switchLayouts(self, direction):
        
        if direction is 'back':
            try:
                self.layout.setCurrentIndex(self.layout.currentIndex()-1)
            except Exception:
                self.layout.setCurrentIndex(self.layout.currentIndex())
                
        if direction is 'forward':
            try: 
                self.layout.setCurrentIndex(self.layout.currentIndex()+1)
            except Exception:
                self.layout.setCurrentIndex(self.layout.currentIndex())


