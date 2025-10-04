import sqlalchemy.types as types
import json


class Jsonb(types.UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "jsonb"

    def bind_processor(self, dialect):
        def process(value):
            return json.dumps(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return json.dumps(value)
        return process
