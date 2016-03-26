
class Column(object):
    def __init__(self, attribute, name):
        self.attribute = attribute
        self.name = name

    def for_polyglot(self, corpus_context):
        att = corpus_context
        for a in self.attribute:
            att = getattr(att, a)
        att = att.column_name(self.name)
        return att

class ExportProfile(object):
    def __init__(self):
        self.columns = []

    def for_polyglot(self):
        return [x.for_polyglot() for x in self.columns]
