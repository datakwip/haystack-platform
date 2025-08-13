"""Database schema setup for Haystack entities."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaSetup:
    """Manages database schema and entity structure."""
    
    def __init__(self, db_connection):
        """Initialize schema setup with database connection.
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db = db_connection
        self.org_id = None
        
    def initialize_organization(self, org_name: str = "Demo Building Corp", 
                              org_key: str = "demo") -> int:
        """Initialize organization for the simulation.
        
        Args:
            org_name: Organization name
            org_key: Organization key
            
        Returns:
            Organization ID
        """
        self.org_id = self.db.create_organization(org_name, org_key)
        return self.org_id
        
    def create_entity(self, tags: Dict[str, Any], value_table_id: str = "demo") -> int:
        """Create an entity in the database.
        
        Args:
            tags: Dictionary of Haystack tags for the entity
            value_table_id: Value table identifier
            
        Returns:
            Entity ID
        """
        # Insert entity
        query = "INSERT INTO core.entity (value_table_id) VALUES (%s) RETURNING id"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (value_table_id,))
                entity_id = cur.fetchone()[0]
                
        # Add tags
        self._add_entity_tags(entity_id, tags)
        
        # Add organization permission
        if self.org_id:
            self._add_org_permission(entity_id)
            
        logger.info(f"Created entity {entity_id} with {len(tags)} tags")
        return entity_id
        
    def _add_entity_tags(self, entity_id: int, tags: Dict[str, Any]):
        """Add tags to an entity.
        
        Args:
            entity_id: Entity ID
            tags: Dictionary of tags to add
        """
        # First ensure tag definitions exist
        for tag_name in tags.keys():
            self._ensure_tag_def(tag_name)
            
        # Add tag values
        for tag_name, value in tags.items():
            self._add_tag_value(entity_id, tag_name, value)
            
    def _ensure_tag_def(self, tag_name: str) -> int:
        """Ensure tag definition exists in database.
        
        Args:
            tag_name: Tag name
            
        Returns:
            Tag definition ID
        """
        # Check if tag exists
        query = "SELECT id FROM core.tag_def WHERE name = %s"
        result = self.db.execute_query(query, (tag_name,))
        
        if result:
            return result[0]['id']
            
        # Create new tag definition
        query = "INSERT INTO core.tag_def (name) VALUES (%s) RETURNING id"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tag_name,))
                return cur.fetchone()[0]
                
    def _add_tag_value(self, entity_id: int, tag_name: str, value: Any):
        """Add a tag value to an entity.
        
        Args:
            entity_id: Entity ID
            tag_name: Tag name
            value: Tag value
        """
        # Get tag ID
        tag_id = self._ensure_tag_def(tag_name)
        
        # Determine value column based on type
        value_cols = {
            'value_n': None,
            'value_b': None,
            'value_s': None,
            'value_ts': None,
            'value_ref': None,
            'value_dict': None
        }
        
        if isinstance(value, bool):
            value_cols['value_b'] = value
        elif isinstance(value, (int, float)):
            value_cols['value_n'] = value
        elif isinstance(value, datetime):
            value_cols['value_ts'] = value
        elif isinstance(value, dict):
            value_cols['value_dict'] = value
        elif isinstance(value, str):
            # Check if it's a reference
            if value.startswith('@') or value.endswith('Ref'):
                # For now, store refs as strings
                value_cols['value_s'] = value
            else:
                value_cols['value_s'] = value
        else:
            value_cols['value_s'] = str(value)
            
        # Insert tag value
        query = """
            INSERT INTO core.entity_tag 
            (entity_id, tag_id, value_n, value_b, value_s, value_ts, value_dict, value_ref)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            entity_id, tag_id,
            value_cols['value_n'], value_cols['value_b'], value_cols['value_s'],
            value_cols['value_ts'], value_cols['value_dict'], value_cols['value_ref']
        )
        self.db.execute_update(query, params)
        
    def _add_org_permission(self, entity_id: int):
        """Add organization permission for entity.
        
        Args:
            entity_id: Entity ID
        """
        if not self.org_id:
            return
            
        query = """
            INSERT INTO core.org_entity_permission (org_id, entity_id)
            VALUES (%s, %s)
            ON CONFLICT (org_id, entity_id) DO NOTHING
        """
        self.db.execute_update(query, (self.org_id, entity_id))
        
    def create_value_tables(self, table_suffix: str = "demo"):
        """Create value tables if they don't exist.
        
        Args:
            table_suffix: Suffix for table names
        """
        tables = [
            f"""
            CREATE TABLE IF NOT EXISTS core.values_{table_suffix} (
                entity_id int4 NOT NULL,
                ts timestamp DEFAULT now() NOT NULL,
                value_n numeric NULL,
                value_b bool NULL,
                value_s varchar NULL,
                value_ts timestamp NULL,
                value_dict jsonb NULL,
                status varchar NULL,
                CONSTRAINT values_{table_suffix}_pkey PRIMARY KEY (entity_id, ts)
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS core.values_{table_suffix}_current (
                entity_id int4 NOT NULL,
                ts timestamp DEFAULT now() NOT NULL,
                value_n numeric NULL,
                value_b bool NULL,
                value_s varchar NULL,
                value_ts timestamp NULL,
                value_dict jsonb NULL,
                status varchar NULL,
                CONSTRAINT values_{table_suffix}_current_pkey PRIMARY KEY (entity_id)
            )
            """
        ]
        
        for query in tables:
            try:
                self.db.execute_update(query)
                logger.info(f"Created/verified value table")
            except Exception as e:
                logger.warning(f"Table creation failed (may exist): {e}")
                
    def get_entity_by_tag(self, tag_name: str, tag_value: str) -> Optional[int]:
        """Get entity ID by tag name and value.
        
        Args:
            tag_name: Tag name to search
            tag_value: Tag value to match
            
        Returns:
            Entity ID if found, None otherwise
        """
        query = """
            SELECT et.entity_id 
            FROM core.entity_tag et
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = %s AND et.value_s = %s
            LIMIT 1
        """
        result = self.db.execute_query(query, (tag_name, tag_value))
        return result[0]['entity_id'] if result else None