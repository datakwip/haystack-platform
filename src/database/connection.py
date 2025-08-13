"""Database connection module for TimescaleDB."""

import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import SimpleConnectionPool
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages TimescaleDB connection and operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database connection with configuration.
        
        Args:
            config: Database configuration dictionary with keys:
                - host: Database host
                - port: Database port
                - database: Database name
                - user: Database user
                - password: Database password
        """
        self.config = config
        self.pool: Optional[SimpleConnectionPool] = None
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = SimpleConnectionPool(
                1, 20,  # Min and max connections
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
            
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
                
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries with query results
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
                
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount
                
    def execute_batch_insert(self, query: str, data: List[tuple], page_size: int = 1000):
        """Execute batch insert operation.
        
        Args:
            query: SQL query string with placeholders
            data: List of tuples with data to insert
            page_size: Number of records per batch
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_batch(cur, query, data, page_size=page_size)
                logger.info(f"Batch inserted {len(data)} records")
                
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, schema: str = 'core'):
        """Insert pandas DataFrame into database table.
        
        Args:
            df: DataFrame to insert
            table_name: Target table name
            schema: Database schema name
        """
        with self.get_connection() as conn:
            df.to_sql(
                table_name, 
                conn, 
                schema=schema,
                if_exists='append', 
                index=False,
                method='multi'
            )
            logger.info(f"Inserted {len(df)} records into {schema}.{table_name}")
            
    def setup_hypertables(self):
        """Set up TimescaleDB hypertables for time-series data."""
        queries = [
            "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",
            "SELECT create_hypertable('core.values_demo', 'ts', if_not_exists => TRUE);",
            "SELECT create_hypertable('core.values_demo_current', 'ts', if_not_exists => TRUE);"
        ]
        
        for query in queries:
            try:
                self.execute_update(query)
                logger.info(f"Executed: {query}")
            except Exception as e:
                logger.warning(f"Query failed (may already exist): {e}")
                
    def create_organization(self, org_name: str, org_key: str) -> int:
        """Create organization in database.
        
        Args:
            org_name: Organization name
            org_key: Organization key
            
        Returns:
            Organization ID
        """
        # Check if organization exists
        query = "SELECT id FROM core.org WHERE name = %s"
        result = self.execute_query(query, (org_name,))
        
        if result:
            return result[0]['id']
            
        # Create new organization
        query = """
            INSERT INTO core.org (name, key, value_table, schema_name) 
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (org_name, org_key, f'values_{org_key}', org_key))
                org_id = cur.fetchone()[0]
                logger.info(f"Created organization '{org_name}' with ID {org_id}")
                return org_id
                
    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")