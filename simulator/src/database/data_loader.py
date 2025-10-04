"""Data loader for inserting time-series data into TimescaleDB."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
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
                
        # Clean up data types and handle NaN values
        df = self._clean_dataframe_types(df)
                
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
                
        # Clean up data types and handle NaN values
        df = self._clean_dataframe_types(df)
                
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
        
    def _clean_dataframe_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert DataFrame data types for database insertion.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Handle boolean column - convert NaN to None
        if 'value_b' in df.columns:
            df['value_b'] = df['value_b'].where(pd.notna(df['value_b']), None)
            # Ensure boolean values are proper Python bool or None
            df['value_b'] = df['value_b'].apply(lambda x: bool(x) if x is not None and not pd.isna(x) else None)
        
        # Handle numeric column - convert NaN to None  
        if 'value_n' in df.columns:
            df['value_n'] = df['value_n'].where(pd.notna(df['value_n']), None)
            # Ensure numeric values are proper Python float or None
            df['value_n'] = df['value_n'].apply(lambda x: float(x) if x is not None and not pd.isna(x) else None)
            
        # Handle string column - convert NaN to None
        if 'value_s' in df.columns:
            df['value_s'] = df['value_s'].where(pd.notna(df['value_s']), None)
            
        # Handle timestamp column - convert NaN to None
        if 'value_ts' in df.columns:
            df['value_ts'] = df['value_ts'].where(pd.notna(df['value_ts']), None)
            
        # Handle dict column - convert NaN to None
        if 'value_dict' in df.columns:
            df['value_dict'] = df['value_dict'].where(pd.notna(df['value_dict']), None)
            
        # Ensure status is always a string
        if 'status' in df.columns:
            df['status'] = df['status'].fillna('ok').astype(str)
            
        return df
        
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

    def get_last_timestamp_all_points(self) -> Optional[datetime]:
        """Get the latest timestamp across all points.

        Returns:
            Latest timestamp or None if no data exists
        """
        query = f"""
            SELECT MAX(ts) as max_ts
            FROM core.{self.table_name}
        """
        result = self.db.execute_query(query)

        if result and result[0]['max_ts']:
            return result[0]['max_ts']
        return None

    def get_last_totalizer_values(self) -> Dict[str, Any]:
        """Get the last known values for all totalizers.

        Returns:
            Dictionary with totalizer values
        """
        totalizers = {
            'electric_energy': 0.0,
            'gas_volume': 0.0,
            'water_volume': 0.0,
            'chiller_energy': {}
        }

        # Get latest electric energy
        query = f"""
            SELECT v.value_n
            FROM core.{self.table_name} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'energy'
            AND v.entity_id IN (
                SELECT et2.entity_id
                FROM core.entity_tag et2
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'elec'
            )
            ORDER BY v.ts DESC
            LIMIT 1
        """
        result = self.db.execute_query(query)
        if result and result[0]['value_n'] is not None:
            totalizers['electric_energy'] = float(result[0]['value_n'])

        # Get latest gas volume
        query = f"""
            SELECT v.value_n
            FROM core.{self.table_name} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'volume'
            AND v.entity_id IN (
                SELECT et2.entity_id
                FROM core.entity_tag et2
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'naturalGas'
            )
            ORDER BY v.ts DESC
            LIMIT 1
        """
        result = self.db.execute_query(query)
        if result and result[0]['value_n'] is not None:
            totalizers['gas_volume'] = float(result[0]['value_n'])

        # Get latest water volume
        query = f"""
            SELECT v.value_n
            FROM core.{self.table_name} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'volume'
            AND v.entity_id IN (
                SELECT et2.entity_id
                FROM core.entity_tag et2
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'water'
            )
            ORDER BY v.ts DESC
            LIMIT 1
        """
        result = self.db.execute_query(query)
        if result and result[0]['value_n'] is not None:
            totalizers['water_volume'] = float(result[0]['value_n'])

        # Get chiller energies
        query = f"""
            SELECT et_id.value_s as point_id, v.value_n
            FROM core.{self.table_name} v
            JOIN core.entity e ON v.entity_id = e.id
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            JOIN core.entity_tag et_id ON e.id = et_id.entity_id
            JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
            WHERE td.name = 'energy'
            AND td_id.name = 'id'
            AND et_id.value_s LIKE 'point-chiller-%-energy'
            AND v.ts = (
                SELECT MAX(ts) FROM core.{self.table_name} WHERE entity_id = v.entity_id
            )
        """
        result = self.db.execute_query(query)
        for row in result:
            point_id = row['point_id']
            if point_id:
                parts = point_id.split('-')
                if len(parts) >= 3:
                    chiller_num = int(parts[2])
                    totalizers['chiller_energy'][chiller_num] = float(row['value_n'])

        return totalizers

    def detect_entities_exist(self) -> bool:
        """Check if building entities exist in database.

        Returns:
            True if entities exist, False otherwise
        """
        query = """
            SELECT COUNT(*) as count
            FROM core.entity e
            JOIN core.entity_tag et ON e.id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'point' AND et.value_b = true
        """
        result = self.db.execute_query(query)
        count = result[0]['count'] if result else 0
        return count > 0

    def get_data_gap_ranges(self, start_time: datetime, end_time: datetime,
                           interval_minutes: int = 15) -> List[Dict[str, datetime]]:
        """Identify gaps in data within a time range.

        Args:
            start_time: Start of range to check
            end_time: End of range to check
            interval_minutes: Expected interval between data points

        Returns:
            List of dictionaries with 'start' and 'end' keys for each gap
        """
        query = f"""
            SELECT DISTINCT ts
            FROM core.{self.table_name}
            WHERE ts >= %s AND ts <= %s
            ORDER BY ts
        """
        result = self.db.execute_query(query, (start_time, end_time))
        actual_timestamps = set(row['ts'] for row in result)

        # Generate expected timestamps
        expected_timestamps = []
        current = start_time
        while current <= end_time:
            expected_timestamps.append(current)
            current += timedelta(minutes=interval_minutes)

        # Find gaps
        gaps = []
        gap_start = None

        for ts in expected_timestamps:
            if ts not in actual_timestamps:
                if gap_start is None:
                    gap_start = ts
            else:
                if gap_start is not None:
                    gaps.append({
                        'start': gap_start,
                        'end': ts - timedelta(minutes=interval_minutes)
                    })
                    gap_start = None

        # Close final gap if exists
        if gap_start is not None:
            gaps.append({
                'start': gap_start,
                'end': expected_timestamps[-1]
            })

        return gaps