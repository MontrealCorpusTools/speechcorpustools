
from polyglotdb.graph.cypher import *

def create_return_statement(query):
    kwargs = {'order_by': '', 'additional_columns':'', 'columns':''}
    return_statement = ''
    if query._delete:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        return_statement = delete_template.format(**kwargs)
        return return_statement
    set_strings = []
    set_label_strings = []
    remove_label_strings = []
    if 'pause' in query._set_token:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['type_alias'] = query.to_find.type_alias

        return_statement = set_pause_template.format(**kwargs)
        return return_statement
    for k,v in query._set_token.items():
        if v is None:
            v = 'NULL'
        else:
            v = value_for_cypher(v)
        set_strings.append(set_property_template.format(alias = query.to_find.alias, attribute = k, value = v))
    for k,v in query._set_type.items():
        if v is None:
            v = 'NULL'
        else:
            v = value_for_cypher(v)
        set_strings.append(set_property_template.format(alias = query.to_find.type_alias, attribute = k, value = v))
    if query._set_token_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._set_token_labels))
        set_label_strings.append(set_label_template.format(**kwargs))
    if query._set_type_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.type_alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._set_type_labels))
        set_label_strings.append(set_label_template.format(**kwargs))
    if set_label_strings or set_strings:
        return_statement = 'SET ' + ', '.join(set_label_strings + set_strings)
    if query._remove_type_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.type_alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._remove_type_labels))
        remove_label_strings.append(remove_label_template.format(**kwargs))
    if query._remove_token_labels:
        kwargs = {}
        kwargs['alias'] = query.to_find.type_alias
        kwargs['value'] = ':' + ':'.join(map(key_for_cypher, query._remove_token_labels))
        remove_label_strings.append(remove_label_template.format(**kwargs))
    if remove_label_strings:
        if return_statement:
            return_statement += '\nWITH {alias}, {type_alias}\n'.format(alias = query.to_find.alias, type_alias = query.to_find.type_alias)
        return_statement += '\nREMOVE ' + ', '.join(remove_label_strings)
    if return_statement:
        return return_statement

    if query._aggregate:
        template = aggregate_template
        properties = []
        for g in query._group_by:
            properties.append(g.aliased_for_output())
        if len(query._order_by) == 0 and len(query._group_by) > 0:
            query._order_by.append((query._group_by[0], False))
        for a in query._aggregate:
            properties.append(a.for_cypher())
        kwargs['aggregates'] = ', '.join(properties)
    else:
        template = distinct_template
        properties = []
        for c in query._columns:
            properties.append(c.aliased_for_output())
        if properties:
            kwargs['columns'] = ', '.join(properties)

    properties = []
    for c in query._order_by:
        ac_set = set(query._additional_columns)
        gb_set = set(query._group_by)
        h_c = hash(c[0])
        for col in ac_set:
            if h_c == hash(col):
                element = col.output_alias
                break
        else:
            for col in gb_set:
                if h_c == hash(col):
                    element = col.output_alias
                    break
            else:
                query._additional_columns.append(c[0])
                element = c[0].output_alias
        if c[1]:
            element += ' DESC'
        properties.append(element)

    if properties:
        kwargs['order_by'] += '\nORDER BY ' + ', '.join(properties)

    properties = []
    for c in query._additional_columns:
        if c in query._group_by:
            continue
        properties.append(c.aliased_for_output())
    if properties:
        string = ', '.join(properties)
        if kwargs['columns'] or ('aggregates' in kwargs and kwargs['aggregates']):
            string = ', ' + string
        kwargs['additional_columns'] += string
    return template.format(**kwargs)

def query_to_cypher(query):
    kwargs = {'match': '',
            'optional_match':'',
            'where': '',
            'with': '',
            'return':''}
    annotation_levels = query.annotation_levels()

    match_strings = []
    optional_match_strings = []
    optional_where_strings = []
    where_strings = []

    all_withs = set()

    filter_annotations = set()
    for c in query._criterion:
        for a in c.annotations:
            filter_annotations.add(a)

    for k,v in annotation_levels.items():
        if k.has_subquery:
            continue
        statements,optional_statements, withs, wheres, optional_wheres = generate_token_match(k,v, filter_annotations)
        all_withs.update(withs)
        match_strings.extend(statements)
        optional_match_strings.extend(optional_statements)
        optional_where_strings.extend(optional_wheres)
        where_strings.extend(wheres)

    statements = generate_hierarchical_match(annotation_levels, query.corpus.hierarchy)
    match_strings.extend(statements)

    kwargs['match'] = 'MATCH ' + ',\n'.join(match_strings)

    if optional_match_strings:
        kwargs['optional_match'] = 'OPTIONAL MATCH ' + ',\n'.join(optional_match_strings)
        if optional_where_strings:
            kwargs['optional_match'] += '\nWHERE ' + ',\n'.join(optional_where_strings)

    kwargs['where'] = criterion_to_where(query._criterion, wheres)

    kwargs['with'] = generate_withs(query, all_withs)


    kwargs['return'] = create_return_statement(query)
    cypher = template.format(**kwargs)
    return cypher
