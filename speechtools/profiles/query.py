import pickle
import os

from polyglotdb.config import BASE_DIR

PROFILE_DIR = os.path.join(BASE_DIR, 'profiles')

class Filter(object):
    def __init__(self, attribute, operator, value):
        self.attribute = attribute
        self.operator = operator
        self.value = value

    @property
    def is_alignment(self):
        if self.attribute[-1] not in ['begin','end']:
            return False
        if not isinstance(self.value, tuple):
            return False
        if self.attribute[-1] != self.value[-1]:
            return False
        if self.operator not in ['==', '!=']:
            return False
        return True

    def for_polyglot(self, corpus_context):
        att = corpus_context
        for a in self.attribute:
            att = getattr(att, a)

        if isinstance(self.value, tuple):
            value = corpus_context
            for a in self.value:
                att = getattr(att, a)
        else:
            value = self.value

        if self.operator == '==':
            return att == value
        elif self.operator == '!=':
            return att != value
        elif self.operator == '>':
            return att > value
        elif self.operator == '>=':
            return att >= value
        elif self.operator == '<':
            return att < value
        elif self.operator == '<=':
            return att <= value
        elif self.operator == 'in':
            return att.in_(value)
        elif self.operator == 'not in':
            return att.not_in_(value)

class QueryProfile(object):
    extension = '.queryprofile'
    def __init__(self):
        self.filters = []
        self.name = ''
        self.to_find = None

    @property
    def path(self):
        return os.path.join(PROFILE_DIR, self.name.replace(' ', '_') + self.extension)

    @classmethod
    def load_profile(cls, name):
        path = os.path.join(PROFILE_DIR, name.replace(' ', '_') + cls.extension)
        with open(path, 'rb') as f:
            obj = pickle.load(f)
        return obj

    def for_polyglot(self):
        return [x.for_polyglot() for x in self.filters]

    def save_profile(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self, f)
