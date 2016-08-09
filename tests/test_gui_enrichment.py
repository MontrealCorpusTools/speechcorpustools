import pytest
from PyQt5 import QtCore, QtWidgets
from speechtools.main import MainWindow
from speechtools.widgets.enrich import EncodeStressDialog, EncodeSyllabicsDialog, EncodeSyllablesDialog
from speechtools.widgets.base import RadioSelectWidget
from speechtools.widgets.query.basic import ValueWidget
from speechtools.widgets.query.main import QueryWidget, QueryForm, QueryResults
from polyglotdb import CorpusContext
import collections

def test_enrich_speakers(stressed_config, qtbot):
	#config = stressed_config
	syllabics= "AA0,AA1,AA2,AH0,AH1,AH2,AE0,AE1,AE2,AY0,AY1,AY2,ER0,ER1,ER2,EH0,EH1,EH2,EY1,EY2,IH0,IH1,IH2,IY0,IY1,IY2,UW0,UW1,UW2".split(",")
	with CorpusContext(stressed_config) as c:

		c.encode_syllabic_segments(syllabics)
		c.encode_syllables("maxonset")
		c.reset_to_old_label()
		dict1 = c.encode_stress('[0-2]')
		c.remove_pattern()
		c.enrich_syllables(dict1)
		
	query = ValueWidget(stressed_config, 'syllable')
	qtbot.addWidget(query)
	query.changeType('syllable','stress', str)
	

	#assert(2<1)
	#w1.exec_()
	

#	w2.exec_()
#	w.exec_()

	assert(len(query.levels)>0)