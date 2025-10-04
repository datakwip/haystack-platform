from antlr4 import ParserRuleContext
from app.api.filter.antlr.utils import \
    get_number_case_body, \
    get_str_case_body, \
    get_bool_case_body, \
    get_date_case_body, \
    get_val_type, \
    add_recursive_table_to_header

def is_path(ctx: ParserRuleContext):
    if not hasattr(ctx, "children"):
        return False
    return "->" in list(map(lambda child: child.getText(),
                            ctx.children))


def convert_path_to_sql(ctx: ParserRuleContext, number_of_tables: int, db_schema):
    number_of_tables += 1
    sql_header = ""
    sql_where = ""

    if is_not_rule(ctx):
        is_has_rule = len(ctx.children) == 2
        path_ctx = ctx.children[1]
    else:
        is_has_rule = len(ctx.children) == 1
        path_ctx = ctx.children[0]

    if is_has_rule:
        sql_where = """ (select entity_id
            from {}.entity_tag et<table_number>, {}.tag_def td<table_number>
            where  et<table_number>.tag_id = td<table_number>.id
            and td<table_number>.name = '<path>') """.format(db_schema, db_schema)\
            .replace(
            "<table_number>", str(number_of_tables))\
            .replace("<path>", path_ctx.children[len(path_ctx.children) - 1]
                     .getText())
    else:
        path = path_ctx.children[len(path_ctx.children) - 1]
        cmp_op = ctx.children[len(ctx.children) - 2]
        val = ctx.children[len(ctx.children) - 1]
        sql_header += add_recursive_table_to_header(path, number_of_tables, db_schema)
        sql_where += get_path_sql_where(path, cmp_op, val, number_of_tables, db_schema)
    for i in reversed(range(0, len(path_ctx.children) - 2, 2)):
        number_of_tables += 1
        if not is_has_rule:
            sql_header += add_recursive_table_to_header(
                path_ctx.children[i], number_of_tables, db_schema)
        sql_where = """ (select entity_id
            from {}.entity_tag et<table_number>, {}.tag_def td<table_number>
            where
                et<table_number> .tag_id  = td<table_number>.id
                and td<table_number>.name = '<path>'
                and et<table_number>.value_ref in <sql_where>
            ) """.format(db_schema, db_schema)\
                    .replace("<table_number>", str(number_of_tables))\
                    .replace("<path>", path_ctx.children[i].getText())\
                    .replace("<sql_where>", sql_where)
    sql_where = " e.id in ({})".format(sql_where)
    return (sql_header, sql_where, number_of_tables)


def get_path_sql_where(path, cmp_op, val, table_number, db_schema):
    cmp_op = cmp_op.getText() if cmp_op.getText() != '==' else '='
    sql_query_start = """ (select et<table_number>.entity_id
            from {}.entity_tag et<table_number>,
            (select ',' || string_agg(td<table_number>.name, ',')
                || ',' as parent_id  from hier_query<table_number>, {}.tag_def td<table_number>
                where td<table_number>.id = hier_query<table_number>.parent_id
            ) hq<table_number>, {}.tag_def td<table_number>
            where et<table_number>.tag_id = td<table_number>.id
            and td<table_number>.name = '<path>'
            AND CASE """.format(db_schema, db_schema, db_schema)\
        .replace("<path>", path.getText())\
        .replace("<table_number>", str(table_number))

    val_type = get_val_type(val)
    sql_query_case_body = \
        get_number_case_body(val_type, cmp_op, val, table_number) + \
        get_bool_case_body(val_type, cmp_op, val, table_number) + \
        get_str_case_body(val_type, cmp_op, val, table_number)\
        + get_date_case_body(val_type, cmp_op, val, table_number)
    sql_query_end = 'END  group by entity_id'
    return " {}{}{}) ".format(
        sql_query_start, sql_query_case_body, sql_query_end)


def is_not_rule(ctx: ParserRuleContext):
    return not is_path(ctx.children[0])
