
from .query import QueryProfile, Filter

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
