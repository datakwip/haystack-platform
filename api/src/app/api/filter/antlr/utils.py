from antlr4 import ParserRuleContext

def get_val_type(val: ParserRuleContext):
    if len(val.children) == 0:
        raise Exception("ctx does not have children")

    typeList = {
        val.children[0].parentCtx.parser.NUMBER: 'number',
        val.children[0].parentCtx.parser.REF: 'ref',
        val.children[0].parentCtx.parser.STR: 'str',
        val.children[0].parentCtx.parser.BOOL: 'bool',
        val.children[0].parentCtx.parser.URI: 'uri',
        val.children[0].parentCtx.parser.DATE: 'date',
        val.children[0].parentCtx.parser.TIME: 'time'
    }
    return typeList[val.children[0].symbol.type]


def get_number_case_body(val_type: str, cmp_op: str,
                         val: ParserRuleContext, number_of_tables: int):
    if val_type in ['number', 'ref']:
        return """
            WHEN hq<table_number>.parent_id like '%,number,%'
                THEN   et<table_number>.value_n <cmp_op> <val>
            WHEN hq<table_number>.parent_id like '%,ref,%'
                THEN   et<table_number>.value_ref <cmp_op> <val>
            """\
            .replace("<val>", val.getText())\
            .replace("<cmp_op>", cmp_op)\
            .replace("<table_number>", str(number_of_tables))
    return ''


def get_bool_case_body(val_type: str, cmp_op: str,
                       val: ParserRuleContext, number_of_tables: int):
    if val_type in ['bool']:
        return """
        WHEN hq<table_number>.parent_id like '%,bool,%'
            THEN   et<table_number>.value_b <cmp_op> <val>
        """\
            .replace("<val>", val.getText())\
            .replace("<cmp_op>", cmp_op)\
            .replace("<table_number>", str(number_of_tables))
    return ''


def get_str_case_body(val_type: str, cmp_op: str,
                      val: ParserRuleContext, number_of_tables: int):
    if val_type in ['str', 'uri']:
        value = val.getText()[1:-1]
        return """
        WHEN hq<table_number>.parent_id like '%,str,%'
            THEN   et<table_number>.value_s <cmp_op> '<val>'
        """\
            .replace("<val>", value)\
            .replace("<cmp_op>", cmp_op)\
            .replace("<table_number>", str(number_of_tables))
    return ''

def get_in_str_case_body(cmp_op: str,
                      val: ParserRuleContext, number_of_tables: int):
        value = val.getText()
        return """
        WHEN hq<table_number>.parent_id like '%,str,%'
            THEN   et<table_number>.value_s <cmp_op> <val>
        """\
            .replace("<val>", value)\
            .replace("<cmp_op>", cmp_op)\
            .replace("<table_number>", str(number_of_tables))


def get_date_case_body(val_type: str, cmp_op: str,
                       val: ParserRuleContext, number_of_tables: int):
    if val_type in ['date', 'time']:
        return """
        WHEN hq<table_number>.parent_id like '%,date,%'
            or hq<table_number>.parent_id like '%,dateTime,%'
            THEN et<table_number>.value_ts <cmp_op> '<val>'
        """\
            .replace("<val>", val.getText())\
            .replace("<cmp_op>", cmp_op)\
            .replace("<table_number>", str(number_of_tables))
    return ''


def add_recursive_table_to_header(
        path: ParserRuleContext, number_of_tables: int, db_schema : str):
    if number_of_tables == 1:
        sql = """WITH RECURSIVE hier_query<table_number>
          AS
          (
          select child_id, parent_id
          from {}.tag_hierarchy th, {}.tag_def td<table_number>
          where th.child_id  = td<table_number>.id
          and td<table_number>.name = '<path>'
          UNION ALL
          select th2.child_id, th2.parent_id
          from {}.tag_hierarchy th2
          INNER JOIN hier_query<table_number> c ON c.parent_id = th2.child_id
          )
          """.format(db_schema, db_schema, db_schema)
    else:
        sql = """,hier_query<table_number>
          AS
          (
          select child_id, parent_id
          from {}.tag_hierarchy th, {}.tag_def td<table_number>
          where th.child_id  = td<table_number>.id
          and td<table_number>.name = '<path>'
          UNION ALL
          select th2.child_id, th2.parent_id
          from {}.tag_hierarchy th2
          INNER JOIN hier_query<table_number> c ON c.parent_id = th2.child_id
          )
          """.format(db_schema,db_schema,db_schema)

    return sql.replace("<table_number>", str(number_of_tables))\
        .replace("<path>", path.getText())
