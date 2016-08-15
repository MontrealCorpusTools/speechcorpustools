import pytest
from PyQt5 import QtCore, QtWidgets
from speechtools.widgets.query.basic import ValueWidget
from polyglotdb import CorpusContext
import collections

def test_enrich_stress(stressed_config, qtbot):
	#config = stressed_config
	syllabics= "AA0,AA1,AA2,AH0,AH1,AH2,AE0,AE1,AE2,AY0,AY1,AY2,ER0,ER1,ER2,EH0,EH1,EH2,EY1,EY2,IH0,IH1,IH2,IY0,IY1,IY2,UW0,UW1,UW2".split(",")
	with CorpusContext(stressed_config) as c:

		c.encode_syllabic_segments(syllabics)
		c.encode_syllables("maxonset")
		c.reset_to_old_label()
		c.encode_stresstone_to_syllables('stress','[0-2]$')
		
	query = ValueWidget(stressed_config, 'syllable')
	qtbot.addWidget(query)
	query.changeType('syllable','stress', str)
	

	assert(len(query.levels)>0)

def test_enrich_relativized(acoustic_config, qtbot):

	with CorpusContext(acoustic_config) as c:
		c.encode_measure("word_median")

	query =ValueWidget(acoustic_config, 'word')
	qtbot.addWidget(query)
	query.changeType('word','median_duration',float)

	assert(isinstance(query.valueWidget,QtWidgets.QLineEdit))