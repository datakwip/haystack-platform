import jsoncfg
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import sys

load_dotenv()

logger = logging.getLogger(__name__)
config = jsoncfg.load_config('./config.json')
dk_env = os.getenv('dk_env')
if dk_env is None:
    dk_env = "tigerdata"

# Parse multiple config keys from dk_env (comma-separated)
config_keys = [key.strip() for key in dk_env.split(',')]
print("config_keys: {}".format(config_keys))

# Use the first config as the primary config for regular operations
primary_config_key = config_keys[0]
print("primary_config_key: {}".format(primary_config_key))

log_timing = os.getenv('log_timing')
if log_timing is None:
    log_timing = '0'

# Primary config (used for most endpoints)
database = config[primary_config_key].dbUrl()
database_grafana_connector= config[primary_config_key].dbUrlGrafanaConnector()
app_client_id = config[primary_config_key].app_client_id()
user_pool_id= config[primary_config_key].user_pool_id()
load_data_from_csv = False
log_level = "INFO"
dbSchema = config[primary_config_key].dbScheme()
test_table = os.getenv('test_tables')

# Database connection pool settings
main_db_pool_size = int(os.getenv('MAIN_DB_POOL_SIZE', '5'))
main_db_max_overflow = int(os.getenv('MAIN_DB_MAX_OVERFLOW', '5'))
grafana_db_pool_size = int(os.getenv('GRAFANA_DB_POOL_SIZE', '1'))
grafana_db_max_overflow = int(os.getenv('GRAFANA_DB_MAX_OVERFLOW', '0'))

def check_database_availability(db_url: str) -> bool:
    """Check if database is available by attempting a connection"""
    try:
        # Check if required PostgreSQL driver is available
        try:
            import psycopg2
        except ImportError:
            try:
                import psycopg2_binary
            except ImportError:
                logger.error(f"PostgreSQL driver not found. Please install psycopg2 or psycopg2-binary")
                return False
        
        engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as e:
        error_msg = str(e)
        if "Can't load plugin: sqlalchemy.dialects:postgres" in error_msg:
            logger.error(f"PostgreSQL dialect not available. Please install psycopg2-binary: pip install psycopg2-binary")
        else:
            logger.error(f"Database connection failed for {db_url}: {error_msg}")
        return False

# All configs (used for /bulk/value and /value endpoints)
all_configs = []
available_configs = []

for i, key in enumerate(config_keys):
    cfg = {
        'key': key,
        'dbUrl': config[key].dbUrl(),
        'dbUrlGrafanaConnector': config[key].dbUrlGrafanaConnector() if hasattr(config[key], 'dbUrlGrafanaConnector') else None,
        'dbScheme': config[key].dbScheme(),
        'app_client_id': config[key].app_client_id() if hasattr(config[key], 'app_client_id') else None,
        'user_pool_id': config[key].user_pool_id() if hasattr(config[key], 'user_pool_id') else None,
        'is_primary': i == 0,  # First config is primary
        'is_available': False
    }
    try:
        cfg['defaultUser'] = config[key].defaultUser()
    except:
        cfg['defaultUser'] = None
    
    # Check database availability
    is_available = check_database_availability(cfg['dbUrl'])
    cfg['is_available'] = is_available
    
    if i == 0 and not is_available:
        # Primary database is not available - stop the application
        logger.error(f"Primary database {key} is not available. Stopping application.")
        sys.exit(1)
    
    all_configs.append(cfg)
    
    if is_available:
        available_configs.append(cfg)
        logger.info(f"Database {key} is available")
    else:
        logger.warning(f"Database {key} is not available and will be skipped")

try:
    default_user = config[primary_config_key].defaultUser()
except:
    default_user = None
print("dbSchema: {}".format(dbSchema))
print("testing: ", test_table)
print("all_configs: {}".format([cfg['key'] for cfg in all_configs]))
print("available_configs: {}".format([cfg['key'] for cfg in available_configs]))

try:
    load_data_from_csv = config.development.loadDataFromCsv()
except Exception:
    pass
try:
    log_level = config.development.logLevel().upper()
except Exception:
    pass
