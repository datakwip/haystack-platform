from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging


class DatabaseGrafanaConnector():
    def __init__(self, databaseUrlGrafanaConnector: str, pool_size: int = 1, max_overflow: int = 0):
        self.__databaseUrl = databaseUrlGrafanaConnector
        self.__pool_size = pool_size
        self.__max_overflow = max_overflow

    def init_database(self):
        self.__engine = create_engine(
            self.__databaseUrl, 
            echo=False, 
            pool_size=self.__pool_size, 
            max_overflow=self.__max_overflow,
            pool_pre_ping=True,  # Validates connections before use
            pool_recycle=3600,   # Recycle connections every hour
        )
        self.__session = sessionmaker(
            autocommit=False, autoflush=False, bind=self.__engine)
        self.__base = declarative_base()

    def get_engine(self):
        return self.__engine

    def get_local_session(self):
        return self.__session()

    def get_base(self):
        return self.__base

    def log_connection_stats(self):
        """Log current connection pool statistics"""
        logger = logging.getLogger(__name__)
        pool = self.__engine.pool
        
        # Get pool statistics
        pool_size = pool.size()
        checked_in = pool.checkedin()
        checked_out = pool.checkedout()
        overflow = pool.overflow()
        # Note: invalid() method doesn't exist on QueuePool, removing it
        
        logger.info(f"Grafana DB Connection Pool Stats - "
                   f"Size: {pool_size}, "
                   f"Checked In: {checked_in}, "
                   f"Checked Out: {checked_out}, "
                   f"Overflow: {overflow}")
        
        return {
            'pool_size': pool_size,
            'checked_in': checked_in,
            'checked_out': checked_out,
            'overflow': overflow
        }
