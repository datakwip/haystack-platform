"""Main entry point for continuous data generation service.

This script starts the continuous data simulator service with health monitoring
and scheduled data generation.
"""

import logging
import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent))

from service.continuous_generator import ContinuousDataService
from service.scheduler import DataGenerationScheduler
from service.health_server import HealthCheckServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config_with_env(config_path: str) -> Dict[str, Any]:
    """Load configuration file with environment variable substitution.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Configuration dictionary with env vars substituted
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Ensure state_database section exists
    if 'state_database' not in config:
        config['state_database'] = {}

    # Support environment variable substitution for DATABASE_URL (Railway format - TimescaleDB)
    if 'DATABASE_URL' in os.environ:
        # Parse DATABASE_URL and update config
        db_url = os.environ['DATABASE_URL']
        # postgresql://user:password@host:port/database
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            parts = db_url.replace('postgresql://', '').replace('postgres://', '').split('@')
            if len(parts) == 2:
                user_pass = parts[0].split(':')
                host_port_db = parts[1].split('/')

                if len(user_pass) == 2 and len(host_port_db) == 2:
                    user, password = user_pass
                    host_port = host_port_db[0].split(':')
                    database = host_port_db[1]

                    config['database']['user'] = user
                    config['database']['password'] = password
                    config['database']['database'] = database

                    if len(host_port) == 2:
                        config['database']['host'] = host_port[0]
                        config['database']['port'] = int(host_port[1])
                    else:
                        config['database']['host'] = host_port[0]

    # Support environment variable substitution for STATE_DB_URL (Railway format - PostgreSQL)
    if 'STATE_DB_URL' in os.environ:
        # Parse STATE_DB_URL and update config
        db_url = os.environ['STATE_DB_URL']
        # postgresql://user:password@host:port/database
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            parts = db_url.replace('postgresql://', '').replace('postgres://', '').split('@')
            if len(parts) == 2:
                user_pass = parts[0].split(':')
                host_port_db = parts[1].split('/')

                if len(user_pass) == 2 and len(host_port_db) == 2:
                    user, password = user_pass
                    host_port = host_port_db[0].split(':')
                    database = host_port_db[1]

                    config['state_database']['user'] = user
                    config['state_database']['password'] = password
                    config['state_database']['database'] = database

                    if len(host_port) == 2:
                        config['state_database']['host'] = host_port[0]
                        config['state_database']['port'] = int(host_port[1])
                    else:
                        config['state_database']['host'] = host_port[0]

    # Override with individual environment variables if present (TimescaleDB)
    config['database']['host'] = os.getenv('DB_HOST', config['database'].get('host', 'localhost'))
    config['database']['port'] = int(os.getenv('DB_PORT', config['database'].get('port', 5432)))
    config['database']['database'] = os.getenv('DB_NAME', config['database'].get('database', 'datakwip'))
    config['database']['user'] = os.getenv('DB_USER', config['database'].get('user', 'demo'))
    config['database']['password'] = os.getenv('DB_PASSWORD', config['database'].get('password', 'demo123'))

    # Override with individual environment variables if present (State DB)
    config['state_database']['host'] = os.getenv('STATE_DB_HOST', config['state_database'].get('host', 'localhost'))
    config['state_database']['port'] = int(os.getenv('STATE_DB_PORT', config['state_database'].get('port', 5433)))
    config['state_database']['database'] = os.getenv('STATE_DB_NAME', config['state_database'].get('database', 'simulator_state'))
    config['state_database']['user'] = os.getenv('STATE_DB_USER', config['state_database'].get('user', 'simulator_user'))
    config['state_database']['password'] = os.getenv('STATE_DB_PASSWORD', config['state_database'].get('password', 'simulator_password'))

    return config


def main():
    """Main service entry point."""
    logger.info("=" * 60)
    logger.info("Haystack Building Data Simulator - Continuous Service")
    logger.info("=" * 60)

    try:
        # Load configurations
        db_config_path = os.getenv('DB_CONFIG_PATH', 'config/database_config.yaml')
        building_config_path = os.getenv('BUILDING_CONFIG_PATH', 'config/building_config.yaml')

        logger.info(f"Loading database config from: {db_config_path}")
        db_config = load_config_with_env(db_config_path)

        logger.info(f"Loading building config from: {building_config_path}")
        with open(building_config_path, 'r') as f:
            building_config = yaml.safe_load(f)

        # Get service configuration from environment
        health_port = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
        interval_minutes = int(os.getenv('SERVICE_INTERVAL_MINUTES',
                                        building_config['generation']['data_interval_minutes']))

        logger.info(f"Service configuration:")
        logger.info(f"  Database: {db_config['database']['host']}:{db_config['database']['port']}/{db_config['database']['database']}")
        logger.info(f"  Health check port: {health_port}")
        logger.info(f"  Data interval: {interval_minutes} minutes")

        # Initialize service
        value_table = db_config['tables']['value_table']
        service = ContinuousDataService(db_config, building_config, value_table)

        # Start service
        logger.info("Starting service...")
        if not service.startup():
            logger.error("Service startup failed")
            sys.exit(1)

        # Start health check server
        logger.info(f"Starting health check server on port {health_port}...")
        health_server = HealthCheckServer(
            port=health_port,
            health_callback=service.health_check
        )
        health_server.start()

        # Start scheduler
        logger.info("Starting data generation scheduler...")
        scheduler = DataGenerationScheduler(interval_minutes=interval_minutes)
        scheduler.start(service.generate_current_interval)

        logger.info("=" * 60)
        logger.info("Service started successfully!")
        logger.info(f"Health check: http://0.0.0.0:{health_port}/health")
        logger.info(f"Status: http://0.0.0.0:{health_port}/status")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Keep service running
        import time
        while not service.shutdown_requested:
            time.sleep(1)

        # Graceful shutdown
        logger.info("Shutting down...")
        scheduler.stop()
        health_server.stop()
        service.shutdown()

        logger.info("Service stopped successfully")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
