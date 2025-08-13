"""HVAC equipment models with realistic operational characteristics."""

import logging
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .building import Equipment, Point, EquipmentStatus

logger = logging.getLogger(__name__)


@dataclass
class ChillerModel(Equipment):
    """Chiller equipment model with performance characteristics."""
    capacity_tons: float = 400.0
    cop_rated: float = 6.2
    min_load_ratio: float = 0.15
    max_load_ratio: float = 1.0
    current_load_ratio: float = 0.0
    supply_temp_setpoint: float = 44.0  # °F
    
    def __post_init__(self):
        super().__init__(
            self.id, self.name, self.site_ref, "chiller",
            self.manufacturer, self.model, self.install_date, self.status, self.tags
        )
        
    def calculate_performance(self, load_ratio: float, outdoor_temp: float) -> Dict[str, float]:
        """Calculate chiller performance at given conditions.
        
        Args:
            load_ratio: Load ratio (0-1)
            outdoor_temp: Outdoor temperature (°F)
            
        Returns:
            Dictionary with performance metrics
        """
        if load_ratio < self.min_load_ratio:
            # Below minimum load, chiller cycles off
            return {
                'power_kw': 0.0,
                'cop': 0.0,
                'supply_temp': 70.0,  # No cooling
                'flow_gpm': 0.0,
                'operating': False
            }
            
        # Part-load efficiency curve (typical centrifugal chiller)
        if load_ratio < 0.3:
            efficiency_factor = 0.4
        elif load_ratio < 0.5:
            efficiency_factor = 0.75
        elif load_ratio < 0.8:
            efficiency_factor = 0.95
        else:
            efficiency_factor = 0.9
            
        # Temperature impact on COP
        condenser_temp_impact = max(0.5, 1.0 - (outdoor_temp - 85) * 0.02)
        
        # Calculate COP
        current_cop = self.cop_rated * efficiency_factor * condenser_temp_impact
        current_cop = max(2.0, current_cop)  # Minimum COP
        
        # Calculate power
        cooling_load_tons = self.capacity_tons * load_ratio
        power_kw = (cooling_load_tons * 3.517) / current_cop  # 3.517 kW/ton baseline
        
        # Supply temperature varies with load
        supply_temp = self.supply_temp_setpoint + (1 - load_ratio) * 4  # Higher temp at low loads
        
        # Flow rate proportional to load
        flow_gpm = 2.4 * cooling_load_tons  # 2.4 gpm per ton typical
        
        return {
            'power_kw': power_kw,
            'cop': current_cop,
            'supply_temp': supply_temp,
            'return_temp': supply_temp + 12,  # 12°F delta T
            'flow_gpm': flow_gpm,
            'operating': True,
            'load_ratio': load_ratio
        }


