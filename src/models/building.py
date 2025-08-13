"""Building system data models."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EquipmentStatus(Enum):
    """Equipment operational status."""
    OFF = "off"
    ON = "on"
    FAULT = "fault"
    MAINTENANCE = "maintenance"
    STARTING = "starting"
    STOPPING = "stopping"


class DataStatus(Enum):
    """Data quality status."""
    OK = "ok"
    STALE = "stale"
    FAULT = "fault"
    UNKNOWN = "unknown"


@dataclass
class Site:
    """Building site model."""
    id: str
    name: str
    area: float
    area_unit: str = "ft²"
    address: str = ""
    timezone: str = "America/New_York"
    year_built: int = 2020
    floors: int = 1
    primary_function: str = "office"
    weather_station_ref: str = ""
    
    def to_haystack_tags(self) -> Dict[str, Any]:
        """Convert to Project Haystack tags."""
        return {
            "id": self.id,
            "dis": self.name,
            "site": True,
            "area": self.area,
            "areaUnit": self.area_unit,
            "geoAddr": self.address,
            "tz": self.timezone,
            "yearBuilt": self.year_built,
            "floors": self.floors,
            "primaryFunction": self.primary_function,
            "weatherStationRef": self.weather_station_ref
        }


@dataclass 
class Equipment:
    """Base equipment model."""
    id: str
    name: str
    site_ref: str
    equipment_type: str
    manufacturer: str = ""
    model: str = ""
    install_date: Optional[datetime] = None
    status: EquipmentStatus = EquipmentStatus.OFF
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def to_haystack_tags(self) -> Dict[str, Any]:
        """Convert to Project Haystack tags."""
        base_tags = {
            "id": self.id,
            "dis": self.name,
            "equip": True,
            "siteRef": self.site_ref,
            self.equipment_type: True
        }
        
        if self.manufacturer:
            base_tags["manufacturer"] = self.manufacturer
        if self.model:
            base_tags["model"] = self.model
        if self.install_date:
            base_tags["installDate"] = self.install_date.strftime("%Y-%m-%d")
            
        # Add custom tags
        base_tags.update(self.tags)
        
        return base_tags


@dataclass
class Point:
    """Sensor/control point model."""
    id: str
    name: str
    site_ref: str
    equip_ref: str
    kind: str  # "Bool", "Number", "Str"
    unit: Optional[str] = None
    writable: bool = False
    tags: Dict[str, Any] = field(default_factory=dict)
    current_value: Any = None
    current_status: DataStatus = DataStatus.OK
    last_update: Optional[datetime] = None
    
    def to_haystack_tags(self) -> Dict[str, Any]:
        """Convert to Project Haystack tags."""
        base_tags = {
            "id": self.id,
            "dis": self.name,
            "point": True,
            "siteRef": self.site_ref,
            "equipRef": self.equip_ref,
            "kind": self.kind
        }
        
        if self.unit:
            base_tags["unit"] = self.unit
        if self.writable:
            base_tags["writable"] = True
            
        # Add sensor/cmd tags
        if not self.writable:
            base_tags["sensor"] = True
        else:
            base_tags["cmd"] = True
            
        # Add custom tags
        base_tags.update(self.tags)
        
        return base_tags
        
    def update_value(self, value: Any, status: DataStatus = DataStatus.OK, 
                    timestamp: Optional[datetime] = None):
        """Update point value."""
        self.current_value = value
        self.current_status = status
        self.last_update = timestamp or datetime.now()


@dataclass
class DataPoint:
    """Time-series data point."""
    entity_id: int
    timestamp: datetime
    value_n: Optional[float] = None
    value_b: Optional[bool] = None
    value_s: Optional[str] = None
    status: DataStatus = DataStatus.OK
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'entity_id': self.entity_id,
            'ts': self.timestamp,
            'value_n': self.value_n,
            'value_b': self.value_b,
            'value_s': self.value_s,
            'status': self.status.value
        }


@dataclass
class BuildingSystem:
    """Complete building system model."""
    site: Site
    equipment: List[Equipment] = field(default_factory=list)
    points: List[Point] = field(default_factory=list)
    
    def add_equipment(self, equip: Equipment):
        """Add equipment to building system."""
        self.equipment.append(equip)
        
    def add_point(self, point: Point):
        """Add point to building system."""
        self.points.append(point)
        
    def get_equipment_by_type(self, equip_type: str) -> List[Equipment]:
        """Get equipment by type."""
        return [eq for eq in self.equipment if eq.equipment_type == equip_type]
        
    def get_points_by_equipment(self, equip_id: str) -> List[Point]:
        """Get points for specific equipment."""
        return [pt for pt in self.points if pt.equip_ref == equip_id]
        
    def get_total_entities(self) -> int:
        """Get total number of entities (site + equipment + points)."""
        return 1 + len(self.equipment) + len(self.points)