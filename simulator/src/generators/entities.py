"""Entity generators for Project Haystack compliant building entities."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EntityGenerator:
    """Generates Project Haystack compliant entities."""
    
    def __init__(self, schema_setup, config: Dict[str, Any]):
        """Initialize entity generator.
        
        Args:
            schema_setup: SchemaSetup instance
            config: Building configuration dictionary
        """
        self.schema = schema_setup
        self.config = config
        self.entity_map = {}  # Store entity IDs for references
        
    def generate_all_entities(self) -> Dict[str, int]:
        """Generate all building entities.
        
        Returns:
            Dictionary mapping entity names to IDs
        """
        logger.info("Starting entity generation...")
        
        # Generate site
        site_id = self.generate_site()
        
        # Generate chillers
        chiller_ids = self.generate_chillers()
        
        # Generate AHUs
        ahu_ids = self.generate_ahus()
        
        # Generate VAV boxes
        vav_ids = self.generate_vav_boxes()
        
        # Generate meters
        meter_ids = self.generate_meters()
        
        # Generate points for all equipment
        point_ids = self.generate_all_points()
        
        logger.info(f"Entity generation complete. Created {len(self.entity_map)} entities")
        return self.entity_map
        
    def generate_site(self) -> int:
        """Generate site entity.
        
        Returns:
            Site entity ID
        """
        site_config = self.config['site']
        
        site_tags = {
            "id": site_config['id'],
            "dis": site_config['name'],
            "site": True,
            "area": site_config['area'],
            "areaUnit": site_config['area_unit'],
            "geoAddr": site_config['address'],
            "tz": site_config['timezone'],
            "yearBuilt": site_config['year_built'],
            "primaryFunction": site_config['primary_function'],
            "occupancy": site_config['occupancy_type'],
            "weatherStationRef": site_config['weather_station'],
            "floors": site_config['floors']
        }
        
        site_id = self.schema.create_entity(site_tags)
        self.entity_map['site'] = site_id
        self.entity_map[site_config['id']] = site_id
        
        logger.info(f"Created site entity: {site_config['name']} (ID: {site_id})")
        return site_id
        
    def generate_chillers(self) -> List[int]:
        """Generate chiller entities.
        
        Returns:
            List of chiller entity IDs
        """
        chiller_config = self.config['equipment']['chillers']
        site_ref = self.config['site']['id']
        chiller_ids = []
        
        for i in range(1, chiller_config['count'] + 1):
            chiller_tags = {
                "id": f"equip-chiller-{i}",
                "dis": f"Chiller #{i} - {'Primary' if i == 1 else 'Backup'}",
                "equip": True,
                "chiller": True,
                "siteRef": site_ref,
                "cooling": True,
                "coolingCapacity": chiller_config['capacity'],
                "coolingCapacityUnit": "tonRefrig",
                "manufacturer": chiller_config['manufacturer'],
                "model": chiller_config['model'],
                "installDate": "2018-03-15",
                "primaryEquip": (i == 1)
            }
            
            chiller_id = self.schema.create_entity(chiller_tags)
            chiller_ids.append(chiller_id)
            self.entity_map[f"chiller-{i}"] = chiller_id
            self.entity_map[f"equip-chiller-{i}"] = chiller_id
            
            logger.info(f"Created chiller entity: Chiller #{i} (ID: {chiller_id})")
            
        return chiller_ids
        
    def generate_ahus(self) -> List[int]:
        """Generate Air Handling Unit entities.
        
        Returns:
            List of AHU entity IDs
        """
        ahu_config = self.config['equipment']['ahus']
        site_ref = self.config['site']['id']
        ahu_ids = []
        
        floors_per_ahu = ahu_config['floors_per_ahu']
        total_floors = self.config['site']['floors']
        
        for i in range(1, ahu_config['count'] + 1):
            start_floor = (i - 1) * floors_per_ahu + 1
            end_floor = min(i * floors_per_ahu, total_floors)
            
            ahu_tags = {
                "id": f"equip-ahu-{i}",
                "dis": f"AHU-{i} Floors {start_floor}-{end_floor}",
                "equip": True,
                "ahu": True,
                "siteRef": site_ref,
                "airHandling": True,
                "manufacturer": ahu_config['manufacturer'],
                "model": ahu_config['model'],
                "chilledWaterRef": "equip-chiller-1",  # Primary chiller
                "floorsServed": f"{start_floor}-{end_floor}",
                "startFloor": start_floor,
                "endFloor": end_floor
            }
            
            ahu_id = self.schema.create_entity(ahu_tags)
            ahu_ids.append(ahu_id)
            self.entity_map[f"ahu-{i}"] = ahu_id
            self.entity_map[f"equip-ahu-{i}"] = ahu_id
            
            logger.info(f"Created AHU entity: AHU-{i} (ID: {ahu_id})")
            
        return ahu_ids
        
    def generate_vav_boxes(self) -> List[int]:
        """Generate VAV box entities.
        
        Returns:
            List of VAV entity IDs
        """
        vav_config = self.config['equipment']['vav_boxes']
        site_ref = self.config['site']['id']
        vav_ids = []
        
        total_floors = self.config['site']['floors']
        floors_per_ahu = self.config['equipment']['ahus']['floors_per_ahu']
        
        for floor in range(1, total_floors + 1):
            # Determine which AHU serves this floor
            ahu_num = ((floor - 1) // floors_per_ahu) + 1
            ahu_ref = f"equip-ahu-{ahu_num}"
            
            for zone in vav_config['zones']:
                vav_id_str = f"equip-vav-{floor}-{zone.lower()}"
                
                vav_tags = {
                    "id": vav_id_str,
                    "dis": f"VAV-{floor}{zone[0]} Floor {floor} {zone}",
                    "equip": True,
                    "vav": True,
                    "siteRef": site_ref,
                    "ahuRef": ahu_ref,
                    "floor": floor,
                    "zone": zone.lower(),
                    "airTerminalUnit": True,
                    "maxAirFlow": self.config['performance']['vav']['max_flow_cfm'],
                    "minFlowRatio": self.config['performance']['vav']['min_flow_ratio']
                }
                
                vav_id = self.schema.create_entity(vav_tags)
                vav_ids.append(vav_id)
                self.entity_map[vav_id_str] = vav_id
                
                logger.debug(f"Created VAV entity: {vav_id_str} (ID: {vav_id})")
                
        logger.info(f"Created {len(vav_ids)} VAV box entities")
        return vav_ids
        
    def generate_meters(self) -> List[int]:
        """Generate utility meter entities.
        
        Returns:
            List of meter entity IDs
        """
        meters_config = self.config['equipment']['meters']
        site_ref = self.config['site']['id']
        meter_ids = []
        
        # Electric meter
        electric_tags = {
            "id": meters_config['electric']['id'],
            "dis": meters_config['electric']['name'],
            "equip": True,
            "meter": True,
            "elec": True,
            "siteRef": site_ref,
            "submeterOf": site_ref
        }
        electric_id = self.schema.create_entity(electric_tags)
        meter_ids.append(electric_id)
        self.entity_map[meters_config['electric']['id']] = electric_id
        
        # Gas meter
        gas_tags = {
            "id": meters_config['gas']['id'],
            "dis": meters_config['gas']['name'],
            "equip": True,
            "meter": True,
            "gas": True,
            "siteRef": site_ref,
            "submeterOf": site_ref
        }
        gas_id = self.schema.create_entity(gas_tags)
        meter_ids.append(gas_id)
        self.entity_map[meters_config['gas']['id']] = gas_id
        
        # Water meter
        water_tags = {
            "id": meters_config['water']['id'],
            "dis": meters_config['water']['name'],
            "equip": True,
            "meter": True,
            "water": True,
            "siteRef": site_ref,
            "submeterOf": site_ref
        }
        water_id = self.schema.create_entity(water_tags)
        meter_ids.append(water_id)
        self.entity_map[meters_config['water']['id']] = water_id
        
        logger.info(f"Created {len(meter_ids)} meter entities")
        return meter_ids
        
    def generate_all_points(self) -> List[int]:
        """Generate all point entities for equipment.
        
        Returns:
            List of all point entity IDs
        """
        point_ids = []
        
        # Generate chiller points
        point_ids.extend(self._generate_chiller_points())
        
        # Generate AHU points
        point_ids.extend(self._generate_ahu_points())
        
        # Generate VAV points
        point_ids.extend(self._generate_vav_points())
        
        # Generate meter points
        point_ids.extend(self._generate_meter_points())
        
        logger.info(f"Created {len(point_ids)} point entities")
        return point_ids
        
    def _generate_chiller_points(self) -> List[int]:
        """Generate points for all chillers."""
        point_ids = []
        site_ref = self.config['site']['id']
        
        chiller_points = [
            {"suffix": "status", "dis": "Status", "kind": "Bool", "sensor": True},
            {"suffix": "enable", "dis": "Enable Command", "kind": "Bool", "cmd": True},
            {"suffix": "chwSupplyTemp", "dis": "CHW Supply Temp", "kind": "Number", 
             "unit": "°F", "temp": True, "sensor": True, "leaving": True, "water": True},
            {"suffix": "chwReturnTemp", "dis": "CHW Return Temp", "kind": "Number",
             "unit": "°F", "temp": True, "sensor": True, "entering": True, "water": True},
            {"suffix": "condenserTemp", "dis": "Condenser Temp", "kind": "Number",
             "unit": "°F", "temp": True, "sensor": True, "condenser": True},
            {"suffix": "chwFlow", "dis": "CHW Flow Rate", "kind": "Number",
             "unit": "gpm", "flow": True, "sensor": True, "water": True},
            {"suffix": "power", "dis": "Power", "kind": "Number",
             "unit": "kW", "power": True, "sensor": True, "elec": True},
            {"suffix": "energy", "dis": "Energy", "kind": "Number",
             "unit": "kWh", "energy": True, "sensor": True, "elec": True, "totalizing": True},
            {"suffix": "cop", "dis": "COP", "kind": "Number",
             "unit": "ratio", "sensor": True, "efficiency": True}
        ]
        
        for i in range(1, self.config['equipment']['chillers']['count'] + 1):
            equip_ref = f"equip-chiller-{i}"
            
            for point in chiller_points:
                point_id_str = f"point-chiller-{i}-{point['suffix']}"
                
                point_tags = {
                    "id": point_id_str,
                    "dis": f"Chiller {i} {point['dis']}",
                    "point": True,
                    "siteRef": site_ref,
                    "equipRef": equip_ref,
                    "kind": point['kind']
                }
                
                # Add additional tags from point definition
                for key, value in point.items():
                    if key not in ['suffix', 'dis', 'kind']:
                        point_tags[key] = value
                        
                point_id = self.schema.create_entity(point_tags)
                point_ids.append(point_id)
                self.entity_map[point_id_str] = point_id
                
        return point_ids
        
    def _generate_ahu_points(self) -> List[int]:
        """Generate points for all AHUs."""
        point_ids = []
        site_ref = self.config['site']['id']
        
        ahu_points = [
            {"suffix": "status", "dis": "Status", "kind": "Bool", "sensor": True},
            {"suffix": "enable", "dis": "Enable", "kind": "Bool", "cmd": True},
            {"suffix": "supplyTemp", "dis": "Supply Air Temp", "kind": "Number",
             "unit": "°F", "temp": True, "sensor": True, "discharge": True, "air": True},
            {"suffix": "returnTemp", "dis": "Return Air Temp", "kind": "Number",
             "unit": "°F", "temp": True, "sensor": True, "return": True, "air": True},
            {"suffix": "mixedTemp", "dis": "Mixed Air Temp", "kind": "Number",
             "unit": "°F", "temp": True, "sensor": True, "mixed": True, "air": True},
            {"suffix": "supplyFanSpeed", "dis": "Supply Fan Speed", "kind": "Number",
             "unit": "%", "sensor": True, "fan": True, "speed": True},
            {"suffix": "staticPressure", "dis": "Static Pressure", "kind": "Number",
             "unit": "inH₂O", "pressure": True, "sensor": True, "air": True}
        ]
        
        for i in range(1, self.config['equipment']['ahus']['count'] + 1):
            equip_ref = f"equip-ahu-{i}"
            
            for point in ahu_points:
                point_id_str = f"point-ahu-{i}-{point['suffix']}"
                
                point_tags = {
                    "id": point_id_str,
                    "dis": f"AHU {i} {point['dis']}",
                    "point": True,
                    "siteRef": site_ref,
                    "equipRef": equip_ref,
                    "kind": point['kind']
                }
                
                for key, value in point.items():
                    if key not in ['suffix', 'dis', 'kind']:
                        point_tags[key] = value
                        
                point_id = self.schema.create_entity(point_tags)
                point_ids.append(point_id)
                self.entity_map[point_id_str] = point_id
                
        return point_ids
        
    def _generate_vav_points(self) -> List[int]:
        """Generate points for all VAV boxes."""
        point_ids = []
        site_ref = self.config['site']['id']
        
        vav_points = [
            {"suffix": "zoneTemp", "dis": "Zone Temp", "kind": "Number",
             "unit": "°F", "temp": True, "sensor": True, "zone": True, "air": True},
            {"suffix": "zoneTempSp", "dis": "Zone Temp Setpoint", "kind": "Number",
             "unit": "°F", "temp": True, "sp": True, "zone": True},
            {"suffix": "airFlow", "dis": "Air Flow", "kind": "Number",
             "unit": "cfm", "flow": True, "sensor": True, "air": True},
            {"suffix": "damperPos", "dis": "Damper Position", "kind": "Number",
             "unit": "%", "damper": True, "sensor": True},
            {"suffix": "occupied", "dis": "Occupied", "kind": "Bool",
             "occupied": True, "sensor": True}
        ]
        
        total_floors = self.config['site']['floors']
        zones = self.config['equipment']['vav_boxes']['zones']
        
        for floor in range(1, total_floors + 1):
            for zone in zones:
                equip_ref = f"equip-vav-{floor}-{zone.lower()}"
                
                for point in vav_points:
                    point_id_str = f"point-vav-{floor}-{zone.lower()}-{point['suffix']}"
                    
                    point_tags = {
                        "id": point_id_str,
                        "dis": f"Floor {floor} {zone} {point['dis']}",
                        "point": True,
                        "siteRef": site_ref,
                        "equipRef": equip_ref,
                        "kind": point['kind'],
                        "floor": floor,
                        "zone": zone.lower()
                    }
                    
                    for key, value in point.items():
                        if key not in ['suffix', 'dis', 'kind']:
                            point_tags[key] = value
                            
                    point_id = self.schema.create_entity(point_tags)
                    point_ids.append(point_id)
                    self.entity_map[point_id_str] = point_id
                    
        return point_ids
        
    def _generate_meter_points(self) -> List[int]:
        """Generate points for utility meters."""
        point_ids = []
        site_ref = self.config['site']['id']
        
        # Electric meter points
        electric_points = [
            {"suffix": "power", "dis": "Power", "kind": "Number",
             "unit": "kW", "power": True, "sensor": True, "elec": True},
            {"suffix": "energy", "dis": "Energy", "kind": "Number",
             "unit": "kWh", "energy": True, "sensor": True, "elec": True, "totalizing": True},
            {"suffix": "powerFactor", "dis": "Power Factor", "kind": "Number",
             "unit": "pf", "sensor": True, "elec": True, "pf": True}
        ]
        
        electric_ref = self.config['equipment']['meters']['electric']['id']
        for point in electric_points:
            point_id_str = f"point-{electric_ref}-{point['suffix']}"
            
            point_tags = {
                "id": point_id_str,
                "dis": f"Main Electric {point['dis']}",
                "point": True,
                "siteRef": site_ref,
                "equipRef": electric_ref,
                "kind": point['kind']
            }
            
            for key, value in point.items():
                if key not in ['suffix', 'dis', 'kind']:
                    point_tags[key] = value
                    
            point_id = self.schema.create_entity(point_tags)
            point_ids.append(point_id)
            self.entity_map[point_id_str] = point_id
            
        # Gas meter points
        gas_points = [
            {"suffix": "flow", "dis": "Gas Flow", "kind": "Number",
             "unit": "ft³/h", "flow": True, "sensor": True, "gas": True},
            {"suffix": "volume", "dis": "Gas Volume", "kind": "Number",
             "unit": "ft³", "volume": True, "sensor": True, "gas": True, "totalizing": True}
        ]
        
        gas_ref = self.config['equipment']['meters']['gas']['id']
        for point in gas_points:
            point_id_str = f"point-{gas_ref}-{point['suffix']}"
            
            point_tags = {
                "id": point_id_str,
                "dis": f"Main Gas {point['dis']}",
                "point": True,
                "siteRef": site_ref,
                "equipRef": gas_ref,
                "kind": point['kind']
            }
            
            for key, value in point.items():
                if key not in ['suffix', 'dis', 'kind']:
                    point_tags[key] = value
                    
            point_id = self.schema.create_entity(point_tags)
            point_ids.append(point_id)
            self.entity_map[point_id_str] = point_id
            
        # Water meter points
        water_points = [
            {"suffix": "flow", "dis": "Water Flow", "kind": "Number",
             "unit": "gal/min", "flow": True, "sensor": True, "water": True},
            {"suffix": "volume", "dis": "Water Volume", "kind": "Number",
             "unit": "gal", "volume": True, "sensor": True, "water": True, "totalizing": True}
        ]
        
        water_ref = self.config['equipment']['meters']['water']['id']
        for point in water_points:
            point_id_str = f"point-{water_ref}-{point['suffix']}"
            
            point_tags = {
                "id": point_id_str,
                "dis": f"Main Water {point['dis']}",
                "point": True,
                "siteRef": site_ref,
                "equipRef": water_ref,
                "kind": point['kind']
            }
            
            for key, value in point.items():
                if key not in ['suffix', 'dis', 'kind']:
                    point_tags[key] = value
                    
            point_id = self.schema.create_entity(point_tags)
            point_ids.append(point_id)
            self.entity_map[point_id_str] = point_id
            
        return point_ids