@dataclass
class AHUModel(Equipment):
    """Air Handling Unit model."""
    supply_fan_hp: float = 25.0
    return_fan_hp: float = 20.0
    max_airflow_cfm: float = 15000.0
    current_airflow_ratio: float = 0.0
    supply_temp_setpoint: float = 55.0  # °F
    
    def __post_init__(self):
        super().__init__(
            self.id, self.name, self.site_ref, "ahu",
            self.manufacturer, self.model, self.install_date, self.status, self.tags
        )
        
    def calculate_performance(self, airflow_ratio: float, outdoor_temp: float,
                            return_temp: float = 72.0) -> Dict[str, float]:
        """Calculate AHU performance.
        
        Args:
            airflow_ratio: Airflow ratio (0-1)
            outdoor_temp: Outdoor temperature (°F)
            return_temp: Return air temperature (°F)
            
        Returns:
            Dictionary with performance metrics
        """
        if airflow_ratio < 0.2:
            # Below minimum airflow
            return {
                'supply_temp': return_temp,
                'mixed_temp': return_temp,
                'supply_fan_speed': 0,
                'power_kw': 0,
                'operating': False
            }
            
        # Fan power curve (cubic relationship)
        fan_power_ratio = airflow_ratio ** 2.5  # VFD fan curve
        supply_fan_power = self.supply_fan_hp * 0.746 * fan_power_ratio  # Convert HP to kW
        return_fan_power = self.return_fan_hp * 0.746 * fan_power_ratio
        
        total_power = supply_fan_power + return_fan_power
        
        # Supply fan speed percentage
        supply_fan_speed = airflow_ratio * 100
        
        # Mixed air temperature (simplified economizer logic)
        if 55 <= outdoor_temp <= 65:  # Economizer range
            outside_air_ratio = min(0.3, max(0.15, (65 - outdoor_temp) / 20))
        else:
            outside_air_ratio = 0.15  # Minimum outdoor air
            
        mixed_temp = return_temp * (1 - outside_air_ratio) + outdoor_temp * outside_air_ratio
        
        # Supply temperature based on cooling/heating need
        supply_temp = self.supply_temp_setpoint
        
        return {
            'supply_temp': supply_temp,
            'mixed_temp': mixed_temp,
            'return_temp': return_temp,
            'supply_fan_speed': supply_fan_speed,
            'power_kw': total_power,
            'airflow_cfm': self.max_airflow_cfm * airflow_ratio,
            'outside_air_ratio': outside_air_ratio,
            'operating': True
        }


@dataclass
class VAVModel(Equipment):
    """VAV box model."""
    max_airflow_cfm: float = 800.0
    min_airflow_ratio: float = 0.3
    current_airflow_cfm: float = 0.0
    zone_temp_setpoint: float = 72.0
    floor: int = 1
    zone: str = "north"
    
    def __post_init__(self):
        super().__init__(
            self.id, self.name, self.site_ref, "vav",
            self.manufacturer, self.model, self.install_date, self.status, self.tags
        )
        
    def calculate_performance(self, zone_temp: float, supply_temp: float = 55.0,
                            occupied: bool = True) -> Dict[str, float]:
        """Calculate VAV performance based on zone conditions.
        
        Args:
            zone_temp: Current zone temperature (°F)
            supply_temp: Supply air temperature (°F)
            occupied: Zone occupancy status
            
        Returns:
            Dictionary with performance metrics
        """
        if not occupied:
            # Unoccupied - minimum airflow
            airflow_cfm = self.max_airflow_cfm * self.min_airflow_ratio
            damper_position = self.min_airflow_ratio * 100
        else:
            # Occupied - modulate based on temperature error
            temp_error = zone_temp - self.zone_temp_setpoint
            
            # PI control logic (simplified)
            if abs(temp_error) < 1.0:
                # Within deadband
                flow_demand = 0.5
            else:
                # Proportional response
                flow_demand = 0.5 + (temp_error / 4.0)  # 4°F for full range
                
            # Clamp to valid range
            flow_demand = max(self.min_airflow_ratio, min(1.0, flow_demand))
            
            airflow_cfm = self.max_airflow_cfm * flow_demand
            damper_position = flow_demand * 100
            
        return {
            'zone_temp': zone_temp,
            'zone_temp_sp': self.zone_temp_setpoint,
            'airflow_cfm': airflow_cfm,
            'damper_position': damper_position,
            'supply_temp': supply_temp,
            'heating_valve_position': 0,  # Cooling only VAV
            'occupied': occupied,
            'flow_ratio': airflow_cfm / self.max_airflow_cfm
        }


