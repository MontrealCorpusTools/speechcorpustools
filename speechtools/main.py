import os
import pickle

from PyQt5 import QtGui, QtCore, QtWidgets
import PyQt5
import vispy

from polyglotdb.config import BASE_DIR, CorpusConfig

from polyglotdb import CorpusContext

from polyglotdb.exceptions import ConnectionError

from .widgets import (ViewWidget, HelpWidget, DiscourseWidget, QueryWidget, CollapsibleWidgetPair,
                        DetailsWidget, ConnectWidget, AcousticDetailsWidget, DetailedMessageBox,
                        CollapsibleTabWidget)
from .widgets.help import ExportHelpWidget

from .widgets.enrich import (EncodePauseDialog, EncodeUtteranceDialog,
                            EncodeSpeechRateDialog, EncodeUtterancePositionDialog,
                            AnalyzeAcousticsDialog, EncodeSyllabicsDialog,
                            EncodePhoneSubsetDialog, EncodeSyllablesDialog,
                            EnrichLexiconDialog, EnrichFeaturesDialog,
                            EncodeHierarchicalPropertiesDialog)

from .helper import get_system_font_height

from .progress import ProgressWidget

from .workers import (AcousticAnalysisWorker, ImportCorpusWorker,
                    PauseEncodingWorker, UtteranceEncodingWorker,
                    SpeechRateWorker, UtterancePositionWorker,
                    SyllabicEncodingWorker, PhoneSubsetEncodingWorker,
                    SyllableEncodingWorker, LexiconEnrichmentWorker,
                    FeatureEnrichmentWorker, HierarchicalPropertiesWorker,
                    QueryWorker, ExportQueryWorker)

sct_config_pickle_path = os.path.join(BASE_DIR, 'config')

class Pane(QtWidgets.QWidget):
    def __init__(self):
        super(Pane, self).__init__()

    def growLower(self):
        self.splitter.setSizes([1, 1000000])
        self.splitter.widget(1).ensureVisible()

    def growUpper(self):
        self.splitter.setSizes([1000000, 1])
        self.splitter.widget(0).ensureVisible()

class LeftPane(Pane):
    def __init__(self):
        super(LeftPane, self).__init__()

        self.viewWidget = ViewWidget()
        self.queryWidget = QueryWidget()
        self.queryWidget.needsShrinking.connect(self.growLower)
        self.viewWidget.needsShrinking.connect(self.growUpper)
        self.queryWidget.viewRequested.connect(self.changeDiscourse)

        self.splitter = CollapsibleWidgetPair(QtCore.Qt.Vertical, self.queryWidget, self.viewWidget, collapsible = 0)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def updateConfig(self, config):
        self.viewWidget.updateConfig(config)
        self.queryWidget.updateConfig(config)

    def changeDiscourse(self, discourse, begin = None, end = None):
        self.viewWidget.changeDiscourse(discourse, begin, end)



class RightPane(Pane):
    configUpdated = QtCore.pyqtSignal(object)
    discourseChanged = QtCore.pyqtSignal(str)
    def __init__(self):
        super(RightPane, self).__init__()


        if os.path.exists(sct_config_pickle_path):
            with open(sct_config_pickle_path, 'rb') as f:
                config = pickle.load(f)
            if config.corpus_name:
                try:
                    with CorpusContext(config) as c:
                        c.hierarchy = c.generate_hierarchy()
                        c.save_variables()
                except ConnectionError:
                    config = None
        else:
            config = None
        self.connectWidget = ConnectWidget(config = config)
        self.connectWidget.configChanged.connect(self.configUpdated.emit)
        self.discourseWidget = DiscourseWidget()
        self.configUpdated.connect(self.discourseWidget.updateConfig)
        self.discourseWidget.discourseChanged.connect(self.discourseChanged.emit)
        self.helpWidget = HelpWidget()
        self.helpPopup = ExportHelpWidget()
        self.detailsWidget = DetailsWidget()
        self.acousticsWidget = AcousticDetailsWidget()
        upper = CollapsibleTabWidget()
        upper.needsShrinking.connect(self.growLower)

        upper.addTab(self.connectWidget,'Connection')
        upper.addTab(self.discourseWidget, 'Discourses')

        lower = CollapsibleTabWidget()
        lower.needsShrinking.connect(self.growUpper)

        lower.addTab(self.detailsWidget, 'Details')

        lower.addTab(self.acousticsWidget, 'Acoustics')

        lower.addTab(self.helpWidget, 'Help')

        self.splitter = CollapsibleWidgetPair(QtCore.Qt.Vertical, upper, lower)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

