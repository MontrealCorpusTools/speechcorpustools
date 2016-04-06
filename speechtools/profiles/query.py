

from .base import BaseProfile

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
            if a == '':
                continue
            att = getattr(att, a)

        if isinstance(self.value, tuple):
            value = corpus_context
            for a in self.value:
                if a == '':
                    continue
                value = getattr(value, a)
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
        elif self.operator == 'regex':
            return att.regex(value)

class QueryProfile(BaseProfile):
    extension = '.queryprofile'
    def __init__(self):
        self.filters = []
        self.name = ''
        self.to_find = None

    def for_polyglot(self, corpus_context):
        return [x.for_polyglot(corpus_context) for x in self.filters]
