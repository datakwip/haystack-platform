"""Continuous data generation service.

This module provides the main service class for continuous data generation
with lifecycle management and error handling.
"""

import logging
import signal
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from database.connection import DatabaseConnection
from database.data_loader import DataLoader
from database.schema_setup import SchemaSetup
from generators.entities import EntityGenerator
from generators.time_series import TimeSeriesGenerator
from generators.weather import WeatherSimulator
from generators.schedules import ScheduleGenerator
from service.state_manager import StateManager
from service.gap_filler import GapFiller

logger = logging.getLogger(__name__)


class ContinuousDataService:
    """Manages continuous data generation service lifecycle."""

    def __init__(self, db_config: Dict[str, Any], building_config: Dict[str, Any],
                 value_table: str = 'values_demo'):
        """Initialize continuous data service.

        Args:
            db_config: Database configuration (includes 'database' and 'state_database' keys)
            building_config: Building configuration
            value_table: Name of the values table
        """
        self.db_config = db_config
        self.building_config = building_config
        self.value_table = value_table

        # Initialize components
        self.data_db: Optional[DatabaseConnection] = None  # TimescaleDB - building data
        self.state_db: Optional[DatabaseConnection] = None  # PostgreSQL - operational state
        self.state_manager: Optional[StateManager] = None
        self.entity_map: Dict[str, int] = {}

        self.running = False
        self.shutdown_requested = False

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def startup(self) -> bool:
        """Initialize service and prepare for data generation.

        Returns:
            True if startup successful, False otherwise
        """
        try:
            logger.info("Starting continuous data service...")

            # Connect to TimescaleDB (building data)
            self.data_db = DatabaseConnection(self.db_config['database'])
            logger.info("TimescaleDB connected (building data)")

            # Connect to PostgreSQL (operational state)
            self.state_db = DatabaseConnection(self.db_config['state_database'])
            logger.info("PostgreSQL connected (operational state)")

            # Initialize state manager with both databases
            self.state_manager = StateManager(self.data_db, self.state_db)

            # Check if entities exist
            data_loader = DataLoader(self.data_db, self.value_table)
            entities_exist = data_loader.detect_entities_exist()

            if not entities_exist:
                logger.info("No entities found - generating building entities...")
                schema = SchemaSetup(self.data_db)
                org_id = schema.initialize_organization(
                    self.db_config['organization']['name'],
                    self.db_config['organization']['key']
                )
                schema.create_value_tables(self.db_config['organization']['key'])

                entity_gen = EntityGenerator(schema, self.building_config)
                self.entity_map = entity_gen.generate_all_entities()
                logger.info(f"Generated {len(self.entity_map)} entities")
            else:
                logger.info("Entities already exist - loading entity map...")
                self.entity_map = self._load_entity_map()
                logger.info(f"Loaded {len(self.entity_map)} entities")

            # Detect and fill any gaps
            gap_start, gap_end, num_intervals = self.state_manager.calculate_gap(self.value_table)

            if num_intervals > 0:
                logger.info(f"Detected gap of {num_intervals} intervals - filling...")

                # Get last totalizer values for continuity
                totalizers = self.state_manager.get_totalizer_states(self.value_table)

                # Fill the gap
                gap_filler = GapFiller(self.data_db, self.building_config, self.entity_map, self.value_table)
                success = gap_filler.fill_gap_incremental(
                    gap_start,
                    gap_end,
                    initial_totalizers=totalizers
                )

                if success:
                    logger.info("Gap filled successfully")
                else:
                    logger.error("Failed to fill gap")
                    return False

            # Save startup state
            self.state_manager.save_service_state(
                status='running',
                config={'mode': 'continuous', 'version': '1.0'}
            )

            self.running = True
            logger.info("Service startup complete")
            return True

        except Exception as e:
            logger.error(f"Service startup failed: {e}", exc_info=True)
            if self.state_manager:
                self.state_manager.save_service_state(
                    status='error',
                    error_message=str(e)
                )
            return False

    def generate_current_interval(self) -> bool:
        """Generate data for the current 15-minute interval.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current time aligned to 15-minute interval
            current_time = datetime.now().replace(second=0, microsecond=0)
            aligned_time = current_time.replace(
                minute=(current_time.minute // 15) * 15
            )

            logger.info(f"Generating data for interval: {aligned_time}")

            # Get current totalizer states
            data_loader = DataLoader(self.data_db, self.value_table)
            totalizers = data_loader.get_last_totalizer_values()

            # Initialize generators
            ts_gen = TimeSeriesGenerator(
                self.building_config,
                self.entity_map,
                initial_totalizers=totalizers
            )
            weather_sim = WeatherSimulator(self.building_config['weather'])
            schedule_gen = ScheduleGenerator(self.building_config)

            # Generate weather and occupancy
            weather = weather_sim.get_current_weather(aligned_time)
            occupancy = schedule_gen.get_occupancy_ratio(aligned_time)

            # Generate data points
            data_points = ts_gen._generate_timestamp_data(
                aligned_time,
                weather['dry_bulb_temp'],
                weather['season'],
                occupancy
            )

            # Insert data
            data_loader.insert_time_series_batch(data_points)

            # Update current values
            data_loader.update_current_values(data_points)

            # Save state
            self.state_manager.save_service_state(
                status='running',
                last_run_ts=aligned_time,
                totalizers=ts_gen.totalizers
            )

            logger.info(f"Successfully generated {len(data_points)} data points for {aligned_time}")
            return True

        except Exception as e:
            logger.error(f"Error generating interval data: {e}", exc_info=True)
            if self.state_manager:
                self.state_manager.save_service_state(
                    status='error',
                    error_message=str(e)
                )
            return False

    def shutdown(self):
        """Gracefully shutdown the service."""
        logger.info("Shutting down continuous data service...")

        if self.state_manager:
            self.state_manager.save_service_state(status='stopped')

        if self.data_db:
            self.data_db.close()
            logger.info("TimescaleDB connection closed")

        if self.state_db:
            self.state_db.close()
            logger.info("State database connection closed")

        self.running = False
        logger.info("Service shutdown complete")

    def health_check(self) -> Dict[str, Any]:
        """Get current service health status.

        Returns:
            Dictionary with health status information
        """
        status = {
            'service': 'haystack_simulator',
            'status': 'running' if self.running else 'stopped',
            'timestamp': datetime.now().isoformat()
        }

        if self.state_manager:
            try:
                service_state = self.state_manager.get_service_state()
                if service_state:
                    # Convert datetime to ISO format string for JSON serialization
                    last_run = service_state.get('last_run_timestamp')
                    status['last_run'] = last_run.isoformat() if last_run else None
                    status['state_status'] = service_state.get('status')
            except Exception as e:
                status['error'] = str(e)

        return status

    def _load_entity_map(self) -> Dict[str, int]:
        """Load entity map from database.

        Returns:
            Dictionary mapping entity names to IDs
        """
        query = """
            SELECT e.id, et_id.value_s as entity_name
            FROM core.entity e
            JOIN core.entity_tag et_id ON e.id = et_id.entity_id
            JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
            WHERE td_id.name = 'id'
        """

        result = self.data_db.execute_query(query)
        entity_map = {}

        for row in result:
            if row['entity_name']:
                entity_map[row['entity_name']] = row['id']

        return entity_map

    # Control methods for API

    def start(self) -> bool:
        """Start the simulator if not already running.

        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Simulator is already running")
            return False

        try:
            # If service hasn't been initialized yet, run startup
            if not self.data_db or not self.state_db:
                return self.startup()

            # Otherwise, just mark as running
            self.running = True
            self.shutdown_requested = False

            if self.state_manager:
                self.state_manager.save_service_state(status='running')

            logger.info("Simulator started")
            return True

        except Exception as e:
            logger.error(f"Failed to start simulator: {e}")
            return False

    def stop(self) -> bool:
        """Stop the simulator gracefully.

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Simulator is not running")
            return False

        try:
            self.running = False
            self.shutdown_requested = True

            if self.state_manager:
                self.state_manager.save_service_state(status='stopped')

            logger.info("Simulator stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop simulator: {e}")
            return False

    def pause(self) -> bool:
        """Pause the simulator temporarily without full shutdown.

        Returns:
            True if paused successfully, False otherwise
        """
        if not self.running:
            logger.warning("Simulator is not running, cannot pause")
            return False

        try:
            self.running = False

            if self.state_manager:
                self.state_manager.save_service_state(status='paused')

            logger.info("Simulator paused")
            return True

        except Exception as e:
            logger.error(f"Failed to pause simulator: {e}")
            return False

    def reset(self, clear_data: bool = False) -> bool:
        """Reset simulator state and optionally clear generated data.

        Args:
            clear_data: If True, clear all generated time-series data

        Returns:
            True if reset successfully, False otherwise
        """
        try:
            # Stop if running
            was_running = self.running
            if self.running:
                self.stop()

            # Reset state
            if self.state_manager:
                # Reset totalizers to zero
                zero_totalizers = {
                    'electric_energy': 0.0,
                    'gas_volume': 0.0,
                    'water_volume': 0.0,
                    'chiller_energy': {}
                }

                self.state_manager.save_service_state(
                    status='initialized',
                    last_run_ts=None,
                    totalizers=zero_totalizers,
                    error_message=None
                )

            # Optionally clear data
            if clear_data and self.data_db:
                logger.info("Clearing generated data...")
                try:
                    # Truncate value tables
                    truncate_queries = [
                        f"TRUNCATE TABLE core.{self.value_table} CASCADE;",
                        f"TRUNCATE TABLE core.{self.value_table}_current CASCADE;"
                    ]

                    for query in truncate_queries:
                        try:
                            self.data_db.execute_update(query)
                        except Exception as e:
                            logger.warning(f"Failed to truncate table: {e}")

                    logger.info("Data cleared successfully")

                except Exception as e:
                    logger.error(f"Failed to clear data: {e}")
                    return False

            # Restart if it was running
            if was_running:
                return self.start()

            logger.info(f"Simulator reset{' with data cleared' if clear_data else ''}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset simulator: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get current generation metrics and statistics.

        Returns:
            Dictionary with metrics data
        """
        metrics = {
            'running': self.running,
            'entity_count': len(self.entity_map),
            'value_table': self.value_table
        }

        if self.state_manager:
            try:
                state = self.state_manager.get_service_state()
                if state:
                    metrics['status'] = state.get('status')
                    metrics['last_run'] = state.get('last_run_timestamp')
                    metrics['totalizers'] = state.get('totalizers')
                    metrics['error_message'] = state.get('error_message')

            except Exception as e:
                logger.error(f"Failed to get state metrics: {e}")
                metrics['metrics_error'] = str(e)

        # Get count of generated points (if possible)
        if self.data_db:
            try:
                count_query = f"SELECT COUNT(*) as count FROM core.{self.value_table}"
                result = self.data_db.execute_query(count_query)
                if result:
                    metrics['total_points'] = result[0]['count']
            except Exception as e:
                logger.warning(f"Failed to get point count: {e}")

        return metrics
