import logging
from fastapi import Depends, HTTPException, Request
import json
from app.api.filter.antlr.antlr_error_listener import AntlrError
from app.services import config_service
from sqlalchemy import text
import traceback

logger = logging.getLogger(__name__)
def init(app):
    @app.get("/health", status_code=200)
    def get_app_health():
        return {"status":"ok"}

    @app.get("/health/databases", status_code=200)
    def get_database_health(request: Request):
        """Check health status of all configured databases"""
        database_status = []
        overall_status = "healthy"
        
        try:
            all_databases = request.state.all_databases
            
            for db_config in all_databases:
                db_status = {
                    "key": db_config["key"],
                    "is_primary": db_config.get("is_primary", False),
                    "status": "unknown",
                    "error": None
                }
                
                try:
                    # Test database connection
                    db_session = db_config['database'].get_local_session()
                    db_session.execute(text("SELECT 1"))
                    db_session.close()
                    db_status["status"] = "healthy"
                    
                except Exception as e:
                    db_status["status"] = "unhealthy" 
                    db_status["error"] = str(e)
                    
                    # If primary database is unhealthy, overall status is critical
                    if db_config.get("is_primary", False):
                        overall_status = "critical"
                    elif overall_status == "healthy":
                        overall_status = "degraded"
                        
                database_status.append(db_status)
                
        except Exception as e:
            logger.error(f"Error checking database health: {str(e)}")
            return {
                "overall_status": "error",
                "error": str(e),
                "databases": []
            }
            
        return {
            "overall_status": overall_status,
            "databases": database_status,
            "total_databases": len(database_status),
            "healthy_databases": len([db for db in database_status if db["status"] == "healthy"]),
            "config_keys": config_service.config_keys,
            "available_config_keys": [cfg['key'] for cfg in config_service.available_configs]
        }


