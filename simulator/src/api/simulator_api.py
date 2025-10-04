"""FastAPI endpoints for simulator control and status.

Provides REST API for monitoring and controlling the Haystack building data simulator.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    uptime_seconds: float
    version: str = "1.0.0"


class StatusResponse(BaseModel):
    """Simulator status response."""
    status: str  # 'running', 'stopped', 'error'
    last_run: Optional[datetime]
    points_generated_total: Optional[int]
    error_message: Optional[str]


class StateResponse(BaseModel):
    """Detailed simulator state response."""
    status: str
    last_run_timestamp: Optional[datetime]
    totalizers: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    error_message: Optional[str]
    updated_at: Optional[datetime]


class ControlResponse(BaseModel):
    """Control action response."""
    message: str
    status: str


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    config: Dict[str, Any]


class ActivityEvent(BaseModel):
    """Activity log event."""
    id: int
    timestamp: datetime
    event_type: str
    message: str
    details: Optional[Dict[str, Any]]


class MetricsResponse(BaseModel):
    """Generation metrics response."""
    total_points_generated: int
    total_entities: int
    generation_rate_per_min: Optional[float]
    last_interval_duration_ms: Optional[float]
    error_count_24h: int
    uptime_seconds: float


def create_app(simulator_service, state_db, activity_logger, start_time: datetime) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        simulator_service: ContinuousDataService instance
        state_db: DatabaseConnection for state database
        activity_logger: ActivityLogger instance
        start_time: Service start time for uptime calculation

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Haystack Simulator API",
        description="Control and monitor the building data simulator",
        version="1.0.0"
    )

    # CORS middleware for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3001",  # Next.js dev server
            "http://localhost:3000",  # Alternative port
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        uptime = (datetime.now() - start_time).total_seconds()
        return HealthResponse(
            status="healthy",
            uptime_seconds=uptime
        )

    @app.get("/api/status", response_model=StatusResponse)
    async def get_status():
        """Get current simulator status."""
        try:
            # Query state from database
            query = """
                SELECT status, last_run_timestamp, error_message, config
                FROM core.simulator_state
                ORDER BY id DESC LIMIT 1
            """
            result = state_db.execute_query(query)

            if not result:
                return StatusResponse(
                    status="unknown",
                    last_run=None,
                    points_generated_total=None,
                    error_message="No state record found"
                )

            state = result[0]

            # Get total points from activity log (approximate)
            count_query = """
                SELECT COALESCE(SUM((details->>'point_count')::int), 0) as total
                FROM core.simulator_activity_log
                WHERE event_type = 'generation'
                AND details->>'point_count' IS NOT NULL
            """
            count_result = state_db.execute_query(count_query)
            points_total = count_result[0]['total'] if count_result else 0

            return StatusResponse(
                status=state['status'],
                last_run=state['last_run_timestamp'],
                points_generated_total=points_total,
                error_message=state.get('error_message')
            )

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve status: {str(e)}"
            )

    @app.get("/api/state", response_model=StateResponse)
    async def get_state():
        """Get detailed simulator state."""
        try:
            query = """
                SELECT status, last_run_timestamp, totalizers, config, error_message, updated_at
                FROM core.simulator_state
                ORDER BY id DESC LIMIT 1
            """
            result = state_db.execute_query(query)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No state record found"
                )

            state = result[0]

            return StateResponse(
                status=state['status'],
                last_run_timestamp=state['last_run_timestamp'],
                totalizers=state['totalizers'],
                config=state['config'],
                error_message=state.get('error_message'),
                updated_at=state['updated_at']
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve state: {str(e)}"
            )

    @app.post("/api/control/start", response_model=ControlResponse)
    async def start_simulator():
        """Start the simulator."""
        try:
            if not hasattr(simulator_service, 'start'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Start method not yet implemented in simulator service"
                )

            success = simulator_service.start()

            if success:
                activity_logger.log_start()
                return ControlResponse(
                    message="Simulator started successfully",
                    status="running"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start simulator"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start simulator: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start: {str(e)}"
            )

    @app.post("/api/control/stop", response_model=ControlResponse)
    async def stop_simulator():
        """Stop the simulator."""
        try:
            if not hasattr(simulator_service, 'stop'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Stop method not yet implemented in simulator service"
                )

            success = simulator_service.stop()

            if success:
                activity_logger.log_stop(reason="User requested stop")
                return ControlResponse(
                    message="Simulator stopped successfully",
                    status="stopped"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to stop simulator"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to stop simulator: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stop: {str(e)}"
            )

    @app.post("/api/control/reset", response_model=ControlResponse)
    async def reset_simulator(clear_data: bool = False):
        """Reset simulator state.

        Args:
            clear_data: Whether to clear generated data (query parameter)
        """
        try:
            if not hasattr(simulator_service, 'reset'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Reset method not yet implemented in simulator service"
                )

            success = simulator_service.reset(clear_data=clear_data)

            if success:
                activity_logger.log_reset(clear_data=clear_data)
                return ControlResponse(
                    message=f"Simulator reset successfully{' with data cleared' if clear_data else ''}",
                    status="initialized"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to reset simulator"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to reset simulator: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reset: {str(e)}"
            )

    @app.get("/api/config")
    async def get_config():
        """Get current configuration."""
        try:
            query = """
                SELECT config
                FROM core.simulator_state
                ORDER BY id DESC LIMIT 1
            """
            result = state_db.execute_query(query)

            if not result or not result[0].get('config'):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No configuration found"
                )

            return result[0]['config']

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve configuration: {str(e)}"
            )

    @app.put("/api/config", response_model=ControlResponse)
    async def update_config(config_update: ConfigUpdate):
        """Update simulator configuration."""
        try:
            # Update config in database
            query = """
                UPDATE core.simulator_state
                SET config = %s, updated_at = NOW()
                WHERE id = (SELECT id FROM core.simulator_state ORDER BY id DESC LIMIT 1)
            """

            import json
            config_json = json.dumps(config_update.config)
            state_db.execute_update(query, (config_json,))

            # Log config change
            activity_logger.log_config_change(config_update.config)

            return ControlResponse(
                message="Configuration updated successfully",
                status="updated"
            )

        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update configuration: {str(e)}"
            )

    @app.get("/api/activity")
    async def get_activity(
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None
    ):
        """Get activity log with pagination and filtering.

        Args:
            limit: Maximum number of records (default 100)
            offset: Number of records to skip (default 0)
            event_type: Filter by event type (optional)
        """
        try:
            events = activity_logger.get_activity(
                limit=limit,
                offset=offset,
                event_type=event_type
            )

            return {
                "events": events,
                "limit": limit,
                "offset": offset,
                "count": len(events)
            }

        except Exception as e:
            logger.error(f"Failed to get activity: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve activity log: {str(e)}"
            )

    @app.get("/api/metrics", response_model=MetricsResponse)
    async def get_metrics():
        """Get generation metrics and statistics."""
        try:
            # Get total points generated
            points_query = """
                SELECT COALESCE(SUM((details->>'point_count')::int), 0) as total
                FROM core.simulator_activity_log
                WHERE event_type = 'generation'
                AND details->>'point_count' IS NOT NULL
            """
            points_result = state_db.execute_query(points_query)
            total_points = points_result[0]['total'] if points_result else 0

            # Get entity count from last generation event
            entity_query = """
                SELECT details->>'entity_count' as count
                FROM core.simulator_activity_log
                WHERE event_type = 'generation'
                AND details->>'entity_count' IS NOT NULL
                ORDER BY timestamp DESC LIMIT 1
            """
            entity_result = state_db.execute_query(entity_query)
            total_entities = int(entity_result[0]['count']) if entity_result and entity_result[0]['count'] else 0

            # Calculate generation rate (last 10 minutes)
            rate_query = """
                SELECT
                    COALESCE(SUM((details->>'point_count')::int), 0) as points,
                    EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/60 as minutes
                FROM core.simulator_activity_log
                WHERE event_type = 'generation'
                AND timestamp >= NOW() - INTERVAL '10 minutes'
            """
            rate_result = state_db.execute_query(rate_query)
            if rate_result and rate_result[0]['minutes'] and rate_result[0]['minutes'] > 0:
                generation_rate = rate_result[0]['points'] / rate_result[0]['minutes']
            else:
                generation_rate = None

            # Get error count (last 24 hours)
            error_count = activity_logger.get_error_count(
                since=datetime.now() - timedelta(hours=24)
            )

            # Calculate uptime
            uptime = (datetime.now() - start_time).total_seconds()

            return MetricsResponse(
                total_points_generated=total_points,
                total_entities=total_entities,
                generation_rate_per_min=generation_rate,
                last_interval_duration_ms=None,  # TODO: Track this
                error_count_24h=error_count,
                uptime_seconds=uptime
            )

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve metrics: {str(e)}"
            )

    return app
