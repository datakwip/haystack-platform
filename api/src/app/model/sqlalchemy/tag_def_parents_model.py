from sqlalchemy import Table
from app.model.sqlalchemy.base import Base
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from sqlalchemy_views import CreateView
from sqlalchemy import Column, \
    Integer,\
    String
from app.services import config_service


class TagDefParents(Base):
    __tablename__ = "tag_def_parents"
    __table_args__ = {'schema': config_service.dbSchema}

    tag_id = Column(Integer, primary_key=True)
    parent_ids = Column(String)


def create_views(engine):
        tag_def_parents = Table('tag_def_parents', Base.metadata, schema=config_service.dbSchema)
        definition = text("""WITH RECURSIVE hier_query
                  AS
                  (
                  select child_id real_child_id, child_id, parent_id
                  from {}.tag_hierarchy th
                  UNION ALL
                  select c.real_child_id, th2.child_id, th2.parent_id
                  from {}.tag_hierarchy th2
                  INNER JOIN hier_query c ON c.parent_id = th2.child_id
                  )
        select real_child_id tag_id, ',' 
                   || string_agg(td1.name, ',') 
                   || ',' as parent_ids
                   from hier_query, {}.tag_def td1
                   where td1.id = hier_query.parent_id
        group by real_child_id""".format(config_service.dbSchema, config_service.dbSchema, config_service.dbSchema))
        create_view = CreateView(tag_def_parents, definition, or_replace=True)
        engine.execute(create_view)

        i = 1

#def add_recursive_table_to_header(
#        db : Session,
#        path: ParserRuleContext,
#        number_of_tables: int
#    ):
#    hierarchy = db.query(
#            aggregate_model.TagHierarchy, literal("1").label('group_column')).join(source_object_model.TagDef,
#                                               aggregate_model.TagHierarchy.child_id == source_object_model.TagDef.id) \
#            .filter(source_object_model.TagDef.name == path.getText()) \
#            .filter(aggregate_model.TagHierarchy.disabled_ts == None) \
#            .cte(name="hier_query<table_number>".replace("<table_number>", str(number_of_tables)), recursive=True)

#    parent = aliased(hierarchy, name="p")
#    children = aliased(aggregate_model.TagHierarchy, name="c")
#    children = db.query(children, literal("1").label('group_column')).filter(children.disabled_ts == None).subquery()
#    hierarchy = hierarchy.union_all(
#            db.query(
#                children).join(source_object_model.TagDef, children.c.child_id == source_object_model.TagDef.id).join(
#                parent, parent.c.parent_id == children.c.child_id) \
#                .filter(children.c.child_id == parent.c.parent_id))
#    return  hierarchy