
from .base import BaseProfile

class Column(object):
    def __init__(self, attribute, name):
        self.attribute = attribute
        self.name = name

    def for_polyglot(self, corpus_context, to_find):
        att = corpus_context
        if 'speaker' in self.attribute:
            ind = self.attribute.index('speaker')
            att = getattr(corpus_context, to_find)
            for a in self.attribute[ind:]:
                att = getattr(att, a)
        elif 'discourse' in self.attribute:
            ind = self.attribute.index('discourse')
            att = getattr(corpus_context, to_find)
            for a in self.attribute[ind:]:
                att = getattr(att, a)
        else:
            if self.attribute[0] != to_find:
                att = getattr(corpus_context, to_find)
            for a in self.attribute:
                if a.endswith('_name'):
                    att = getattr(att, getattr(corpus_context, a))
                else:
                    att = getattr(att, a)
        att = att.column_name(self.name)
        return att

    def __repr__(self):
        return '<Column {}, {}>'.format(self.attribute, self.name)

class ExportProfile(BaseProfile):
    extension = '.exportprofile'
    def __init__(self):
        self.columns = []
        self.name = ''
        self.to_find = None

    def for_polyglot(self, corpus_context, to_find = None):
        columns = []
        if to_find is None:
            to_find = self.to_find
        for  x in self.columns:
            try:
                columns.append(x.for_polyglot(corpus_context, to_find))
            except AttributeError:
                pass
        return columns
