import unittest

from app.db.database import Database


class AntlrTestBase(unittest.TestCase):
    def __init__(self):
        super().__init__()
        database = Database("postgresql://postgres:password@host.docker.internal/master")
        database.init_database()
        self.db = database.get_local_session()