class Detail():
    def __init__(self, msg: str, type : str, loc : list[str] = ["body"]):
        self.msg = msg
        self.type = type
        self.loc = loc

    def to_json(self):
        return {
            "msg" : self.msg,
            "type" : self.type,
            "loc" : self.loc
        }

class Ctx():
    def __init__(self, body : str):
        self.body = body

    def to_json(self):
        return {"body" : self.body}

class DtoExceptionObject():
    def __init__(self, details : list[Detail], ctx : Ctx):
        self.details = details,
        self.ctx = ctx
    def to_json(self):
        return {"errors" : [detail.to_json() for detail in self.details[0]],
                "ctx" : self.ctx.to_json()}

class DtoException(Exception):
    def __init__(self, dtoExceptionObject : DtoExceptionObject):
        self.dtoExceptionObject = dtoExceptionObject

    def __str__(self):
        return "{} {} {}".format(self.msg, self.type, str(self.loc))

    def to_json(self):
        return  self.dtoExceptionObject.to_json()

class BadRequestException(DtoException):
    pass

class AccessDeniedException(DtoException):
    pass

class PrimaryDatabaseException(Exception):
    """Exception for primary database failures that should stop the poller"""
    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)

class SecondaryDatabaseException(Exception):
    """Exception for secondary database failures that should be logged but not stop processing"""
    def __init__(self, database_key: str, message: str, original_exception: Exception = None):
        self.database_key = database_key
        self.message = message
        self.original_exception = original_exception
        super().__init__(f"Database {database_key}: {message}")
