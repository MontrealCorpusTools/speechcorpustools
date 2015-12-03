import csv
import os

def time_data_to_csvs(type, directory, discourse, timed_data):
    with open(os.path.join(directory, '{}_{}.csv'.format(discourse, type)), 'w') as f:
        for t in timed_data:
            f.write('{},{}\n'.format(t[0], t[1]))

def import_utterance_csv(corpus_context, discourse):
    csv_path = 'file:///{}'.format(os.path.join(corpus_context.config.temporary_directory('csv'), '{}_utterance.csv'.format(discourse)).replace('\\','/'))
    statement = '''USING PERIODIC COMMIT 1000
            LOAD CSV FROM "{path}" AS csvLine
            MATCH (begin:word:{corpus}:{discourse} {{begin: toFloat(csvLine[0])}}),
            (end:word:{corpus}:{discourse} {{end: toFloat(csvLine[1])}})
            MERGE (utt:utterance:{corpus}:{discourse}:speech {{begin: toFloat(csvLine[0]), end: toFloat(csvLine[1]), discourse: '{discourse}'}})-[:is_a]->(u_type:utterance_type)
            WITH utt, begin, end
            MATCH path = shortestPath((begin)-[:precedes*0..]->(end))
            WITH utt, begin, end, nodes(path) as words
            UNWIND words as w
            MERGE (w)-[:contained_by]->(utt)'''
    statement = statement.format(path = csv_path, corpus = corpus_context.corpus_name, discourse = discourse)
    corpus_context.graph.cypher.execute(statement)