class MainWindow(QtWidgets.QMainWindow):
    enrichHelpBroadcast= QtCore.pyqtSignal()
    configUpdated = QtCore.pyqtSignal(object)
    def __init__(self, app):
        super(MainWindow, self).__init__()
        #vispy.sys_info(os.path.join(BASE_DIR, 'vispy.info'), overwrite = True)
        self.corpusConfig = None

        self.leftPane = LeftPane()
        self.configUpdated.connect(self.leftPane.updateConfig)
        self.leftPane.viewWidget.connectionIssues.connect(self.havingConnectionIssues)

        self.rightPane = RightPane()
        self.rightPane.configUpdated.connect(self.updateConfig)
        self.rightPane.discourseChanged.connect(self.leftPane.changeDiscourse)

        self.rightPane.connectWidget.corporaHelpBroadcast.connect(self.rightPane.helpWidget.getConnectionHelp)


        self.leftPane.viewWidget.discourseWidget.nextRequested.connect(self.leftPane.queryWidget.requestNext)
        self.leftPane.viewWidget.discourseWidget.previousRequested.connect(self.leftPane.queryWidget.requestPrevious)
        self.leftPane.viewWidget.discourseWidget.markedAsAnnotated.connect(self.leftPane.queryWidget.markAnnotated)
        self.leftPane.viewWidget.discourseWidget.selectionChanged.connect(self.rightPane.detailsWidget.showDetails)
        self.leftPane.viewWidget.discourseWidget.acousticsSelected.connect(self.rightPane.acousticsWidget.showDetails)
        self.mainWidget = CollapsibleWidgetPair(QtCore.Qt.Horizontal, self.leftPane,self.rightPane)
        self.leftPane.queryWidget.needsHelp.connect(self.rightPane.helpWidget.getHelpInfo)
        self.leftPane.queryWidget.exportHelpBroadcast.connect(self.rightPane.helpPopup.exportHelp)
        self.enrichHelpBroadcast.connect(self.rightPane.helpWidget.getEnrichHelp)
        self.leftPane.viewWidget.discourseWidget.discourseHelpBroadcast.connect(self.rightPane.helpWidget.getDiscourseHelp)
        self.leftPane.queryWidget.queryForm.queryToRun.connect(self.runQuery)
        self.leftPane.queryWidget.queryForm.queryToExport.connect(self.exportQuery)

        self.wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.mainWidget)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)

        self.status = QtWidgets.QLabel()
        self.statusBar().addWidget(self.status, stretch=1)
        self.connectionStatus = QtWidgets.QLabel()
        self.statusBar().addWidget(self.connectionStatus)
        self.setWindowTitle("Speech Corpus Tools")
        self.createActions()
        self.createMenus()

        self.updateStatus()

        if os.path.exists(sct_config_pickle_path):
            self.rightPane.connectWidget.connectToServer(ignore=True)


        self.queryWorker = QueryWorker()
        self.queryWorker.dataReady.connect(self.leftPane.queryWidget.updateResults)
        self.queryWorker.errorEncountered.connect(self.showError)
        self.queryWorker.errorEncountered.connect(self.leftPane.queryWidget.queryForm.finishQuery)
        self.queryWorker.dataReady.connect(self.leftPane.queryWidget.queryForm.finishQuery)
        self.queryWorker.finishedCancelling.connect(self.leftPane.queryWidget.queryForm.finishQuery)

        self.exportWorker = ExportQueryWorker()
        self.exportWorker.errorEncountered.connect(self.showError)
        self.exportWorker.errorEncountered.connect(self.leftPane.queryWidget.queryForm.finishExport)
        self.exportWorker.dataReady.connect(self.leftPane.queryWidget.queryForm.finishExport)
        self.exportWorker.finishedCancelling.connect(self.leftPane.queryWidget.queryForm.finishExport)

        self.acousticWorker = AcousticAnalysisWorker()
        self.acousticWorker.errorEncountered.connect(self.showError)

        self.importWorker = ImportCorpusWorker()
        self.importWorker.errorEncountered.connect(self.showError)
        self.importWorker.dataReady.connect(self.checkImport)

        self.syllabicsWorker = SyllabicEncodingWorker()
        self.syllabicsWorker.errorEncountered.connect(self.showError)
        self.syllabicsWorker.dataReady.connect(self.updateStatus)

        self.syllablesWorker = SyllableEncodingWorker()
        self.syllablesWorker.errorEncountered.connect(self.showError)
        self.syllablesWorker.dataReady.connect(self.updateStatus)

        self.pauseWorker = PauseEncodingWorker()
        self.pauseWorker.errorEncountered.connect(self.showError)
        self.pauseWorker.dataReady.connect(self.updateStatus)

        self.utteranceWorker = UtteranceEncodingWorker()
        self.utteranceWorker.errorEncountered.connect(self.showError)
        self.utteranceWorker.dataReady.connect(self.updateStatus)

        self.speechRateWorker = SpeechRateWorker()
        self.speechRateWorker.errorEncountered.connect(self.showError)
        self.speechRateWorker.dataReady.connect(self.updateStatus)

        self.utterancePositionWorker = UtterancePositionWorker()
        self.utterancePositionWorker.errorEncountered.connect(self.showError)
        self.utterancePositionWorker.dataReady.connect(self.updateStatus)

        self.phoneSubsetWorker = PhoneSubsetEncodingWorker()
        self.phoneSubsetWorker.errorEncountered.connect(self.showError)
        self.phoneSubsetWorker.dataReady.connect(self.updateStatus)

        self.enrichLexiconWorker = LexiconEnrichmentWorker()
        self.enrichLexiconWorker.errorEncountered.connect(self.showError)
        self.enrichLexiconWorker.dataReady.connect(self.updateStatus)

        self.enrichFeaturesWorker = FeatureEnrichmentWorker()
        self.enrichFeaturesWorker.errorEncountered.connect(self.showError)
        self.enrichFeaturesWorker.dataReady.connect(self.updateStatus)

        self.hierarchicalPropertiesWorker = HierarchicalPropertiesWorker()
        self.hierarchicalPropertiesWorker.errorEncountered.connect(self.showError)
        self.hierarchicalPropertiesWorker.dataReady.connect(self.updateStatus)

        self.rightPane.connectWidget.corporaList.cancelImporter.connect(self.importWorker.stop)
        self.rightPane.connectWidget.corporaList.corpusToImport.connect(self.importCorpus)
        self.progressWidget = ProgressWidget(self)

    def exportQuery(self, query_profile, export_profile, path):

        kwargs = {}
        kwargs['config'] = self.corpusConfig
        kwargs['profile'] = query_profile
        kwargs['export_profile'] = export_profile
        kwargs['path'] = path
        self.exportWorker.setParams(kwargs)
        self.progressWidget.createProgressBar('export', self.exportWorker)
        self.progressWidget.show()
        self.exportWorker.start()

    def runQuery(self, query_profile):
        kwargs = {}
        kwargs['config'] = self.corpusConfig
        kwargs['profile'] = query_profile

        self.queryWorker.setParams(kwargs)
        self.progressWidget.createProgressBar('query', self.queryWorker)
        self.progressWidget.show()
        self.queryWorker.start()

    def checkImport(self, could_not_parse):
        if could_not_parse:
            reply = DetailedMessageBox()
            reply.setWindowTitle('Errors during parsing')
            reply.setIcon(QtWidgets.QMessageBox.Warning)
            reply.setText("Some files could not be parsed, but those that could be parsed have been successfully loaded.")
            reply.setInformativeText("Please check the files below for issues.")
            reply.setDetailedText('\n'.join(could_not_parse))
            ret = reply.exec_()


    def showError(self, e):
        reply = DetailedMessageBox()
        reply.setDetailedText(str(e))
        ret = reply.exec_()

    def havingConnectionIssues(self):
        size = get_system_font_height()
        self.connectionStatus.setPixmap(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning).pixmap(size, size))
        self.connectionStatus.setToolTip('Having connection issues...')

    def updateConfig(self, config):
        self.corpusConfig = config
        self.updateStatus()

    def updateStatus(self):
        self.encodeHierarchicalPropertiesAct.setEnabled(False)
        self.enrichLexiconAct.setEnabled(False)
        self.enrichLexiconAct.setText("Enrich lexicon...")
        self.enrichFeaturesAct.setEnabled(False)
        self.enrichFeaturesAct.setText("Enrich phonological inventory...")
        self.syllabicsAct.setEnabled(False)
        self.syllabicsAct.setText("Encode syllabic segments...")
        self.syllablesAct.setEnabled(False)
        self.syllablesAct.setText("Encode syllables...")
        self.phoneSubsetAct.setEnabled(False)
        self.phoneSubsetAct.setText("Encode phone subsets (classes)...")
        self.pausesAct.setEnabled(False)
        self.pausesAct.setText("Encode non-speech elements...")
        self.utterancesAct.setEnabled(False)
        self.utterancesAct.setText("Encode utterances...")
        self.speechRateAct.setEnabled(False)
        self.speechRateAct.setText("Encode speech rate...")
        self.utterancePositionAct.setEnabled(False)
        self.utterancePositionAct.setText("Encode position in utterance...")
        if self.corpusConfig is None:
            self.status.setText('No connection')
            size = get_system_font_height()
            self.connectionStatus.setPixmap(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical).pixmap(size, size))
            self.connectionStatus.setToolTip('No connection')
        else:
            c_name = self.corpusConfig.corpus_name
            if not c_name:
                c_name = 'No corpus selected'
            else:
                with CorpusContext(self.corpusConfig) as c:
                    self.pausesAct.setEnabled(True)
                    self.encodeHierarchicalPropertiesAct.setEnabled(True)
                    self.enrichLexiconAct.setEnabled(True)
                    self.enrichFeaturesAct.setEnabled(True)
                    self.syllabicsAct.setEnabled(True)
                    self.phoneSubsetAct.setEnabled(True)
                    if c.hierarchy.has_type_subset(c.phone_name, 'syllabic'):
                        self.syllabicsAct.setText("Re-encode syllabic segments...")
                        self.syllablesAct.setEnabled(True)
                    if 'syllable' in c.hierarchy.annotation_types:
                        self.syllablesAct.setText("Re-encode syllables...")
                    if c.hierarchy.has_token_subset(c.word_name, 'pause'):
                        self.pausesAct.setText("Re-encode non-speech elements...")
                    if c.hierarchy.has_token_subset(c.word_name, 'pause') and self.corpusConfig.graph_host == 'localhost':
                        self.utterancesAct.setEnabled(True)
                    else:
                        self.utterancesAct.setEnabled(False)
                    if 'utterance' in c.hierarchy.annotation_types:
                        self.utterancesAct.setText("Re-encode utterances...")
                        self.speechRateAct.setEnabled(True)
                        self.utterancePositionAct.setEnabled(True)
                    else:
                        self.speechRateAct.setEnabled(False)
                        self.utterancePositionAct.setEnabled(False)

                    if c.hierarchy.has_token_property('utterance', 'speech_rate'):
                        self.speechRateAct.setText("Re-encode speech rate...")

                    if c.hierarchy.has_token_property(c.word_name, 'position_in_utterance'):
                        self.utterancePositionAct.setText("Re-encode position in utterance...")
            self.enrichHelpAct.setEnabled(True)
            self.enrichHelpAct.setText("Help")
            self.status.setText('Connected to {} ({})'.format(self.corpusConfig.graph_hostname, c_name))
            size = get_system_font_height()
            self.connectionStatus.setPixmap(QtWidgets.qApp.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton).pixmap(size, size))
            self.connectionStatus.setToolTip('Connected!')
        self.configUpdated.emit(self.corpusConfig)

    def closeEvent(self, event):
        #self.importWorker.stop()
        #self.syllabicsWorker.stop()
        #self.pauseWorker.stop()
        #self.utteranceWorker.stop()
        #self.speechRateWorker.stop()
        #self.utterancePositionWorker.stop()
        if self.corpusConfig is not None:
            with open(sct_config_pickle_path, 'wb') as f:
                pickle.dump(self.corpusConfig, f)
        super(MainWindow, self).closeEvent(event)

    def createActions(self):

        self.specifyAct = QtWidgets.QAction( "Add phonological features...",
                self,
                statusTip="Specify a corpus", triggered=self.specifyCorpus)

        self.exportAct = QtWidgets.QAction( "Export a  corpus...",
                self,
                statusTip="Export a corpus", triggered=self.exportCorpus)

        self.encodeHierarchicalPropertiesAct = QtWidgets.QAction( "Encode hierarchical properties...",
                self,
                statusTip="Encode properties for annotations based on the hierarchy (rate/count/position of lower annotations within higher annotations",
                triggered=self.encodeHierarchicalProperties)
        self.encodeHierarchicalPropertiesAct.setEnabled(False)

        self.enrichLexiconAct = QtWidgets.QAction( "Enrich lexicon...",
                self,
                statusTip="Enrich lexicon from a CSV file", triggered=self.enrichLexicon)
        self.enrichLexiconAct.setEnabled(False)

        self.enrichFeaturesAct = QtWidgets.QAction( "Enrich phonological inventory...",
                self,
                statusTip="Enrich inventory from a CSV file with features", triggered=self.enrichFeatures)
        self.enrichFeaturesAct.setEnabled(False)

        self.syllabicsAct = QtWidgets.QAction( "Encode syllabic segments...",
                self,
                statusTip="Encode syllabic segments", triggered=self.encodeSyllabics)
        self.syllabicsAct.setEnabled(False)

        self.syllablesAct = QtWidgets.QAction( "Encode syllables...",
                self,
                statusTip="Encode syllables", triggered=self.encodeSyllables)
        self.syllablesAct.setEnabled(False)

        self.phoneSubsetAct = QtWidgets.QAction( "Encode phone subsets (classes)...",
                self,
                statusTip="Create (natural and unnatural) classes of segments", triggered=self.encodePhoneSubset)
        self.phoneSubsetAct.setEnabled(False)

        self.pausesAct = QtWidgets.QAction( "Encode non-speech elements...",
                self,
                statusTip="Encode pauses based on word labels", triggered=self.encodePauses)
        self.pausesAct.setEnabled(False)

        self.utterancesAct = QtWidgets.QAction( "Encode utterances...",
                self,
                statusTip="Encode utterances for the current corpus using parameters for pause length", triggered=self.encodeUtterances)
        self.utterancesAct.setEnabled(False)

        self.speechRateAct = QtWidgets.QAction( "Encode speech rate...",
                self,
                statusTip="Calculate and save speech rate for utterances based on phone subsets", triggered=self.speechRate)
        self.speechRateAct.setEnabled(False)

        self.utterancePositionAct = QtWidgets.QAction( "Encode position in utterance...",
                self,
                statusTip="Calculate and save each word's position in its utterance", triggered=self.utterancePosition)
        self.utterancePositionAct.setEnabled(False)

        self.analyzeAcousticsAct = QtWidgets.QAction( "Analyze acoustics...",
                self,
                statusTip="Batch analysis of formants and pitch for the current corpus", triggered=self.analyzeAcoustics)

        self.enrichHelpAct = QtWidgets.QAction( "Help",
                self,
                statusTip="getHelp", triggered = self.getEnrichHelp) #, triggered=self.encodeUtterances
        self.enrichHelpAct.setEnabled(True)
    def createMenus(self):

        self.corpusMenu = self.menuBar().addMenu("Corpus")

        #self.corpusMenu.addAction(self.specifyAct)

        self.enhancementMenu = self.menuBar().addMenu("Enhance corpus")

        self.enhancementMenu.addAction(self.encodeHierarchicalPropertiesAct)
        self.enhancementMenu.addAction(self.enrichLexiconAct)
        self.enhancementMenu.addAction(self.enrichFeaturesAct)
        self.enhancementMenu.addAction(self.syllabicsAct)
        self.enhancementMenu.addAction(self.syllablesAct)
        self.enhancementMenu.addAction(self.phoneSubsetAct)
        self.enhancementMenu.addAction(self.pausesAct)
        self.enhancementMenu.addAction(self.utterancesAct)

        #self.enhancementMenu.addAction(self.speechRateAct)
        #self.enhancementMenu.addAction(self.utterancePositionAct)
        self.enhancementMenu.addAction(self.analyzeAcousticsAct)
        self.enhancementMenu.addAction(self.enrichHelpAct)

    def specifyCorpus(self):
        pass

    def exportCorpus(self):
        pass

    def enrichLexicon(self):
        dialog = EnrichLexiconDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            path, case_sensitive = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'path': path,
                        'case_sensitive': case_sensitive}
            self.enrichLexiconWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('lexicon', self.enrichLexiconWorker)
            self.progressWidget.show()
            self.enrichLexiconWorker.start()

    def enrichFeatures(self):
        dialog = EnrichFeaturesDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            path = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'path': path}
            self.enrichFeaturesWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('features', self.enrichFeaturesWorker)
            self.progressWidget.show()
            self.enrichFeaturesWorker.start()

    def encodeSyllabics(self):
        dialog = EncodeSyllabicsDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            segments = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'segments': segments}
            self.syllabicsWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('syllabics', self.syllabicsWorker)
            self.progressWidget.show()
            self.syllabicsWorker.start()

    def encodeSyllables(self):
        dialog = EncodeSyllablesDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            algorithm = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'algorithm': algorithm}
            self.syllablesWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('syllables', self.syllablesWorker)
            self.progressWidget.show()
            self.syllablesWorker.start()

    def encodePhoneSubset(self):
        dialog = EncodePhoneSubsetDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            label, segments = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'label': label,
                        'segments': segments}
            self.phoneSubsetWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('subset', self.phoneSubsetWorker)
            self.progressWidget.show()
            self.phoneSubsetWorker.start()

    def encodePauses(self):
        dialog = EncodePauseDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            words = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'pause_words': words}
            self.pauseWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('pauses', self.pauseWorker)
            self.progressWidget.show()
            self.pauseWorker.start()

    def encodeHierarchicalProperties(self):
        dialog = EncodeHierarchicalPropertiesDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            kwargs = dialog.value()
            kwargs.update({'config': self.corpusConfig})
            self.hierarchicalPropertiesWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('hierarchical', self.hierarchicalPropertiesWorker)
            self.progressWidget.show()
            self.hierarchicalPropertiesWorker.start()

    def encodeUtterances(self):
        dialog = EncodeUtteranceDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            min_pause, min_utt = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'min_pause_length': min_pause,
                        'min_utterance_length': min_utt}
            self.utteranceWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('utterances', self.utteranceWorker)
            self.progressWidget.show()
            self.utteranceWorker.start()

    def getEnrichHelp(self):
        self.enrichHelpBroadcast.emit()

    def speechRate(self):
        dialog = EncodeSpeechRateDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            subset = dialog.value()
            kwargs = {'config': self.corpusConfig,
                        'to_count': subset}
            self.speechRateWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('speech_rate', self.speechRateWorker)
            self.progressWidget.show()
            self.speechRateWorker.start()

    def utterancePosition(self):
        dialog = EncodeUtterancePositionDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            kwargs = {'config': self.corpusConfig}
            self.utterancePositionWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('utterance_position', self.utterancePositionWorker)
            self.progressWidget.show()
            self.utterancePositionWorker.start()

    def analyzeAcoustics(self):
        dialog = AnalyzeAcousticsDialog(self.corpusConfig, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            acoustics = dialog.value()
            kwargs = {'config': self.corpusConfig,
                    'acoustics': acoustics}
            self.acousticWorker.setParams(kwargs)
            self.progressWidget.createProgressBar('acoustic', self.acousticWorker)
            self.progressWidget.show()
            self.acousticWorker.start()

    def importCorpus(self, name, directory):
        kwargs = {'name': name,
                'directory': directory}
        self.importWorker.setParams(kwargs)
        self.progressWidget.createProgressBar('import', self.importWorker)
        self.progressWidget.show()
        self.importWorker.start()
        self.updateStatus()

    def createProgressBar(self, key, worker):
        self.progressWidget.createProgressBar(key, worker)
