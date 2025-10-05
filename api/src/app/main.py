from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import threading
import app.db.data_loader.loader as loader
from app.db.database import Database
from app.db.database_grafana_connector import DatabaseGrafanaConnector
from app.api.source_objects import entity as entity_api
from app.api.source_objects import tag_def as tag_def_api
from app.api.source_objects import tag_meta as tag_meta_api
from app.api.source_objects import tag_enum as tag_enum_api
from app.api.source_objects import entity_tag as entity_tag_api
from app.api.acl.user import app_user as app_user_api
from app.api.acl.user import user as user_api
from app.api.source_objects import filter as filter_api
from app.api.acl.user import user_entity_add_permission as user_entity_add_permission_api
from app.api.acl.user import user_entity_rev_permission as user_entity_rev_permission_api
from app.api.acl.user import user_tag_add_permission as user_tag_add_permission_api
from app.api.acl.user import user_tag_rev_permission as user_tag_rev_permission_api
from app.api.acl.org import org as org_api
from app.api.acl.org import org_entity_permission as org_entity_permission_api
from app.api.acl.org import org_tag_permission as org_tag_permission_api
#from app.api.exporter import exporter_api as exporter_api
from app.api.views import tag_def_parents as tag_def_parents_api
from app.api.auth import auth
from app.api import system as system_api
from app.api.source_objects import value as value_api
from app.api.source_objects import report as report_api
from app.api.poller_config import poller_config as poller_config_api
from app.api.uploaded_files import uploaded_files as uploaded_files_api
from app.api.source_objects import fleet_report as fleet_report_api
from app.model.sqlalchemy import source_object_model, history_model, aggregate_model, acl_org_model, acl_user_model, tag_def_parents_model
import uuid
from app.model.sqlalchemy.base import Base
from app.services import config_service
from app.services import logger_service as lg
from app.services.acl import user_service
import logging
from app.model.sqlalchemy import values_tables
from app.model.sqlalchemy import core_ess_table
from app.model.sqlalchemy import core_renu_table
from app.model.sqlalchemy import dynamic_value_tables

lg.logger(
    fileName="app.log",
    level=config_service.log_level,
    format="%(asctime)s\t%(levelname)s\t%(threadName)s" "\t[%(filename)s.%(funcName)s:%(lineno)d]\t%(message)s",
)

logger = logging.getLogger(__name__)
database = Database(config_service.database, config_service.main_db_pool_size, config_service.main_db_max_overflow)
database.init_database()
database_grafana_connector = DatabaseGrafanaConnector(config_service.database_grafana_connector, config_service.grafana_db_pool_size, config_service.grafana_db_max_overflow)
database_grafana_connector.init_database()

def log_connection_stats_periodically():
    """Background task to log connection stats every 2 minutes"""
    def run_logging():
        while True:
            try:
                database_grafana_connector.log_connection_stats()
                database.log_connection_stats()
            except Exception as e:
                logger.error(f"Error logging connection stats: {str(e)}")
            threading.Event().wait(900)  # Wait 2 minutes (120 seconds)
    
    # Start the background thread
    thread = threading.Thread(target=run_logging, daemon=True)
    thread.start()
    logger.info("Started background connection stats logging (every 2 minutes)")

# Start connection stats logging
log_connection_stats_periodically()

# Initialize databases only for available configs
all_databases = []
for config in config_service.available_configs:
    try:
        db = Database(config['dbUrl'], config_service.main_db_pool_size, config_service.main_db_max_overflow)
        db.init_database()
        all_databases.append({
            'key': config['key'],
            'database': db,
            'dbSchema': config['dbScheme'],
            'is_primary': config['is_primary'],
            'is_available': config['is_available']
        })
        logger.info(f"Successfully initialized database connection for {config['key']}")
    except Exception as e:
        if config['is_primary']:
            logger.error(f"Failed to initialize primary database {config['key']}: {str(e)}")
            raise e  # Stop application if primary database fails
        else:
            logger.warning(f"Failed to initialize secondary database {config['key']}: {str(e)}. Continuing without it.")
# tag_def_parents_model.create_views(database.get_engine())
# Base.metadata.create_all(bind=database.get_engine())  # Schema already created by SQL initialization files

values_tables.getMapOfValueTables(database.get_local_session())
core_renu_table.getMapOfCoreRenuTable(database.get_local_session())
core_ess_table.getMapOfCoreEssTable(database.get_local_session())
dynamic_value_tables.getMapOfTestValuesTable(database.get_local_session())

load_data_from_csv = config_service.load_data_from_csv
if load_data_from_csv:
    dataLoader = loader.DataLoader(database).load()
app = FastAPI()

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request_id = str(uuid.uuid4())
        request.state.db = database.get_local_session()
        request.state.db_grafana_connector = database_grafana_connector.get_local_session()
        request.state.all_databases = all_databases
        request.state.request_id = request_id
        request.state.user_id = 0 if "/health" in str(request.url) or  "/authorize/token" in str(request.url)  else user_service.get_current_user(request, request.state.db, config_service.default_user)
        request.state.default_user_id = config_service.default_user
        response = await call_next(request)
        response.headers["dq-request-id"] = request_id
    except HTTPException as http_exc:
        # Convert HTTP exceptions to proper JSON responses
        response = JSONResponse(
            status_code=http_exc.status_code,
            content={"detail": http_exc.detail}
        )
        response.headers["dq-request-id"] = request_id
    except Exception as e:
        logger.error({"request_id": request_id, "detail": str(e)})
    finally:
        request.state.db.close()
        request.state.db_grafana_connector.close()
    return response


def get_db(request: Request):
    return request.state.db


def get_db_grafana_connector(request: Request):
    return request.state.db_grafana_connector


entity_api.init(app, get_db)
tag_def_api.init(app, get_db)
tag_meta_api.init(app, get_db)
entity_tag_api.init(app, get_db)
filter_api.init(app, get_db_grafana_connector)
tag_enum_api.init(app, get_db)
app_user_api.init(app, get_db)
user_api.init(app, get_db)
user_entity_add_permission_api.init(app, get_db)
user_entity_rev_permission_api.init(app, get_db)
user_tag_add_permission_api.init(app, get_db)
user_tag_rev_permission_api.init(app, get_db)
org_api.init(app, get_db)
org_entity_permission_api.init(app, get_db)
org_tag_permission_api.init(app, get_db)
value_api.init(app, get_db)
report_api.init(app, get_db)
poller_config_api.init(app, get_db)
uploaded_files_api.init(app, get_db)
fleet_report_api.init(app, get_db)
system_api.init(app)
tag_def_parents_api.init(app, get_db)
#exporter_api.init(app, get_db)
auth.init(app)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8087)
