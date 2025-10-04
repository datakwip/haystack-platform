
from app.api.filter.antlr.dqqlVisitor import DqqlVisitor

def get_sql(filter_str: str, tags: list, org_id: int, user_id: int, db_schema: str):
    visitor = DqqlVisitor(db_schema, tags)
    sqlSelect = visitor.build_full_sql_clause(filter_str)
    dynamic_columns = visitor.build_dynamic_columns("root")

    sqlSelect = add_security_to_sql(
        sqlSelect, org_id, user_id, db_schema, visitor.build_dynamic_columns("a"))

    sql = (f"{visitor.sqlHeader} SELECT root.id AS entity_id {dynamic_columns} ,root.value_table "
           f"FROM ({sqlSelect}) root GROUP BY root.id {dynamic_columns} ,value_table")

    return sql


def add_security_to_sql(sql: str, org_id: int, user_id: int, db_schema: str, dynamic_columns: str):
    return "select a.id " + dynamic_columns + " ,org_root.value_table value_table from (" + sql + ") a, {}.org org_root, {}.org_entity_permission oep_root, {}.tag_def td, {}.tag_meta tm where ".format(db_schema, db_schema, db_schema, db_schema) +\
        " td.name = 'lib' and org_root.id = oep_root.org_id and oep_root.entity_id = a.id and td.id = tm.attribute and tm.tag_id = a.tag_id " + \
        " and ((exists (select 1 from {}.org_entity_permission oep where ".format(db_schema) + \
        " oep.org_id = " + str(org_id) + " and oep.entity_id = a.id)" +\
        " or exists (select 1 from {}.user_entity_add_permission ueap where  ".format(db_schema) + \
        " ueap.user_id = " + str(user_id) + " and ueap.entity_id = a.id)" + \
        " and not exists (select 1 from {}.user_entity_rev_permission uerp where  ".format(db_schema) + \
        " uerp.user_id = " + str(user_id) + " and uerp.entity_id = a.id))" + \
           " and ((exists (select 1 from {}.org_tag_permission otp where ".format(db_schema) + \
           " otp.org_id = " + str(org_id) + " and otp.tag_id = tm.value) " + \
           " or exists (select 1 from {}.user_tag_add_permission utap where  ".format(db_schema) + \
           " utap.user_id = " + str(user_id) + " and utap.tag_id = tm.value)) and " + \
           " not exists (select 1 from  {}.user_tag_rev_permission utrp where  ".format(db_schema) + \
           " utrp.user_id = " + str(user_id) + " and utrp.tag_id = tm.value)))"
