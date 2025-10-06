"""
Haystack Definitions Importer Service

Downloads and imports official Project Haystack tag definitions from
https://project-haystack.org into the TimescaleDB database.

Imports:
- Libraries (lib:ph, lib:phIoT, lib:phScience, lib:phIct)
- Tag definitions (site, equip, point, temp, etc.)
- Tag metadata (lib associations)
- Org permissions (grants simulator org access to all libraries)
"""

import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HaystackDefsImporter:
    """Imports Project Haystack definitions into database."""

    DEFS_URL = "https://project-haystack.org/download/defs.json"

    def __init__(self, db):
        """
        Initialize importer.

        Args:
            db: Database connection instance
        """
        self.db = db

    def should_import(self) -> bool:
        """
        Check if definitions need to be imported.

        Returns:
            True if import is needed, False if already imported
        """
        query = """
            SELECT COUNT(*) as count
            FROM core.tag_def
            WHERE name IN ('ph', 'phIoT', 'phScience', 'phIct')
            AND disabled_ts IS NULL
        """
        result = self.db.execute_query(query)

        if result and result[0]['count'] >= 4:
            logger.info("Project Haystack definitions already imported")
            return False

        logger.info("Project Haystack definitions not found, will import")
        return True

    def download_definitions(self) -> Dict[str, Any]:
        """
        Download definitions from Project Haystack website.

        Returns:
            Parsed JSON dictionary

        Raises:
            Exception if download fails
        """
        logger.info(f"Downloading definitions from {self.DEFS_URL}")

        try:
            response = requests.get(self.DEFS_URL, timeout=30)
            response.raise_for_status()
            data = response.json()

            logger.info(f"Downloaded {len(data.get('rows', []))} definitions")
            return data

        except Exception as e:
            logger.error(f"Failed to download definitions: {e}")
            raise

    def extract_value(self, field: Any) -> Any:
        """
        Extract value from Haystack JSON field.

        Haystack JSON uses format: {"_kind": "symbol", "val": "value"}

        Args:
            field: Field from JSON (could be dict with _kind, or simple value)

        Returns:
            Extracted value
        """
        if isinstance(field, dict) and 'val' in field:
            return field['val']
        return field

    def parse_library(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a library definition row.

        Args:
            row: JSON row from defs.json

        Returns:
            Library dict or None if not a library
        """
        def_val = self.extract_value(row.get('def'))

        if not def_val or not isinstance(def_val, str) or not def_val.startswith('lib:'):
            return None

        # Extract library name (remove "lib:" prefix)
        lib_name = def_val[4:]  # Remove "lib:" prefix

        return {
            'name': lib_name,
            'doc': self.extract_value(row.get('doc')),
            'dis': self.extract_value(row.get('dis')),
            'version': self.extract_value(row.get('version')),
            'base_uri': self.extract_value(row.get('baseUri')),
        }

    def parse_tag(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a tag definition row.

        Args:
            row: JSON row from defs.json

        Returns:
            Tag dict or None if this is a library row
        """
        def_val = self.extract_value(row.get('def'))

        if not def_val or not isinstance(def_val, str):
            return None

        # Skip library definitions
        if def_val.startswith('lib:'):
            return None

        # Extract lib reference if present
        lib_ref = None
        if 'lib' in row:
            lib_val = self.extract_value(row.get('lib'))
            if lib_val and lib_val.startswith('lib:'):
                lib_ref = lib_val[4:]  # Remove "lib:" prefix

        return {
            'name': def_val,
            'doc': self.extract_value(row.get('doc')),
            'dis': self.extract_value(row.get('dis')),
            'url': self.extract_value(row.get('url')),
            'version': self.extract_value(row.get('version')),
            'lib': lib_ref,
        }

    def import_library(self, lib: Dict[str, Any]) -> int:
        """
        Import a library definition into core.tag_def.

        Args:
            lib: Library dictionary

        Returns:
            Library tag_def ID
        """
        # Check if already exists
        query = "SELECT id FROM core.tag_def WHERE name = %s AND disabled_ts IS NULL"
        result = self.db.execute_query(query, (lib['name'],))

        if result:
            logger.debug(f"Library '{lib['name']}' already exists")
            return result[0]['id']

        # Insert library
        query = """
            INSERT INTO core.tag_def (name, doc, dis, version, base_uri)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    lib['name'],
                    lib['doc'],
                    lib['dis'],
                    lib['version'],
                    lib['base_uri']
                ))
                lib_id = cur.fetchone()[0]

        logger.info(f"Imported library: {lib['name']} (ID: {lib_id})")
        return lib_id

    def import_tag(self, tag: Dict[str, Any], lib_name_to_id: Dict[str, int]) -> int:
        """
        Import a tag definition into core.tag_def and core.tag_meta.

        Args:
            tag: Tag dictionary
            lib_name_to_id: Mapping of library names to tag_def IDs

        Returns:
            Tag tag_def ID
        """
        # Check if already exists
        query = "SELECT id FROM core.tag_def WHERE name = %s AND disabled_ts IS NULL"
        result = self.db.execute_query(query, (tag['name'],))

        if result:
            tag_id = result[0]['id']
            logger.debug(f"Tag '{tag['name']}' already exists")
        else:
            # Insert tag definition
            query = """
                INSERT INTO core.tag_def (name, doc, dis, url, version)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """

            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (
                        tag['name'],
                        tag['doc'],
                        tag['dis'],
                        tag['url'],
                        tag['version']
                    ))
                    tag_id = cur.fetchone()[0]

            logger.debug(f"Imported tag: {tag['name']} (ID: {tag_id})")

        # Add lib metadata if present
        if tag['lib'] and tag['lib'] in lib_name_to_id:
            self.add_lib_metadata(tag_id, tag['lib'], lib_name_to_id[tag['lib']])

        return tag_id

    def add_lib_metadata(self, tag_id: int, lib_name: str, lib_tag_id: int):
        """
        Add lib metadata to core.tag_meta.

        Args:
            tag_id: Tag definition ID
            lib_name: Library name (for logging)
            lib_tag_id: Library tag_def ID (value to store)
        """
        # Get the tag_def ID for "lib" attribute first
        lib_attr_query = "SELECT id FROM core.tag_def WHERE name = 'lib' AND disabled_ts IS NULL"
        lib_attr_result = self.db.execute_query(lib_attr_query)

        if not lib_attr_result:
            # Create "lib" tag if it doesn't exist
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO core.tag_def (name, doc) VALUES (%s, %s) RETURNING id",
                        ('lib', 'Defines the library a tag belongs to')
                    )
                    lib_attr_id = cur.fetchone()[0]
        else:
            lib_attr_id = lib_attr_result[0]['id']

        # Check if metadata already exists
        query = """
            SELECT id FROM core.tag_meta
            WHERE tag_id = %s AND attribute = %s AND disabled_ts IS NULL
        """
        result = self.db.execute_query(query, (tag_id, lib_attr_id))

        if result:
            logger.debug(f"Tag {tag_id} already has lib metadata")
            return

        # Insert tag_meta entry
        query = """
            INSERT INTO core.tag_meta (tag_id, attribute, value)
            VALUES (%s, %s, %s)
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (tag_id, lib_attr_id, str(lib_tag_id)))

        logger.debug(f"Added lib={lib_name} metadata to tag {tag_id}")

    def grant_org_permissions(self, org_id: int, lib_ids: List[int]):
        """
        Grant organization permissions to use imported libraries.

        Args:
            org_id: Organization ID
            lib_ids: List of library tag_def IDs
        """
        logger.info(f"Granting org {org_id} access to {len(lib_ids)} libraries")

        for lib_id in lib_ids:
            # Check if permission already exists
            query = """
                SELECT id FROM core.org_tag_permission
                WHERE org_id = %s AND tag_id = %s
            """
            result = self.db.execute_query(query, (org_id, lib_id))

            if result:
                logger.debug(f"Org {org_id} already has permission for lib {lib_id}")
                continue

            # Insert permission
            query = """
                INSERT INTO core.org_tag_permission (org_id, tag_id)
                VALUES (%s, %s)
            """

            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (org_id, lib_id))

            logger.debug(f"Granted org {org_id} permission for lib {lib_id}")

    def import_all(self, org_id: int):
        """
        Import all Haystack definitions and grant org permissions.

        Args:
            org_id: Organization ID to grant library permissions
        """
        if not self.should_import():
            return

        logger.info("Starting Project Haystack definitions import")

        # Download definitions
        data = self.download_definitions()
        rows = data.get('rows', [])

        # Parse libraries and tags
        libraries = []
        tags = []

        for row in rows:
            lib = self.parse_library(row)
            if lib:
                libraries.append(lib)
            else:
                tag = self.parse_tag(row)
                if tag:
                    tags.append(tag)

        logger.info(f"Parsed {len(libraries)} libraries and {len(tags)} tag definitions")

        # Import libraries first
        lib_name_to_id = {}
        lib_ids = []

        for lib in libraries:
            lib_id = self.import_library(lib)
            lib_name_to_id[lib['name']] = lib_id
            lib_ids.append(lib_id)

        logger.info(f"Imported {len(libraries)} libraries")

        # Import tags
        tag_count = 0
        for tag in tags:
            self.import_tag(tag, lib_name_to_id)
            tag_count += 1

            # Log progress every 100 tags
            if tag_count % 100 == 0:
                logger.info(f"Imported {tag_count}/{len(tags)} tags...")

        logger.info(f"Imported {tag_count} tag definitions")

        # Grant org permissions
        self.grant_org_permissions(org_id, lib_ids)

        logger.info("✓ Project Haystack definitions import complete")


def import_haystack_definitions(db, org_id: int):
    """
    Convenience function to import Haystack definitions.

    Args:
        db: Database connection
        org_id: Organization ID to grant permissions
    """
    importer = HaystackDefsImporter(db)
    importer.import_all(org_id)
