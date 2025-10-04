"""Activity logging service for simulator events.

Logs domain-level events (generation, errors, config changes) to the activity_log
table in the state database for monitoring and debugging.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ActivityLogger:
    """Logs simulator activity events to database."""

    def __init__(self, state_db):
        """Initialize activity logger.

        Args:
            state_db: DatabaseConnection instance for state database
        """
        self.state_db = state_db

    def log_event(
        self,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log an activity event.

        Args:
            event_type: Type of event (generation, gap_fill, error, start, stop, config_change, reset)
            message: Human-readable event description
            details: Additional event context as dictionary
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if logged successfully, False otherwise
        """
        try:
            query = """
                INSERT INTO core.simulator_activity_log
                (timestamp, event_type, message, details)
                VALUES (%s, %s, %s, %s)
            """

            ts = timestamp or datetime.now()
            details_json = json.dumps(details) if details else None

            self.state_db.execute_update(
                query,
                (ts, event_type, message, details_json)
            )

            logger.debug(f"Logged activity: {event_type} - {message}")
            return True

        except Exception as e:
            logger.error(f"Failed to log activity event: {e}")
            return False

    def log_generation(
        self,
        interval: datetime,
        point_count: int,
        entity_count: int,
        weather: Optional[Dict] = None,
        occupancy: Optional[Dict] = None
    ):
        """Log a data generation event.

        Args:
            interval: Interval timestamp that was generated
            point_count: Number of data points generated
            entity_count: Number of entities with data
            weather: Weather data context
            occupancy: Occupancy data context
        """
        details = {
            'interval': interval.isoformat(),
            'point_count': point_count,
            'entity_count': entity_count
        }

        if weather:
            details['weather'] = weather
        if occupancy:
            details['occupancy'] = occupancy

        message = f"Generated {point_count} points for interval {interval.strftime('%Y-%m-%d %H:%M:%S')}"
        self.log_event('generation', message, details)

    def log_gap_fill(
        self,
        start_time: datetime,
        end_time: datetime,
        gap_count: int,
        points_filled: int
    ):
        """Log a gap filling event.

        Args:
            start_time: Gap start time
            end_time: Gap end time
            gap_count: Number of gaps filled
            points_filled: Total points generated for gaps
        """
        details = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'gap_count': gap_count,
            'points_filled': points_filled
        }

        message = f"Filled {gap_count} gaps ({points_filled} points) from {start_time} to {end_time}"
        self.log_event('gap_fill', message, details)

    def log_error(self, error_message: str, error_details: Optional[Dict] = None):
        """Log an error event.

        Args:
            error_message: Error description
            error_details: Additional error context
        """
        self.log_event('error', error_message, error_details)

    def log_start(self, config: Optional[Dict] = None):
        """Log simulator start event.

        Args:
            config: Configuration details
        """
        message = "Simulator service started"
        self.log_event('start', message, config)

    def log_stop(self, reason: Optional[str] = None):
        """Log simulator stop event.

        Args:
            reason: Reason for stopping
        """
        message = f"Simulator service stopped{': ' + reason if reason else ''}"
        self.log_event('stop', message, {'reason': reason} if reason else None)

    def log_config_change(self, changes: Dict[str, Any]):
        """Log configuration change event.

        Args:
            changes: Dictionary of configuration changes
        """
        message = "Configuration updated"
        self.log_event('config_change', message, changes)

    def log_reset(self, clear_data: bool = False):
        """Log simulator reset event.

        Args:
            clear_data: Whether data was cleared
        """
        message = f"Simulator reset{' with data cleared' if clear_data else ''}"
        self.log_event('reset', message, {'clear_data': clear_data})

    def get_activity(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Query activity log with filtering and pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            List of activity log records
        """
        try:
            # Build query with filters
            query = "SELECT * FROM core.simulator_activity_log WHERE 1=1"
            params = []

            if event_type:
                query += " AND event_type = %s"
                params.append(event_type)

            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= %s"
                params.append(end_time)

            query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            results = self.state_db.execute_query(query, tuple(params))

            # Convert RealDictRow to regular dicts and handle JSON
            events = []
            for row in results:
                event = dict(row)
                # Parse details JSON if present
                if event.get('details'):
                    try:
                        if isinstance(event['details'], str):
                            event['details'] = json.loads(event['details'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse details JSON for event {event['id']}")
                events.append(event)

            return events

        except Exception as e:
            logger.error(f"Failed to query activity log: {e}")
            return []

    def get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent activity log records
        """
        return self.get_activity(limit=limit)

    def get_error_count(self, since: Optional[datetime] = None) -> int:
        """Get count of error events.

        Args:
            since: Count errors since this time (defaults to all time)

        Returns:
            Number of error events
        """
        try:
            query = "SELECT COUNT(*) as count FROM core.simulator_activity_log WHERE event_type = 'error'"
            params = []

            if since:
                query += " AND timestamp >= %s"
                params.append(since)

            result = self.state_db.execute_query(query, tuple(params) if params else None)
            return result[0]['count'] if result else 0

        except Exception as e:
            logger.error(f"Failed to get error count: {e}")
            return 0
