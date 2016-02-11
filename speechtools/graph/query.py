
from py2neo.cypher import RecordList

from polyglotdb.graph.query import GraphQuery as BaseQuery

from speechtools.graph.cypher import query_to_cypher

class GraphQuery(BaseQuery):
    _parameters = ['_criterion','_columns','_order_by','_aggregate',
                    '_preload', '_set_type_labels', '_set_token_labels',
                    '_remove_type_labels', '_remove_token_labels',
                    '_set_type', '_set_token', '_delete', '_limit',
                    '_cache']
    def set_pause(self):
        self._set_token['pause'] = True
        self.corpus.execute_cypher(self.cypher(), **self.cypher_params())
        self._set_token = {}

    def cypher(self):
        return query_to_cypher(self)


class SplitQuery(GraphQuery):
    splitter = ''

    def base_query(self):
        q = GraphQuery(self.corpus, self.to_find)
        for p in q._parameters:
            setattr(q, p, getattr(self, p))
        return q

    def split_queries(self):
        attribute_name = self.splitter[:-1] #remove 's', fixme maybe?
        splitter_attribute = getattr(getattr(self.to_find, attribute_name), 'name')
        for x in getattr(self.corpus, self.splitter):
            base = self.base_query()
            base = base.filter(splitter_attribute == x)
            yield base

    def set_pause(self):
        for q in self.split_queries():
            q.set_pause()

    def all(self):
        results = []
        columns = None
        for q in self.split_queries():
            r = q.all()
            results.extend(r.records)
            if columns is None:
                columns = r.columns
        return RecordList(columns, results)


    def delete(self):
        for q in self.split_queries():
            q.delete()

    def cache(self, *args):
        for q in self.split_queries():
            q.cache(*args)

    def set_type(self, *args, **kwargs):
        for q in self.split_queries():
            q.set_type(*args, **kwargs)

    def set_token(self, *args, **kwargs):
        for q in self.split_queries():
            q.set_token(*args, **kwargs)

    def to_csv(self, path):
        results = []
        columns = None
        for q in self.split_queries():
            r = self.corpus.execute_cypher(q.cypher(), **q.cypher_params())
            results.extend(r.records)
            if columns is None:
                columns = r.columns
        data = RecordList(columns, results)
        save_results(data, path)

class SpeakerGraphQuery(GraphQuery):
    splitter = 'speakers'

class DiscourseGraphQuery(GraphQuery):
    splitter = 'discourses'
