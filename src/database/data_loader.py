"""Data loader for inserting time-series data into TimescaleDB."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataLoader:
    """Manages time-series data insertion into TimescaleDB."""
    
    def __init__(self, db_connection, table_name: str = "values_demo"):
        """Initialize data loader.
        
        Args:
            db_connection: DatabaseConnection instance
            table_name: Target table name for time-series data
        """
        self.db = db_connection
        self.table_name = table_name
        self.current_table_name = f"{table_name}_current"
        
    def insert_time_series_batch(self, data_points: List[Dict[str, Any]]):
        """Insert batch of time-series data points.
        
        Args:
            data_points: List of dictionaries with keys:
                - entity_id: Entity ID
                - ts: Timestamp
                - value_n: Numeric value (optional)
                - value_b: Boolean value (optional)
                - value_s: String value (optional)
                - status: Status string (optional)
        """
        if not data_points:
            return
            
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data_points)
        
        # Ensure required columns exist
        required_cols = ['entity_id', 'ts']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        # Add optional columns with defaults
        optional_cols = {
            'value_n': None,
            'value_b': None,
            'value_s': None,
            'value_ts': None,
            'value_dict': None,
            'status': 'ok'
        }
        
        for col, default in optional_cols.items():
            if col not in df.columns:
                df[col] = default
                
        # Convert to tuples for batch insert
        columns = ['entity_id', 'ts', 'value_n', 'value_b', 'value_s', 
                  'value_ts', 'value_dict', 'status']
        data_tuples = [tuple(row[col] for col in columns) for _, row in df.iterrows()]
        
        # Prepare query
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"""
            INSERT INTO core.{self.table_name} 
            ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (entity_id, ts) DO UPDATE
            SET value_n = EXCLUDED.value_n,
                value_b = EXCLUDED.value_b,
                value_s = EXCLUDED.value_s,
                value_ts = EXCLUDED.value_ts,
                value_dict = EXCLUDED.value_dict,
                status = EXCLUDED.status
        """
        
        # Execute batch insert
        self.db.execute_batch_insert(query, data_tuples)
        logger.info(f"Inserted {len(data_points)} time-series data points")
        
    def update_current_values(self, current_values: List[Dict[str, Any]]):
        """Update current values table with latest readings.
        
        Args:
            current_values: List of current value dictionaries
        """
        if not current_values:
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(current_values)
        
        # Ensure required columns
        required_cols = ['entity_id', 'ts']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        # Add optional columns
        optional_cols = {
            'value_n': None,
            'value_b': None,
            'value_s': None,
            'value_ts': None,
            'value_dict': None,
            'status': 'ok'
        }
        
        for col, default in optional_cols.items():
            if col not in df.columns:
                df[col] = default
                
        # Convert to tuples
        columns = ['entity_id', 'ts', 'value_n', 'value_b', 'value_s',
                  'value_ts', 'value_dict', 'status']
        data_tuples = [tuple(row[col] for col in columns) for _, row in df.iterrows()]
        
        # Prepare upsert query
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"""
            INSERT INTO core.{self.current_table_name}
            ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (entity_id) DO UPDATE
            SET ts = EXCLUDED.ts,
                value_n = EXCLUDED.value_n,
                value_b = EXCLUDED.value_b,
                value_s = EXCLUDED.value_s,
                value_ts = EXCLUDED.value_ts,
                value_dict = EXCLUDED.value_dict,
                status = EXCLUDED.status
        """
        
        # Execute batch insert
        self.db.execute_batch_insert(query, data_tuples)
        logger.info(f"Updated {len(current_values)} current values")
        
    def insert_dataframe(self, df: pd.DataFrame, chunk_size: int = 10000):
        """Insert pandas DataFrame as time-series data.
        
        Args:
            df: DataFrame with time-series data
            chunk_size: Number of rows per batch
        """
        # Validate required columns
        required_cols = ['entity_id', 'ts']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        # Process in chunks
        total_rows = len(df)
        chunks_processed = 0
        
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx]
            
            # Convert chunk to list of dictionaries
            data_points = chunk.to_dict('records')
            
            # Insert batch
            self.insert_time_series_batch(data_points)
            
            chunks_processed += 1
            progress = (end_idx / total_rows) * 100
            logger.info(f"Progress: {progress:.1f}% ({end_idx}/{total_rows} rows)")
            
    def get_latest_timestamp(self, entity_id: int) -> Optional[datetime]:
        """Get the latest timestamp for an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Latest timestamp or None if no data exists
        """
        query = f"""
            SELECT MAX(ts) as max_ts
            FROM core.{self.table_name}
            WHERE entity_id = %s
        """
        result = self.db.execute_query(query, (entity_id,))
        
        if result and result[0]['max_ts']:
            return result[0]['max_ts']
        return None
        
    def delete_old_data(self, days_to_keep: int = 30):
        """Delete data older than specified days.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        query = f"""
            DELETE FROM core.{self.table_name}
            WHERE ts < NOW() - INTERVAL '%s days'
        """
        rows_deleted = self.db.execute_update(query, (days_to_keep,))
        logger.info(f"Deleted {rows_deleted} old records")
        
    def get_row_count(self) -> int:
        """Get total number of rows in time-series table.
        
        Returns:
            Row count
        """
        query = f"SELECT COUNT(*) as count FROM core.{self.table_name}"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0