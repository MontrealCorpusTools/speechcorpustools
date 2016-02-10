
from polyglotdb.graph.query import GraphQuery as BaseQuery

from speechtools.graph.cypher import query_to_cypher

class GraphQuery(BaseQuery):
    def set_pause(self):
        self._set_token['pause'] = True
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._set_token = {}

    def cypher(self):
        return query_to_cypher(self)
