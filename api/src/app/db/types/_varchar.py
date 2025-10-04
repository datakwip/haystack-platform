import sqlalchemy.types as types


class _Varchar(types.UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "_varchar"

    def bind_processor(self, dialect):
        def process(value: list):
            return "{" + ','.join(str(e) for e in value) + "}"
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process