@dataclass
class UtilityMeter(Equipment):
    """Utility meter model."""
    meter_type: str = "electric"  # electric, gas, water
    multiplier: float = 1.0
    current_reading: float = 0.0
    previous_reading: float = 0.0
    
    def __post_init__(self):
        super().__init__(
            self.id, self.name, self.site_ref, "meter",
            self.manufacturer, self.model, self.install_date, self.status, self.tags
        )
        
    def calculate_consumption(self, load_kw: float = None, flow_rate: float = None,
                            interval_minutes: int = 15) -> Dict[str, float]:
        """Calculate utility consumption.
        
        Args:
            load_kw: Current load in kW (for electric)
            flow_rate: Current flow rate (for gas/water)
            interval_minutes: Integration interval
            
        Returns:
            Dictionary with consumption metrics
        """
        if self.meter_type == "electric":
            power = load_kw or 0.0
            energy_kwh = power * (interval_minutes / 60.0)  # kWh for interval
            
            return {
                'power': power,
                'energy': energy_kwh,
                'voltage': 480 + (power / 1000) * 2,  # Slight voltage variation with load
                'current': power * 1000 / (480 * 1.732) if power > 0 else 0,  # 3-phase
                'power_factor': 0.95 if power > 50 else 1.0
            }
            
        elif self.meter_type == "gas":
            flow = flow_rate or 0.0
            volume = flow * (interval_minutes / 60.0)  # Volume for interval
            
            return {
                'flow': flow,
                'volume': volume,
                'pressure': 5.0,  # psig
                'temperature': 70.0  # °F
            }
            
        elif self.meter_type == "water":
            flow = flow_rate or 0.0
            volume = flow * (interval_minutes / 60.0)  # Volume for interval
            
            return {
                'flow': flow,
                'volume': volume,
                'pressure': 65.0,  # psig
                'temperature': 55.0  # °F
            }
            
        return {}


@dataclass
class HVACSystem:
    """Complete HVAC system with equipment coordination."""
    site_ref: str
    chillers: List[ChillerModel] = field(default_factory=list)
    ahus: List[AHUModel] = field(default_factory=list)
    vavs: List[VAVModel] = field(default_factory=list)
    meters: List[UtilityMeter] = field(default_factory=list)
    
    def add_chiller(self, chiller: ChillerModel):
        """Add chiller to system."""
        self.chillers.append(chiller)
        
    def add_ahu(self, ahu: AHUModel):
        """Add AHU to system."""
        self.ahus.append(ahu)
        
    def add_vav(self, vav: VAVModel):
        """Add VAV to system."""
        self.vavs.append(vav)
        
    def add_meter(self, meter: UtilityMeter):
        """Add meter to system."""
        self.meters.append(meter)
        
    def calculate_cooling_load(self, zone_temps: List[float], 
                             outdoor_temp: float) -> float:
        """Calculate total cooling load for system.
        
        Args:
            zone_temps: List of zone temperatures
            outdoor_temp: Outdoor temperature
            
        Returns:
            Total cooling load ratio (0-1)
        """
        if not zone_temps:
            return 0.0
            
        # Calculate load based on zone temperature deviations
        setpoint = 72.0
        temp_deviations = [max(0, temp - setpoint) for temp in zone_temps]
        avg_deviation = sum(temp_deviations) / len(temp_deviations)
        
        # Base load from zone temperatures
        zone_load = min(1.0, avg_deviation / 4.0)  # 4°F = full load
        
        # Additional load from outdoor temperature
        outdoor_load = max(0, (outdoor_temp - 70) / 25)  # 25°F range for full load
        
        total_load = min(1.0, zone_load * 0.7 + outdoor_load * 0.3)
        
        return total_load
        
    def get_total_power_consumption(self) -> float:
        """Get total electrical power consumption of HVAC system.
        
        Returns:
            Total power in kW
        """
        total_power = 0.0
        
        # Add chiller power (would need current operating data)
        for chiller in self.chillers:
            if chiller.status == EquipmentStatus.ON:
                # This would be calculated based on current load
                total_power += chiller.capacity_tons * 0.6  # Rough estimate
                
        # Add AHU power
        for ahu in self.ahus:
            if ahu.status == EquipmentStatus.ON:
                total_power += (ahu.supply_fan_hp + ahu.return_fan_hp) * 0.746
                
        return total_power