
from .query import QueryProfile, Filter

from .export import ExportProfile, Column

class Lab1QueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Lab 1 stops'
        self.to_find = 'phones'
        self.filters = [Filter(('phones','begin'), '==', ('phones', 'words', 'begin')),
                        Filter(('phones','words','begin'), '==', ('phones', 'words', 'utterance', 'begin')),
                        Filter(('phones','following','type_subset'),'==','syllabic'),
                        Filter(('phones','type_subset'), '==', 'stop')]

class Lab2QueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Lab 2 stops'
        self.to_find = 'phones'
        self.filters = [Filter(('phones', 'begin'), '!=', ('phones','words','begin')),
                        Filter(('phones','end'), '!=', ('phones','words','end'),),
                        Filter(('phones','words','end'), '!=', ('phones','words','utterance','end'),),
                        Filter(('phones','type_subset'), '==', 'stop'),
                        Filter(('phones','following','type_subset'), '==', 'syllabic'),
                        Filter(('phones','previous','type_subset'), '==', 'syllabic'),
                        Filter(('phones','words','num_syllables'), 'in', [2, 3]),
                        ]

class Lab3QueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Lab 3 stops'
        self.to_find = 'phones'
        self.filters = [Filter(('phones','begin'), '!=', ('phones','words','begin')),
                        Filter(('phones','type_subset'), '==', 'stop'),
                        Filter(('phones', 'end'), '==', ('phones','words','end')),
                        Filter(('phones', 'following','label'), '==', 'sil'),
                        Filter(('phones','following','duration'), '>=', 0.05),
                        Filter(('phones','previous','type_subset'), '==', 'syllabic'),
                        ]

class WordFinalTappingQueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Word final tapping'
        self.to_find = 'word'
        self.filters = [Filter(('word','transcription'), 'regex', r'.*\.[td]$')
                        ]

class WordFinalTappingExportProfile(ExportProfile):
    def __init__(self):
        self.name = 'Word final tapping'
        self.to_find = 'word'
        self.columns = [Column(('word','label'),'orthography'),
                Column(('word','following','label'),'following_orthography'),
                Column(('word','transcription'),'underlying_transcription'),
                Column(('word','following','transcription'),'following_underlying_transcription'),
                Column(('pause','following','duration'),'following_pause_duration'),
                Column(('pause','following','label'),'following_pause'),
                Column(('word','phone','count'),'number_of_surface_phones'),
                Column(('word','phone','label'),'surface_transcription'),
                Column(('word','phone','penultimate','label'),'penult_segment'),
                Column(('word','phone','penultimate','duration'),'penult_segment_duration'),
                Column(('word','phone','final','label'),'final_segment'),
                Column(('word','phone','final','duration'),'final_segment_duration'),
                Column(('word','following','phone','label'),'following_surface_transcription'),
                Column(('word','following','phone','initial','label'),'following_initial_segment'),
                Column(('word','following','phone','initial','duration'),'following_initial_segment_duration'),
                Column(('word','duration'),'word_duration'),
                Column(('word','following','duration'),'following_word_duration'),
                Column(('word','utterance','speech_rate'),'utterance_speech_rate'),
                Column(('word','discourse','name'), 'discourse'),
                Column(('word','speaker','name'), 'speaker')]
