from antlr4 import ParserRuleContext
from app.api.filter.antlr.utils import \
    get_number_case_body, \
    get_str_case_body, \
    get_bool_case_body, \
    get_date_case_body, \
    get_val_type, \
    add_recursive_table_to_header, get_in_str_case_body


def convert_name_to_sql(name: ParserRuleContext, cmp_op: ParserRuleContext,
                        val: ParserRuleContext, number_of_tables: int, db_schema):
    number_of_tables += 1
    sql_header = add_recursive_table_to_header(name, number_of_tables, db_schema)
    sql_select = get_name_sql_select(number_of_tables, db_schema)
    sql_where = get_name_sql_where(name, cmp_op, val, number_of_tables, db_schema)
    return (sql_header, sql_select, sql_where, number_of_tables)


def get_name_sql_where(name: ParserRuleContext, cmp_op: ParserRuleContext,
                       val: ParserRuleContext, number_of_tables: int, db_schema : str):
    cmp_op = cmp_op.getText() if cmp_op.getText() != '==' else '='
    sql_query_start = """ EXISTS(
            select 1
            from  {}.entity_tag et<table_number>, {}.tag_def td<table_number>
            where et<table_number>.entity_id = e.id
                  and et<table_number>.tag_id = td<table_number>.id
                  and td<table_number>.name = '<path>'
                  AND CASE""".format(db_schema, db_schema)\
        .replace("<path>", name.getText())\
        .replace("<table_number>", str(number_of_tables))

    if cmp_op.lower() == 'in':
        sql_query_case_body = get_in_str_case_body(cmp_op, val, number_of_tables)
    else:
        val_type = get_val_type(val)
        sql_query_case_body = \
            get_number_case_body(val_type, cmp_op, val, number_of_tables) + \
            get_bool_case_body(val_type, cmp_op, val, number_of_tables) + \
            get_str_case_body(val_type, cmp_op, val, number_of_tables) + \
            get_date_case_body(val_type, cmp_op, val, number_of_tables)

    sql_query_end = 'END'
    return " {}{}{}) ".format(
        sql_query_start, sql_query_case_body, sql_query_end)


def get_name_sql_select(number_of_tables, db_schema):
    return """,
           (select ',' 
           || string_agg(td<table_number>.name, ',') 
           || ',' as parent_id  
           from hier_query<table_number>, {}.tag_def td<table_number>
           where td<table_number>.id = hier_query<table_number>.parent_id) hq<table_number>
           """.format(db_schema)\
        .replace("<table_number>", str(number_of_tables))
