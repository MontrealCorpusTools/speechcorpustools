
from .base import BaseProfile

class Column(object):
    def __init__(self, attribute, name):
        self.attribute = attribute
        self.name = name

    def for_polyglot(self, corpus_context):
        att = corpus_context
        for a in self.attribute:
            if a.endswith('_name'):
                att = getattr(att, getattr(corpus_context, a))
            else:
                att = getattr(att, a)
        att = att.column_name(self.name)
        return att

class ExportProfile(BaseProfile):
    extension = '.exportprofile'
    def __init__(self):
        self.columns = []
        self.name = ''
        self.to_find = None

    def for_polyglot(self, corpus_context):
        columns = []
        for  x in self.columns:
            try:
                columns.append(x.for_polyglot(corpus_context))
            except AttributeError:
                pass
        return columns
