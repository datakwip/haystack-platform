from antlr4 import CommonTokenStream, InputStream
from app.api.filter.antlr.antlr_error_listener import AntlrErrorListener
from app.api.filter.antlr.dist.dqql_grammarLexer import dqql_grammarLexer
from app.api.filter.antlr.dist.dqql_grammarParser import dqql_grammarParser
from app.api.filter.antlr.dist.dqql_grammarVisitor import dqql_grammarVisitor
from app.api.filter.antlr.name_service import convert_name_to_sql
from app.api.filter.antlr.path_service import convert_path_to_sql, is_path
from app.model.sqlalchemy.source_object_model import EntityTag

TAG_COLUMN_MAPPING = EntityTag.get_all_column_names()
class DqqlVisitor(dqql_grammarVisitor):
    def __init__(self, db_schema, tags):
        self.tags = tags
        self.db_schema = db_schema
        self.sqlHeader = ""
        self.sqlSelect = """select e.id
            from {}."entity" e,
                 {}.entity_tag et """.format(self.db_schema,self.db_schema)
        self.sqlWhere = "e.id = et.entity_id AND ("
        self.sql_header_tables = 0

    def build_dynamic_columns(self, alias):
        return ", " + ", ".join(f"{alias}.{tag}" for tag in TAG_COLUMN_MAPPING)

    def visitLogicalConditionOr(
            self, ctx: dqql_grammarParser.LogicalConditionOrContext):
        if len(ctx.children) > 1:
            for child in ctx.children:
                if child.getText().upper() == 'OR':
                    self.sqlWhere += " OR "
                else:
                    self.visit(child)
        else:
            self.visitChildren(ctx.children[0])

    def visitLogicalConditionAnd(
            self, ctx: dqql_grammarParser.LogicalConditionAndContext):
        if len(ctx.children) > 1:
            for child in ctx.children:
                if child.getText().upper() == 'AND':
                    self.sqlWhere += " AND "
                else:
                    self.visit(child)
        else:
            self.visit(ctx.children[0])

    def visitLogicalParens(self, ctx: dqql_grammarParser.LogicalParensContext):
        for child in ctx.children:
            if child.getText() == "(":
                self.sqlWhere += " ( "
            elif child.getText() == ")":
                self.sqlWhere += " ) "
            else:
                self.visit(child)

    def visitLogicalHas(self, ctx: dqql_grammarParser.LogicalHasContext):
        if is_path(ctx.children[0]):
            self.convert_path_to_sql(ctx)
        else:
            self.convert_name_without_cmp(ctx)

    def visitLogicalMissing(
            self,
            ctx: dqql_grammarParser.LogicalMissingContext):
        self.sqlWhere += " NOT "
        if is_path(ctx.children[1]):
            self.convert_path_to_sql(ctx)
        else:
            self.convert_name_without_cmp(ctx)
        self.sqlWhere += " "

    def visitLogicalCmp(self, ctx: dqql_grammarParser.LogicalCmpContext):
        if is_path(ctx.children[0]):
            self.convert_path_to_sql(ctx)
        else:
            self.getLogicalCmp(ctx)

    def visitInCmp(self, ctx: dqql_grammarParser.InCmpContext):
        if is_path(ctx.children[0]):
            self.convert_path_to_sql(ctx)
        else:
            self.getLogicalCmp(ctx)

    def visitCmpOp(self, ctx: dqql_grammarParser.CmpOpContext):
        self.visitChildren(ctx)

    def visitTerminal(self, node):
        if node.getText() != '<EOF>':
            self.sqlWhere += " {} ".format(node.getText())

    def getLogicalCmp(self, ctx):
        if len(ctx.children) == 3:
            self.convert_name_to_sql(
                ctx.children[0],
                ctx.children[1],
                ctx.children[2])

    def convert_name_to_sql(self, path, cmpOp, val):
        header, select, where, number_of_tables = convert_name_to_sql(
            path, cmpOp, val, self.sql_header_tables, self.db_schema)
        self.sqlHeader += header
        self.sqlSelect += select
        self.sqlWhere += where
        self.sql_header_tables = number_of_tables

    def convert_name_without_cmp(self, ctx):
        self.sql_header_tables += 1
        self.sqlWhere += """ e.id in
        (select entity_id
            from {}.entity_tag et<table_number>, {}.tag_def td<table_number>
            where et<table_number>.tag_id = td<table_number>.id and td<table_number>.name = '<path>')
        """.format(self.db_schema,self.db_schema).replace("<path>", ctx.getText())\
           .replace("<table_number>", str(self.sql_header_tables))

    def convert_path_to_sql(self, ctx):
        header, where, number_of_tables = convert_path_to_sql(
            ctx, self.sql_header_tables, self.db_schema)
        self.sqlHeader += header
        self.sqlWhere += where
        self.sql_header_tables = number_of_tables
    
    def build_full_sql_clause(self, filter_str):

        def build_subquery():
            sub_query = ""
            if self.tags and '*' not in self.tags:
                sub_query += "AND td.name IN ({})".format(", ".join(["'{}'".format(tag) for tag in self.tags]))
            elif not self.tags:
                sub_query = "ORDER BY et.entity_id, et.tag_id"
            return sub_query
        
        data = InputStream(filter_str)
        lexer = dqql_grammarLexer(data)
        stream = CommonTokenStream(lexer)
        parser = dqql_grammarParser(stream)
        parser.addErrorListener(AntlrErrorListener())
        tree = parser.expr()
        self.visit(tree)
        sqlQuery = self.sqlSelect + ' where ' + self.sqlWhere + ')'
        dynamic_columns = self.build_dynamic_columns("et")
        sub_query = build_subquery()

        distinct_query = "distinct on (et.entity_id)" if not self.tags else ""
        sqlSelect = """select {} et.entity_id as id {} from {}.entity_tag et join {}.tag_def td ON et.tag_id = td.id where et.entity_id in (
        {}) {}""".format(distinct_query, dynamic_columns, self.db_schema, self.db_schema, sqlQuery, sub_query) 
            
        return sqlSelect
