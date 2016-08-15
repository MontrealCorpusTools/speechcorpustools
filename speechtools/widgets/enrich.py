
import re

from collections import OrderedDict

from PyQt5 import QtGui, QtCore, QtWidgets

from polyglotdb import CorpusContext

from .base import RadioSelectWidget

from .lexicon import StressToneSelectWidget, WordSelectWidget

from .inventory import PhoneSelectWidget, PhoneSubsetSelectWidget, RegexPhoneSelectWidget

class BaseDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(BaseDialog, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        aclayout = QtWidgets.QHBoxLayout()

        self.acceptButton = QtWidgets.QPushButton('Encode')
        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)

        aclayout.addWidget(self.acceptButton)
        aclayout.addWidget(self.cancelButton)

        layout.addLayout(aclayout)

        self.setLayout(layout)

    def validate(self):
        return True

    def accept(self):
        if self.validate():
            super(BaseDialog, self).accept()

class EncodePauseDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodePauseDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.wordSelect = WordSelectWidget(config)

        layout.addRow(self.wordSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode non-speech elements')

    def value(self):
        return self.wordSelect.value()

class EncodeUtteranceDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeUtteranceDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.minPauseEdit = QtWidgets.QLineEdit()
        self.minPauseEdit.setText('0')

        self.minUttEdit = QtWidgets.QLineEdit()
        self.minUttEdit.setText('0')

        layout.addRow('Minimum duration of pause between utterances (seconds)', self.minPauseEdit)
        layout.addRow('Minimum duration of utterances (seconds)', self.minUttEdit)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode utterances')

    def validate(self):
        try:
            val = self.value()
        except ValueError:
            reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information",
                    'Please make sure that the durations are properly specified.')
            return False
        if val[0] > 10 or val[1] > 10:
            reply = QtWidgets.QMessageBox.warning(self, "Long duration",
            'Are you sure that durations are specified in seconds?',
            buttons = QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return False
        return True


    def value(self):
        return float(self.minPauseEdit.text()), float(self.minUttEdit.text())

class EncodeSpeechRateDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeSpeechRateDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.subsetSelect = PhoneSubsetSelectWidget(config)

        layout.addRow('Select set of phones to count', self.subsetSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode speech rate')

    def value(self):
        return self.subsetSelect.value()

class EncodeUtterancePositionDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeUtterancePositionDialog, self).__init__(parent)

        self.setWindowTitle('Encode utterance positions')

class AnalyzeAcousticsDialog(BaseDialog):
    def __init__(self, config, parent):
        super(AnalyzeAcousticsDialog, self).__init__(parent)

        self.setWindowTitle('Analyze acoustics')

        layout = QtWidgets.QFormLayout()

        self.acousticsWidget = RadioSelectWidget('Acoustics to encode',
                                            OrderedDict([
                                            ('Pitch (REAPER)','pitch'),
                                            #('Formants (LPC)','formants'),
                                            ]))

        layout.addRow(self.acousticsWidget)

        self.layout().insertLayout(0, layout)

    def value(self):
        return self.acousticsWidget.value()

class EncodeSyllabicsDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeSyllabicsDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()

        self.phoneSelect = PhoneSelectWidget(config)
        for i in range(self.phoneSelect.selectWidget.count()):
            item = self.phoneSelect.selectWidget.item(i)
            for v in ['a','e','i','o','u']:
                if v in item.text().lower():
                    index = self.phoneSelect.selectWidget.model().index(i,0)
                    self.phoneSelect.selectWidget.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
                    break

        layout.addRow('Syllabic segments', self.phoneSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode syllabic segments')
    def value(self):
        return self.phoneSelect.value()

class EncodeSyllablesDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeSyllablesDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.algorithmWidget = RadioSelectWidget('Syllabification algorithm',
                                            OrderedDict([
                                            #('Probabilistic onsets and codas (language-independent)','probabilistic'),
                                            ('Max attested onset (language-independent)','maxonset'),]))

        layout.addRow(self.algorithmWidget)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode syllables')

    def value(self):
        return self.algorithmWidget.value()

class EncodePhoneSubsetDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodePhoneSubsetDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.labelEdit = QtWidgets.QLineEdit()

        layout.addRow('Class label', self.labelEdit)

        self.phoneSelect = PhoneSelectWidget(config)

        layout.addRow('Segments', self.phoneSelect)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode phone subsets')

    def value(self):
        return self.labelEdit.text(), self.phoneSelect.value()

class EnrichLexiconDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EnrichLexiconDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.caseCheck = QtWidgets.QCheckBox()

        layout.addRow('Case sensitive', self.caseCheck)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich lexicon')
        self.path = None

    def accept(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select lexicon", filter = "CSV (*.txt  *.csv)")
        if not self.path:
            return
        QtWidgets.QDialog.accept(self)

    def value(self):
        return self.path, self.caseCheck.isChecked()

class EnrichFeaturesDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EnrichFeaturesDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich phones with features')
        self.path = None

    def accept(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select feature file", filter = "CSV (*.txt  *.csv)")
        if not self.path:
            return
        QtWidgets.QDialog.accept(self)

    def value(self):
        return self.path

class AnnotationTypeSelect(QtWidgets.QComboBox):
    def __init__(self, hierarchy, subsets = False):
        super(AnnotationTypeSelect, self).__init__()
        self.hierarchy = hierarchy
        self.subsets = subsets
        self.baseAnnotation = None
        self.generateItems()

    def setBase(self, base):
        self.baseAnnotation = base
        self.generateItems()

    def generateItems(self):
        self.clear()
        if self.baseAnnotation is None:
            toiter = self.hierarchy.highest_to_lowest[:-1]
        else:
            toiter = self.hierarchy.get_lower_types(self.baseAnnotation)
        for at in toiter:
            self.addItem(at)
            if self.subsets:
                subs = []
                if at in self.hierarchy.subset_types:
                    subs += self.hierarchy.subset_types[at]
                if at in self.hierarchy.subset_tokens:
                    subs += self.hierarchy.subset_tokens[at]

                for s in sorted(subs):
                    self.addItem(' - '.join([at, s]))

class EncodeHierarchicalPropertiesDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeHierarchicalPropertiesDialog, self).__init__(parent)
        with CorpusContext(config) as c:
            hierarchy = c.hierarchy
        layout = QtWidgets.QFormLayout()

        self.higherSelect = AnnotationTypeSelect(hierarchy)
        self.higherSelect.currentIndexChanged.connect(self.updateBase)
        self.higherSelect.currentIndexChanged.connect(self.updateName)
        self.lowerSelect = AnnotationTypeSelect(hierarchy, subsets = True)
        self.lowerSelect.currentIndexChanged.connect(self.updateName)

        self.typeSelect = QtWidgets.QComboBox()
        self.typeSelect.addItem('count')
        self.typeSelect.addItem('rate')
        self.typeSelect.addItem('position')
        self.typeSelect.currentIndexChanged.connect(self.updateName)

        self.nameEdit = QtWidgets.QLineEdit()
        self.updateBase()
        self.updateName()

        layout.addRow('Higher annotation', self.higherSelect)
        layout.addRow('Lower annotation', self.lowerSelect)
        layout.addRow('Type of property', self.typeSelect)
        layout.addRow('Name of property', self.nameEdit)

        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich hierarchical annotations')

    def updateBase(self):
        self.lowerSelect.setBase(self.higherSelect.currentText())

    def updateName(self):
        lower, subset = self.splitLower()
        if subset is not None:
            lower = subset
        to_build = [self.typeSelect.currentText().title(), 'of', lower,
                    'in', self.higherSelect.currentText()]
        self.nameEdit.setText('_'.join(to_build))

    def validate(self):
        if self.nameEdit.text() == '':
            reply = QtWidgets.QMessageBox.critical(self,
                    "Missing information", 'Please make sure a name for the new property is specified.')
            return False
        ## FIXME add check for whether the name of the property already exists
        return True

    def splitLower(self):
        lower_text = self.lowerSelect.currentText()
        if ' - ' in lower_text:
            lower, subset = lower_text.split(' - ')
        else:
            lower = lower_text
            subset = None
        return lower, subset

    def value(self):
        lower, subset = self.splitLower()
        return {'higher': self.higherSelect.currentText(), 'type':self.typeSelect.currentText(),
                'lower': lower, 'subset': subset, 'name': self.nameEdit.text()}

class EncodeStressDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeStressDialog, self).__init__(parent)

        self.config = config
        layout = QtWidgets.QFormLayout()
        self.stressTone = RadioSelectWidget('Type of enrichment',OrderedDict([('Tone','tone'),('Stress','stress')]))
        self.stressToneSelectWidget = StressToneSelectWidget(config)

        self.stressToneSelectWidget.vowelRegexWidget.regexEdit.setText("^[a-z][a-z0-9][a-z0-9]?[a-z0-9]?")
        self.stressToneSelectWidget.regexWidget.regexEdit.setText("_T[0-9]$")
        self.stressToneSelectWidget.regexWidget.testButton.clicked.connect(self.testRegex)
        layout.addRow(self.stressTone)
        
        self.stressTone.optionChanged.connect(self.change_view)
        
        layout.addRow(self.stressToneSelectWidget)
        

        self.resetButton = QtWidgets.QPushButton()
        self.resetButton.setText('Reset')
        self.resetButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        self.resetButton.clicked.connect(self.reset)

        layout.addRow(self.resetButton)
        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Encode stress')
    
    def change_view(self, text):
        if text == 'stress':
            self.stressToneSelectWidget.vowelRegexWidget.regexEdit.setText("^[A-Z][A-Z]")
            self.stressToneSelectWidget.regexWidget.regexEdit.setText('[0-2]$')
        elif text == 'tone':
            self.stressToneSelectWidget.vowelRegexWidget.regexEdit.setText("^[a-z][a-z0-9][a-z0-9]?[a-z0-9]?")
            self.stressToneSelectWidget.regexWidget.regexEdit.setText("_T[0-9]$")

    def testRegex(self):
        if isinstance(self.layout().itemAt(0),QtWidgets.QHBoxLayout):
            self.layout().itemAt(0).setParent(None)
        newLayout = QtWidgets.QHBoxLayout()
        
        allphones = []
     
        with CorpusContext(self.config) as c:
        #   q = c.query_graph(c.phone).filter(c.phone.label.regex(self.stressToneSelectWidget.combo_value()))
            statement = "MATCH (n:phone_type:{corpus}) return n.label as label".format(corpus = c.corpus_name)


            results = c.execute_cypher(statement)
            #for c in results.cursors:
            for label in results:
                    #phone_label = item[0].properties['label']
                phone_label = label['label']
                r = re.search(self.stressToneSelectWidget.regexWidget.regexEdit.text(), phone_label)
                    #s = re.search(self.stressToneSelectWidget.vowelRegexWidget.regexEdit.text(), phone_label)
                if r is not None:
                    index = r.start(0)
                   
                    allphones.append((phone_label,index))        
            allphones =set(allphones)
            allphones=list(allphones)
            data = OrderedDict([
            ('stripped vowel', []),
            ('whole vowel', []),
            ('ending', [])])
            data.update({"whole vowel":[]})
            data.update({"stripped vowel":[]})
            data.update({"ending":[]})
            for tup in allphones:
                data['whole vowel'].append(tup[0])
                data['stripped vowel'].append(tup[0][:tup[1]])
                data['ending'].append(tup[0][tup[1]:])
            regexPhoneSelect = RegexPhoneSelectWidget(data, 3,len(allphones))

            newLayout.addWidget(regexPhoneSelect)
        self.layout().insertLayout(0, newLayout)
    def value(self):
        return (self.stressTone.value(), self.stressToneSelectWidget.value(), self.stressToneSelectWidget.combo_value())
   
    def reset(self):
        with CorpusContext(self.config) as c:
            c.reset_to_old_label()



class EncodeRelativizedMeasuresDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EncodeRelativizedMeasuresDialog, self).__init__(parent)
        
        layout = QtWidgets.QFormLayout()
       
        self.optionWidget = QtWidgets.QComboBox(self)
        self.optionWidget.addItem("Word")
        self.optionWidget.addItem("Phone")
        self.optionWidget.addItem("Speaker")
        with CorpusContext(config) as c:
            if c.hierarchy.has_type_subset(c.phone_name, 'syllabic'): 
                self.optionWidget.addItem("Syllable")

        self.optionWidget.currentTextChanged.connect(self.change_view)
        layout.addWidget(self.optionWidget)

        self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([
            ('Word Mean Duration', 'word_mean_duration'),
            ('Word Median Duration', 'word_median'),
            ('Word Standard Deviation','word_std_dev'),
            ('Baseline Duration', 'baseline_duration')]))
        layout.addWidget(self.radioWidget)

        self.layout().insertLayout(0, layout)

    def change_view(self, text):
        layout = QtWidgets.QFormLayout()
        self.radioWidget.setParent(None)

        if text == 'Word':
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([
            ('Word Mean Duration', 'word_mean_duration'),
            ('Word Median Duration', 'word_median'),
            ('Word Standard Deviation','word_std_dev'),
            ('Baseline Duration', 'baseline_duration')]))

        if text == 'Phone':
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([('Phone Mean Duration','phone_mean'),
            ('Phone Median Duration','phone_median'),
            ('Phone Standard Deviation', 'phone_std_dev')]))
        if text == "Syllable":
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([('Syllable Mean Duration', 'syllable_mean'),
            ('Syllable Median Duration', 'syllable_median'),
            ('Syllable Standard Deviation', 'syllable_std_dev')]))
        if text == "Speaker":
            self.radioWidget = RadioSelectWidget('Desired measure:', OrderedDict([('Mean Speech Rate', 'mean_speech_rate')]))
            
        self.optionWidget.setParent(None)
        layout.addWidget(self.optionWidget)
        layout.addWidget(self.radioWidget)
        self.layout().insertLayout(0, layout)




    def value(self):
        return self.radioWidget.value()

class EnrichSpeakersDialog(BaseDialog):
    def __init__(self, config, parent):
        super(EnrichSpeakersDialog, self).__init__(parent)

        layout = QtWidgets.QFormLayout()
        self.layout().insertLayout(0, layout)

        self.setWindowTitle('Enrich phones with features')
        self.path = None

    def accept(self):
        self.path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select feature file", filter = "CSV (*.txt  *.csv)")
        if not self.path:
            return
        QtWidgets.QDialog.accept(self)

    def value(self):
        return self.path   



























