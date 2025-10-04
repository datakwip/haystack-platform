"""Gap filling service for backfilling missing data intervals.

This module handles detection and filling of data gaps when the simulator
restarts or recovers from downtime.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from database.connection import DatabaseConnection
from database.data_loader import DataLoader
from generators.time_series import TimeSeriesGenerator
from generators.weather import WeatherSimulator
from generators.schedules import ScheduleGenerator

logger = logging.getLogger(__name__)


class GapFiller:
    """Handles detection and filling of data gaps."""

    def __init__(self, db: DatabaseConnection, building_config: Dict[str, Any],
                 entity_map: Dict[str, int], value_table: str = 'values_demo'):
        """Initialize gap filler.

        Args:
            db: Database connection instance
            building_config: Building configuration dictionary
            entity_map: Mapping of entity names to database IDs
            value_table: Name of the values table
        """
        self.db = db
        self.building_config = building_config
        self.entity_map = entity_map
        self.value_table = value_table
        self.data_loader = DataLoader(db, value_table)

    def detect_gaps(self, start_time: datetime, end_time: datetime,
                   interval_minutes: int = 15) -> List[Dict[str, datetime]]:
        """Detect missing intervals in the specified time range.

        Args:
            start_time: Start of range to check
            end_time: End of range to check
            interval_minutes: Expected interval between data points

        Returns:
            List of gap dictionaries with 'start' and 'end' keys
        """
        # Generate expected timestamps
        expected_timestamps = pd.date_range(
            start=start_time,
            end=end_time,
            freq=f'{interval_minutes}min'
        )

        # Get actual timestamps from database
        query = f"""
            SELECT DISTINCT ts
            FROM core.{self.value_table}
            WHERE ts >= %s AND ts <= %s
            ORDER BY ts
        """

        try:
            result = self.db.execute_query(query, (start_time, end_time))
            actual_timestamps = set(row['ts'] for row in result)

            # Find missing timestamps
            missing_timestamps = []
            for ts in expected_timestamps:
                if ts.to_pydatetime() not in actual_timestamps:
                    missing_timestamps.append(ts.to_pydatetime())

            # Group consecutive missing timestamps into gaps
            gaps = []
            if missing_timestamps:
                gap_start = missing_timestamps[0]
                prev_ts = missing_timestamps[0]

                for ts in missing_timestamps[1:]:
                    if (ts - prev_ts).total_seconds() > interval_minutes * 60:
                        # End of current gap
                        gaps.append({'start': gap_start, 'end': prev_ts})
                        gap_start = ts
                    prev_ts = ts

                # Add final gap
                gaps.append({'start': gap_start, 'end': prev_ts})

            logger.info(f"Detected {len(gaps)} gaps with {len(missing_timestamps)} missing intervals")
            return gaps

        except Exception as e:
            logger.error(f"Error detecting gaps: {e}")
            return []

    def fill_gap_incremental(self, start_time: datetime, end_time: datetime,
                            initial_totalizers: Optional[Dict[str, Any]] = None,
                            chunk_size: int = 1000) -> bool:
        """Fill data gap incrementally to avoid memory issues.

        Args:
            start_time: Start time for gap fill
            end_time: End time for gap fill
            initial_totalizers: Initial totalizer values to continue from
            chunk_size: Number of intervals to process at once

        Returns:
            True if successful, False otherwise
        """
        try:
            interval_minutes = self.building_config['generation']['data_interval_minutes']

            # Generate time range
            time_range = pd.date_range(
                start=start_time,
                end=end_time,
                freq=f'{interval_minutes}min'
            )

            total_intervals = len(time_range)
            logger.info(f"Filling gap: {total_intervals} intervals from {start_time} to {end_time}")

            # Initialize generators with totalizers
            ts_gen = TimeSeriesGenerator(
                self.building_config,
                self.entity_map,
                initial_totalizers=initial_totalizers
            )
            weather_sim = WeatherSimulator(self.building_config['weather'])
            schedule_gen = ScheduleGenerator(self.building_config)

            # Process in chunks
            for chunk_start in range(0, total_intervals, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_intervals)
                chunk_timestamps = time_range[chunk_start:chunk_end]

                chunk_data = []

                for timestamp in chunk_timestamps:
                    # Generate weather and occupancy
                    weather = weather_sim.get_current_weather(timestamp.to_pydatetime())
                    occupancy = schedule_gen.get_occupancy_ratio(timestamp.to_pydatetime())

                    # Generate data points
                    timestamp_data = ts_gen._generate_timestamp_data(
                        timestamp.to_pydatetime(),
                        weather['dry_bulb_temp'],
                        weather['season'],
                        occupancy
                    )

                    chunk_data.extend(timestamp_data)

                # Insert chunk
                if chunk_data:
                    chunk_df = pd.DataFrame(chunk_data)
                    self.data_loader.insert_dataframe(chunk_df, chunk_size=10000)

                progress = (chunk_end / total_intervals) * 100
                logger.info(f"Gap fill progress: {progress:.1f}% ({chunk_end}/{total_intervals})")

            logger.info(f"Successfully filled gap with {total_intervals} intervals")
            return True

        except Exception as e:
            logger.error(f"Error filling gap: {e}")
            return False

    def preserve_totalizer_continuity(self, totalizers: Dict[str, Any],
                                     new_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure totalizers continue from last known values without reset.

        Args:
            totalizers: Last known totalizer values
            new_data: New data points being generated

        Returns:
            Updated data points with correct totalizer values
        """
        # This is handled in TimeSeriesGenerator when initialized with totalizers
        # This method is for validation and adjustment if needed
        return new_data

    def verify_gap_filled(self, start_time: datetime, end_time: datetime,
                         interval_minutes: int = 15) -> bool:
        """Validate that gap has been filled successfully.

        Args:
            start_time: Start of filled range
            end_time: End of filled range
            interval_minutes: Expected interval

        Returns:
            True if gap is filled, False if missing intervals remain
        """
        gaps = self.detect_gaps(start_time, end_time, interval_minutes)

        if not gaps:
            logger.info("Gap verification passed - no missing intervals")
            return True
        else:
            logger.warning(f"Gap verification failed - {len(gaps)} gaps remain")
            for gap in gaps:
                logger.warning(f"  Gap: {gap['start']} to {gap['end']}")
            return False

    def get_data_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get summary statistics for data in time range.

        Args:
            start_time: Start time
            end_time: End time

        Returns:
            Dictionary with summary statistics
        """
        query = f"""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT entity_id) as unique_points,
                MIN(ts) as earliest,
                MAX(ts) as latest,
                COUNT(DISTINCT ts) as unique_timestamps
            FROM core.{self.value_table}
            WHERE ts >= %s AND ts <= %s
        """

        try:
            result = self.db.execute_query(query, (start_time, end_time))
            summary = dict(result[0]) if result else {}

            logger.info(f"Data summary for {start_time} to {end_time}:")
            logger.info(f"  Total records: {summary.get('total_records', 0):,}")
            logger.info(f"  Unique points: {summary.get('unique_points', 0)}")
            logger.info(f"  Unique timestamps: {summary.get('unique_timestamps', 0)}")

            return summary

        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
