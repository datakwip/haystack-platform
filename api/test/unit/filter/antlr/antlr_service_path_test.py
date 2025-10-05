import unittest
from app.api.filter.antlr.antlr_service import get_sql

org_id = 5
user_id = 2
db_schema="core_dev"

class AntlrServicePathTest(unittest.TestCase):
    def test_equality(self):
        expected_result = """WITH RECURSIVE hier_query1
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td1
          where th.child_id  = td1.id
          and td1.name = 'yearBuilt'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query1 c ON c.parent_id = th2.child_id
          )
          ,hier_query2
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td2
          where th.child_id  = td2.id
          and td2.name = 'siteRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query2 c ON c.parent_id = th2.child_id
          )
          ,hier_query3
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td3
          where th.child_id  = td3.id
          and td3.name = 'equipRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query3 c ON c.parent_id = th2.child_id
          )
          select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et3, core_dev.tag_def td3
            where
                et3 .tag_id  = td3.id
                and td3.name = 'equipRef'
                and et3.value_ref in  (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in   (select et1.entity_id
            from core_dev.entity_tag et1,
            (select ',' || string_agg(td1.name, ',')
                || ',' as parent_id  from hier_query1, core_dev.tag_def td1
                where td1.id = hier_query1.parent_id
            ) hq1, core_dev.tag_def td1
            where et1.tag_id = td1.id
            and td1.name = 'yearBuilt'
            AND CASE 
            WHEN hq1.parent_id like '%,number,%'
                THEN   et1.value_n = 1985
            WHEN hq1.parent_id like '%,ref,%'
                THEN   et1.value_ref = 1985
            END  group by entity_id) 
            ) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("equipRef->siteRef->yearBuilt==1985", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_inequality(self):
        expected_result = """WITH RECURSIVE hier_query1
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td1
          where th.child_id  = td1.id
          and td1.name = 'yearBuilt'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query1 c ON c.parent_id = th2.child_id
          )
          ,hier_query2
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td2
          where th.child_id  = td2.id
          and td2.name = 'siteRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query2 c ON c.parent_id = th2.child_id
          )
          ,hier_query3
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td3
          where th.child_id  = td3.id
          and td3.name = 'equipRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query3 c ON c.parent_id = th2.child_id
          )
          select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et3, core_dev.tag_def td3
            where
                et3 .tag_id  = td3.id
                and td3.name = 'equipRef'
                and et3.value_ref in  (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in   (select et1.entity_id
            from core_dev.entity_tag et1,
            (select ',' || string_agg(td1.name, ',')
                || ',' as parent_id  from hier_query1, core_dev.tag_def td1
                where td1.id = hier_query1.parent_id
            ) hq1, core_dev.tag_def td1
            where et1.tag_id = td1.id
            and td1.name = 'yearBuilt'
            AND CASE 
            WHEN hq1.parent_id like '%,number,%'
                THEN   et1.value_n != 1985
            WHEN hq1.parent_id like '%,ref,%'
                THEN   et1.value_ref != 1985
            END  group by entity_id) 
            ) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("equipRef->siteRef->yearBuilt!=1985", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_lt(self):
        expected_result = """WITH RECURSIVE hier_query1
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td1
          where th.child_id  = td1.id
          and td1.name = 'yearBuilt'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query1 c ON c.parent_id = th2.child_id
          )
          ,hier_query2
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td2
          where th.child_id  = td2.id
          and td2.name = 'siteRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query2 c ON c.parent_id = th2.child_id
          )
          select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in   (select et1.entity_id
            from core_dev.entity_tag et1,
            (select ',' || string_agg(td1.name, ',')
                || ',' as parent_id  from hier_query1, core_dev.tag_def td1
                where td1.id = hier_query1.parent_id
            ) hq1, core_dev.tag_def td1
            where et1.tag_id = td1.id
            and td1.name = 'yearBuilt'
            AND CASE 
            WHEN hq1.parent_id like '%,number,%'
                THEN   et1.value_n < 1985
            WHEN hq1.parent_id like '%,ref,%'
                THEN   et1.value_ref < 1985
            END  group by entity_id) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("siteRef->yearBuilt < 1985", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_gt(self):
        expected_result = """WITH RECURSIVE hier_query1
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td1
          where th.child_id  = td1.id
          and td1.name = 'yearBuilt'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query1 c ON c.parent_id = th2.child_id
          )
          ,hier_query2
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td2
          where th.child_id  = td2.id
          and td2.name = 'siteRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query2 c ON c.parent_id = th2.child_id
          )
          select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in   (select et1.entity_id
            from core_dev.entity_tag et1,
            (select ',' || string_agg(td1.name, ',')
                || ',' as parent_id  from hier_query1, core_dev.tag_def td1
                where td1.id = hier_query1.parent_id
            ) hq1, core_dev.tag_def td1
            where et1.tag_id = td1.id
            and td1.name = 'yearBuilt'
            AND CASE 
            WHEN hq1.parent_id like '%,number,%'
                THEN   et1.value_n > 1985
            WHEN hq1.parent_id like '%,ref,%'
                THEN   et1.value_ref > 1985
            END  group by entity_id) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("siteRef->yearBuilt > 1985", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_ge(self):
        expected_result = """WITH RECURSIVE hier_query1
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td1
          where th.child_id  = td1.id
          and td1.name = 'yearBuilt'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query1 c ON c.parent_id = th2.child_id
          )
          ,hier_query2
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td2
          where th.child_id  = td2.id
          and td2.name = 'siteRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query2 c ON c.parent_id = th2.child_id
          )
          select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in   (select et1.entity_id
            from core_dev.entity_tag et1,
            (select ',' || string_agg(td1.name, ',')
                || ',' as parent_id  from hier_query1, core_dev.tag_def td1
                where td1.id = hier_query1.parent_id
            ) hq1, core_dev.tag_def td1
            where et1.tag_id = td1.id
            and td1.name = 'yearBuilt'
            AND CASE 
            WHEN hq1.parent_id like '%,number,%'
                THEN   et1.value_n >= 1985
            WHEN hq1.parent_id like '%,ref,%'
                THEN   et1.value_ref >= 1985
            END  group by entity_id) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("siteRef->yearBuilt >= 1985", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_le(self):
        expected_result = """WITH RECURSIVE hier_query1
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td1
          where th.child_id  = td1.id
          and td1.name = 'yearBuilt'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query1 c ON c.parent_id = th2.child_id
          )
          ,hier_query2
          AS
          (
          select child_id, parent_id
          from core_dev.tag_hierarchy th, core_dev.tag_def td2
          where th.child_id  = td2.id
          and td2.name = 'siteRef'
          UNION ALL
          select th2.child_id, th2.parent_id
          from core_dev.tag_hierarchy th2
          INNER JOIN hier_query2 c ON c.parent_id = th2.child_id
          )
          select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in   (select et1.entity_id
            from core_dev.entity_tag et1,
            (select ',' || string_agg(td1.name, ',')
                || ',' as parent_id  from hier_query1, core_dev.tag_def td1
                where td1.id = hier_query1.parent_id
            ) hq1, core_dev.tag_def td1
            where et1.tag_id = td1.id
            and td1.name = 'yearBuilt'
            AND CASE 
            WHEN hq1.parent_id like '%,number,%'
                THEN   et1.value_n <= 1985
            WHEN hq1.parent_id like '%,ref,%'
                THEN   et1.value_ref <= 1985
            END  group by entity_id) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("siteRef->yearBuilt <= 1985", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_has_rule(self):
        expected_result = """select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  e.id in ( (select entity_id
            from core_dev.entity_tag et3, core_dev.tag_def td3
            where
                et3 .tag_id  = td3.id
                and td3.name = 'equipRef'
                and et3.value_ref in  (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in  (select entity_id
            from core_dev.entity_tag et1, core_dev.tag_def td1
            where  et1.tag_id = td1.id
            and td1.name = 'yearBuilt') 
            ) 
            ) ))) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("equipRef->siteRef->yearBuilt", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

    def test_not_rule(self):
        expected_result = """select root.id entity_id from (select a.id from (select e.id, et.tag_id
            from core_dev."entity" e,
                 core_dev.entity_tag et  where  e.id = et.entity_id AND (  NOT  e.id in ( (select entity_id
            from core_dev.entity_tag et2, core_dev.tag_def td2
            where
                et2 .tag_id  = td2.id
                and td2.name = 'siteRef'
                and et2.value_ref in  (select entity_id
            from core_dev.entity_tag et1, core_dev.tag_def td1
            where  et1.tag_id = td1.id
            and td1.name = 'yearBuilt') 
            ) ) )) a, core_dev.tag_def td, core_dev.tag_meta tm where  td.name = 'lib' and  td.id = tm.attribute and tm.tag_id = a.tag_id  and ((exists (select 1 from core_dev.org_entity_permission oep where  oep.org_id = 5 and oep.entity_id = a.id) or exists (select 1 from core_dev.user_entity_add_permission ueap where   ueap.user_id = 2 and ueap.entity_id = a.id) and not exists (select 1 from core_dev.user_entity_rev_permission uerp where   uerp.user_id = 2 and uerp.entity_id = a.id)) and ((exists (select 1 from core_dev.org_tag_permission otp where  otp.org_id = 5 and otp.tag_id = tm.value)  or exists (select 1 from core_dev.user_tag_add_permission utap where   utap.user_id = 2 and utap.tag_id = tm.value)) and  not exists (select 1 from  core_dev.user_tag_rev_permission utrp where   utrp.user_id = 2 and utrp.tag_id = tm.value)))) root group by root.id"""
        result = get_sql("not siteRef->yearBuilt", org_id, user_id, db_schema)
        self.assertEqual(expected_result, result)

if __name__ == '__main__':
    unittest.main()
