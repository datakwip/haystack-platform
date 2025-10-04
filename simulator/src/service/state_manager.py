"""State management for continuous data simulator.

This module handles detection and persistence of simulator state,
allowing the service to resume operations after restarts.
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class StateManager:
    """Manages simulator state persistence and detection."""

    def __init__(self, data_db: DatabaseConnection, state_db: DatabaseConnection,
                 service_name: str = 'haystack_simulator'):
        """Initialize state manager.

        Args:
            data_db: Database connection for building data (TimescaleDB)
            state_db: Database connection for operational state (PostgreSQL)
            service_name: Unique identifier for this service instance
        """
        self.data_db = data_db  # TimescaleDB - building data
        self.state_db = state_db  # PostgreSQL - operational state
        self.service_name = service_name
        self._ensure_state_table()

    def _ensure_state_table(self):
        """Ensure simulator_state table exists in state database."""
        try:
            # Check if table exists
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'core'
                    AND table_name = 'simulator_state'
                )
            """
            result = self.state_db.execute_query(query)

            if not result[0]['exists']:
                logger.warning("simulator_state table does not exist. Run schema/02_simulator_state.sql to create it.")

        except Exception as e:
            logger.error(f"Error checking simulator_state table: {e}")

    def detect_last_timestamp(self, value_table: str = 'values_demo') -> Optional[datetime]:
        """Detect the latest timestamp across all points.

        Args:
            value_table: Name of the values table

        Returns:
            Latest timestamp or None if no data exists
        """
        query = f"""
            SELECT MAX(ts) as max_ts
            FROM core.{value_table}
        """

        try:
            result = self.data_db.execute_query(query)
            if result and result[0]['max_ts']:
                logger.info(f"Last timestamp detected: {result[0]['max_ts']}")
                return result[0]['max_ts']
            else:
                logger.info("No existing data found in database")
                return None
        except Exception as e:
            logger.error(f"Error detecting last timestamp: {e}")
            return None

    def detect_entities_exist(self) -> bool:
        """Check if building entities are already created.

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

        try:
            result = self.data_db.execute_query(query)
            count = result[0]['count'] if result else 0
            exists = count > 0

            if exists:
                logger.info(f"Detected {count} existing point entities")
            else:
                logger.info("No existing entities found")

            return exists
        except Exception as e:
            logger.error(f"Error detecting entities: {e}")
            return False

    def calculate_gap(self, value_table: str = 'values_demo') -> Tuple[Optional[datetime], Optional[datetime], int]:
        """Calculate time gap from last data to present.

        Args:
            value_table: Name of the values table

        Returns:
            Tuple of (start_time, end_time, num_intervals) for gap
        """
        last_ts = self.detect_last_timestamp(value_table)
        current_time = datetime.now().replace(second=0, microsecond=0)

        if not last_ts:
            logger.info("No existing data - full historical generation needed")
            return None, None, 0

        # Align to next 15-minute interval after last timestamp
        start_time = last_ts + timedelta(minutes=15)
        start_time = start_time.replace(
            minute=(start_time.minute // 15) * 15,
            second=0,
            microsecond=0
        )

        # Calculate number of 15-minute intervals
        time_diff = current_time - start_time
        num_intervals = int(time_diff.total_seconds() / 900)  # 900 seconds = 15 minutes

        if num_intervals <= 0:
            logger.info("No gap detected - data is current")
            return None, None, 0

        logger.info(f"Gap detected: {num_intervals} intervals from {start_time} to {current_time}")
        return start_time, current_time, num_intervals

    def get_totalizer_states(self, value_table: str = 'values_demo') -> Dict[str, Any]:
        """Retrieve last known totalizer values for continuity.

        Args:
            value_table: Name of the values table

        Returns:
            Dictionary of totalizer states
        """
        # Get latest electric energy totalizer
        query_electric = f"""
            SELECT v.value_n
            FROM core.{value_table} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'energy'
            AND et.entity_id IN (
                SELECT et2.entity_id
                FROM core.entity_tag et2
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'elec'
            )
            ORDER BY v.ts DESC
            LIMIT 1
        """

        # Get latest gas volume totalizer
        query_gas = f"""
            SELECT v.value_n
            FROM core.{value_table} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'volume'
            AND et.entity_id IN (
                SELECT et2.entity_id
                FROM core.entity_tag et2
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'naturalGas'
            )
            ORDER BY v.ts DESC
            LIMIT 1
        """

        # Get latest water volume totalizer
        query_water = f"""
            SELECT v.value_n
            FROM core.{value_table} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'volume'
            AND et.entity_id IN (
                SELECT et2.entity_id
                FROM core.entity_tag et2
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'water'
            )
            ORDER BY v.ts DESC
            LIMIT 1
        """

        # Get chiller energy totalizers
        query_chillers = f"""
            SELECT et_id.value_s as point_id, v.value_n
            FROM core.{value_table} v
            JOIN core.entity e ON v.entity_id = e.id
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            JOIN core.entity_tag et_id ON e.id = et_id.entity_id
            JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
            WHERE td.name = 'energy'
            AND td_id.name = 'id'
            AND et_id.value_s LIKE 'point-chiller-%-energy'
            AND v.ts = (
                SELECT MAX(ts) FROM core.{value_table} WHERE entity_id = v.entity_id
            )
        """

        totalizers = {
            'electric_energy': 0.0,
            'gas_volume': 0.0,
            'water_volume': 0.0,
            'chiller_energy': {}
        }

        try:
            # Get electric energy
            result = self.data_db.execute_query(query_electric)
            if result and result[0]['value_n'] is not None:
                totalizers['electric_energy'] = float(result[0]['value_n'])

            # Get gas volume
            result = self.data_db.execute_query(query_gas)
            if result and result[0]['value_n'] is not None:
                totalizers['gas_volume'] = float(result[0]['value_n'])

            # Get water volume
            result = self.data_db.execute_query(query_water)
            if result and result[0]['value_n'] is not None:
                totalizers['water_volume'] = float(result[0]['value_n'])

            # Get chiller energies
            result = self.data_db.execute_query(query_chillers)
            for row in result:
                # Extract chiller number from point_id like "point-chiller-1-energy"
                point_id = row['point_id']
                if point_id:
                    parts = point_id.split('-')
                    if len(parts) >= 3:
                        chiller_num = int(parts[2])
                        totalizers['chiller_energy'][chiller_num] = float(row['value_n'])

            logger.info(f"Retrieved totalizer states: {totalizers}")
            return totalizers

        except Exception as e:
            logger.error(f"Error retrieving totalizer states: {e}")
            return totalizers

    def save_service_state(self, status: str, totalizers: Optional[Dict] = None,
                          last_run_ts: Optional[datetime] = None,
                          config: Optional[Dict] = None,
                          error_message: Optional[str] = None):
        """Persist service state to database.

        Args:
            status: Service status (running, stopped, error, etc.)
            totalizers: Current totalizer values
            last_run_ts: Timestamp of last successful run
            config: Service configuration
            error_message: Error message if status is error
        """
        # Check if state record exists
        query_check = """
            SELECT id FROM core.simulator_state
            WHERE service_name = %s
        """

        try:
            result = self.state_db.execute_query(query_check, (self.service_name,))

            if result:
                # Update existing record
                query = """
                    UPDATE core.simulator_state
                    SET status = %s,
                        last_run_timestamp = COALESCE(%s, last_run_timestamp),
                        totalizers = COALESCE(%s, totalizers),
                        config = COALESCE(%s, config),
                        error_message = %s,
                        updated_at = NOW()
                    WHERE service_name = %s
                """
                self.state_db.execute_update(
                    query,
                    (
                        status,
                        last_run_ts,
                        json.dumps(totalizers) if totalizers else None,
                        json.dumps(config) if config else None,
                        error_message,
                        self.service_name
                    )
                )
            else:
                # Insert new record
                query = """
                    INSERT INTO core.simulator_state
                    (service_name, status, last_run_timestamp, totalizers, config, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.state_db.execute_update(
                    query,
                    (
                        self.service_name,
                        status,
                        last_run_ts,
                        json.dumps(totalizers) if totalizers else None,
                        json.dumps(config) if config else None,
                        error_message
                    )
                )

            logger.info(f"Saved service state: {status}")

        except Exception as e:
            logger.error(f"Error saving service state: {e}")
            raise

    def get_service_state(self) -> Optional[Dict[str, Any]]:
        """Retrieve current service state from database.

        Returns:
            Dictionary with service state or None
        """
        query = """
            SELECT service_name, status, last_run_timestamp,
                   totalizers, config, error_message, updated_at
            FROM core.simulator_state
            WHERE service_name = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """

        try:
            result = self.state_db.execute_query(query, (self.service_name,))

            if result:
                state = dict(result[0])
                # Parse JSON fields
                if state.get('totalizers'):
                    state['totalizers'] = json.loads(state['totalizers']) if isinstance(state['totalizers'], str) else state['totalizers']
                if state.get('config'):
                    state['config'] = json.loads(state['config']) if isinstance(state['config'], str) else state['config']

                logger.info(f"Retrieved service state: {state['status']}")
                return state
            else:
                logger.info("No saved service state found")
                return None

        except Exception as e:
            logger.error(f"Error retrieving service state: {e}")
            return None
