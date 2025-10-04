from app.services import logger_service as lg,  config_service
from app.services.export.services import hierarchy_service, xls_service, entity_service
from app.services.export.services import sql_service
import logging
import psycopg2
import argparse
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Export data from Rally into CSV file(s)")
parser.add_argument(
    "-e", "--environment", help="Rally environment, section must exist in configuration file.", default="DEFAULT"
)
parser.add_argument(
    "-c",
    "--config",
    help="Configuration file in INI format. See `Rally exporter parameters.md` for details.",
    default="config.ini",
)
args = parser.parse_args()


lg.logger(
    fileName="app.log",
    level=config_service.log_level,
    format="%(asctime)s\t%(levelname)s\t%(threadName)s" "\t[%(filename)s.%(funcName)s:%(lineno)d]\t%(message)s", # noqa: 501
)

schema="core"
def export_data(org_id):
    logger.info("export started...")
    result = urlparse(config_service.database)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    conn = psycopg2.connect(
    database = database,
    user = username,
    password = password,
    host = hostname,
    port = port
)
    try:
        tags = sql_service.getTagsBySql(conn, schema)
        entity_refs =entity_service.get_entity_refs(conn, org_id, schema)
        tag_hierarchy=hierarchy_service.get_tag_hierarchy(conn, org_id, schema)
        hierarchy = hierarchy_service.get_entity_hierarchy(conn, org_id, tag_hierarchy, schema)
        return xls_service.createXLSFile(hierarchy, conn, org_id, tags, entity_refs, schema, tag_hierarchy)
    except Exception as e:
        logger.error(e)
        conn.close()

