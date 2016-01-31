import csv
import os
from uuid import uuid1
import py2neo

def time_data_to_csvs(type, directory, discourse, timed_data):
    with open(os.path.join(directory, '{}_{}.csv'.format(discourse, type)), 'w') as f:
        for t in timed_data:
            f.write('{},{},{}\n'.format(t[0], t[1], uuid1()))

def import_utterance_csv(corpus_context, discourse, transaction = None):
    csv_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_utterance.csv'.format(discourse)).replace('\\','/'))

    word = getattr(corpus_context, 'word') #FIXME make word more general
    word_type = word.type
    statement = '''LOAD CSV FROM "{path}" AS csvLine
            MATCH (begin:{word_type}:{corpus}:{discourse} {{begin: toFloat(csvLine[0])}}),
            (end:{word_type}:{corpus}:{discourse} {{end: toFloat(csvLine[1])}}),
            (d:Discourse:{corpus} {{name: '{discourse}'}})
            CREATE (d)<-[:spoken_in]-(utt:utterance:{corpus}:{discourse}:speech {{id: csvLine[2], begin: toFloat(csvLine[0]), end: toFloat(csvLine[1])}})-[:is_a]->(u_type:utterance_type)
            WITH utt, begin, end
            MATCH path = shortestPath((begin)-[:precedes*0..]->(end))
            WITH utt, begin, end, nodes(path) as words
            UNWIND words as w
            MERGE (w)-[:contained_by]->(utt)'''
    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                    discourse = discourse,
                    word_type = word_type)
    if transaction is None:
        corpus_context.execute_cypher(statement)
    else:
        transaction.append(statement)

def subannoations_data_to_csv(corpus_context, type, data):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))
    header = sorted(data[0].keys())
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, header, delimiter = ',')
        writer.writeheader()
        for d in data:
            writer.writerow(d)

def import_subannotation_csv(corpus_context, type, annotated_type, props, transaction = None):
    path = os.path.join(corpus_context.config.temporary_directory('csv'),
                        '{}_subannotations.csv'.format(type))
    csv_path = 'file:///{}'.format(path.replace('\\','/'))
    prop_temp = '''{name}: csvLine.{name}'''
    properties = []
    try:
        corpus_context.execute_cypher('CREATE CONSTRAINT ON (node:%s) ASSERT node.id IS UNIQUE' % type)
    except py2neo.cypher.error.schema.ConstraintAlreadyExists:
        pass

    for p in props:
        if p in ['id', 'annotated_id', 'checked', 'begin', 'end']:
            continue
        corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (type, p))
        properties.append(prop_temp.format(name = p))
    if properties:
        properties = ', ' + ', '.join(properties)
    statement = '''USING PERIODIC COMMIT 500
    LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            MATCH (annotated:{a_type}:{corpus} {{id: csvLine.annotated_id}})
            CREATE (annotated) <-[:annotates]-(annotation:{type}:{corpus}
                {{id: csvLine.id, begin: toFloat(csvLine.begin),
                end: toFloat(csvLine.end), checked: false{properties}}})
            '''
    statement = statement.format(path = csv_path,
                corpus = corpus_context.corpus_name,
                    a_type = annotated_type,
                    type = type,
                    properties = properties)
    if transaction is None:
        corpus_context.execute_cypher(statement)
    else:
        transaction.append(statement)


