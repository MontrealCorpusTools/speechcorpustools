
from polyglotdb.graph.query import GraphQuery as BaseQuery

from speechtools.graph.cypher import query_to_cypher

class GraphQuery(BaseQuery):
    def set_pause(self):
        self._set_token['pause'] = True
        self.corpus.graph.cypher.execute(self.cypher(), **self.cypher_params())
        self._set_token = {}

    def cypher(self):
        for c in self._criterion:
            try:
                if c.attribute.label == 'discourse':
                    for c2 in self._criterion:
                        c2.attribute.annotation.discourse_label = c.value
                    break
            except AttributeError:
                pass
        return query_to_cypher(self)
