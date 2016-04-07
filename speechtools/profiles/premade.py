
from .query import QueryProfile, Filter

from .export import ExportProfile, Column

class Lab1QueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Lab 1 stops'
        self.to_find = 'phone_name'
        self.filters = [Filter(('phone_name','begin'), '==', ('phone_name', 'word_name', 'begin')),
                        Filter(('phone_name','word_name','begin'), '==', ('phone_name', 'word_name', 'utterance', 'begin')),
                        Filter(('phone_name','following','type_subset'),'==','syllabic'),
                        Filter(('phone_name','type_subset'), '==', 'stop')]

class Lab2QueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Lab 2 stops'
        self.to_find = 'phone_name'
        self.filters = [Filter(('phone_name', 'begin'), '!=', ('phone_name','word_name','begin')),
                        Filter(('phone_name','end'), '!=', ('phone_name','word_name','end'),),
                        Filter(('phone_name','words','end'), '!=', ('phone_name','word_name','utterance','end'),),
                        Filter(('phone_name','type_subset'), '==', 'stop'),
                        Filter(('phone_name','following','type_subset'), '==', 'syllabic'),
                        Filter(('phone_name','previous','type_subset'), '==', 'syllabic'),
                        Filter(('phone_name','word_name','num_syllables'), 'in', [2, 3]),
                        ]

class Lab3QueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Lab 3 stops'
        self.to_find = 'phone_name'
        self.filters = [Filter(('phone_name','begin'), '!=', ('phone_name','word_name','begin')),
                        Filter(('phone_name','type_subset'), '==', 'stop'),
                        Filter(('phone_name', 'end'), '==', ('phone_name','word_name','end')),
                        Filter(('phone_name', 'following','label'), '==', 'sil'),
                        Filter(('phone_name','following','duration'), '>=', 0.05),
                        Filter(('phone_name','previous','type_subset'), '==', 'syllabic'),
                        ]

class WordFinalTappingQueryProfile(QueryProfile):
    def __init__(self):
        self.name = 'Word final tapping'
        self.to_find = 'word_name'
        self.filters = [Filter(('word_name','transcription'), 'regex', r'.*\.[td]$')
                        ]

class WordFinalTappingExportProfile(ExportProfile):
    def __init__(self):
        self.name = 'Word final tapping'
        self.to_find = 'word'
        self.columns = [Column(('word_name','label'),'orthography'),
                Column(('word_name','following','label'),'following_orthography'),
                Column(('word_name','transcription'),'underlying_transcription'),
                Column(('word_name','following','transcription'),'following_underlying_transcription'),
                Column(('pause','following','duration'),'following_pause_duration'),
                Column(('pause','following','label'),'following_pause'),
                Column(('word_name','phone_name','count'),'number_of_surface_phones'),
                Column(('word_name','phone_name','label'),'surface_transcription'),
                Column(('word_name','phone_name','penultimate','label'),'penult_segment'),
                Column(('word_name','phone_name','penultimate','duration'),'penult_segment_duration'),
                Column(('word_name','phone_name','final','label'),'final_segment'),
                Column(('word_name','phone_name','final','duration'),'final_segment_duration'),
                Column(('word_name','following','phone_name','label'),'following_surface_transcription'),
                Column(('word_name','following','phone_name','initial','label'),'following_initial_segment'),
                Column(('word_name','following','phone_name','initial','duration'),'following_initial_segment_duration'),
                Column(('word_name','duration'),'word_duration'),
                Column(('word_name','following','duration'),'following_word_duration'),
                Column(('word_name','utterance','speech_rate'),'utterance_speech_rate'),
                Column(('word_name','discourse','name'), 'discourse'),
                Column(('word_name','speaker','name'), 'speaker')]
