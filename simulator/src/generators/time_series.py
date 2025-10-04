"""Time-series data generators with realistic patterns."""

import logging
import random
import math
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TimeSeriesGenerator:
    """Generates realistic time-series data for building systems."""

    def __init__(self, config: Dict[str, Any], entity_map: Dict[str, int],
                 initial_totalizers: Optional[Dict[str, Any]] = None):
        """Initialize time-series generator.

        Args:
            config: Building configuration dictionary
            entity_map: Mapping of entity names to database IDs
            initial_totalizers: Optional initial totalizer values for resumption
        """
        self.config = config
        self.entity_map = entity_map
        self.random = random.Random(42)  # Reproducible random seed
        self.np_random = np.random.RandomState(42)

        # Initialize totalizer accumulators for energy/volume meters
        if initial_totalizers:
            # Resume from provided totalizer values
            self.totalizers = {
                'electric_energy': initial_totalizers.get('electric_energy', 0.0),
                'gas_volume': initial_totalizers.get('gas_volume', 0.0),
                'water_volume': initial_totalizers.get('water_volume', 0.0),
                'chiller_energy': initial_totalizers.get('chiller_energy', {})
            }
            logger.info(f"Resuming with totalizers: {self.totalizers}")
        else:
            # Start from zero
            self.totalizers = {
                'electric_energy': 0.0,  # kWh
                'gas_volume': 0.0,       # ft³
                'water_volume': 0.0,     # gallons
                'chiller_energy': {}     # kWh per chiller
            }
        
    def generate_historical_data(self, days: int = 30) -> pd.DataFrame:
        """Generate historical time-series data.
        
        Args:
            days: Number of days of historical data to generate
            
        Returns:
            DataFrame with historical time-series data
        """
        logger.info(f"Generating {days} days of historical data...")
        
        # Generate time range
        end_time = datetime.now().replace(second=0, microsecond=0)
        start_time = end_time - timedelta(days=days)
        interval_minutes = self.config['generation']['data_interval_minutes']
        
        time_range = pd.date_range(
            start=start_time,
            end=end_time,
            freq=f'{interval_minutes}min'
        )
        
        all_data = []
        
        # Generate data for each time point
        for i, timestamp in enumerate(time_range):
            if i % 1000 == 0:
                progress = (i / len(time_range)) * 100
                logger.info(f"Progress: {progress:.1f}% ({i}/{len(time_range)})")
                
            # Generate weather conditions for this timestamp
            outdoor_temp, season = self._get_outdoor_conditions(timestamp)
            
            # Generate occupancy ratio
            occupancy_ratio = self._get_occupancy_ratio(timestamp)
            
            # Generate data for all points
            timestamp_data = self._generate_timestamp_data(
                timestamp, outdoor_temp, season, occupancy_ratio
            )
            
            all_data.extend(timestamp_data)
            
        logger.info(f"Generated {len(all_data)} data points")
        return pd.DataFrame(all_data)
        
    def _get_outdoor_conditions(self, timestamp: datetime) -> Tuple[float, str]:
        """Get outdoor temperature and season for timestamp.
        
        Args:
            timestamp: Datetime for conditions
            
        Returns:
            Tuple of (temperature, season)
        """
        # Determine season
        month = timestamp.month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'fall'
            
        season_config = self.config['weather']['seasons'][season]
        
        # Generate temperature with daily and seasonal variation
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        
        # Daily temperature curve (cooler at night, warmer during day)
        daily_factor = 0.5 * math.sin((hour - 6) * math.pi / 12) + 0.5
        
        # Seasonal variation
        seasonal_factor = 0.5 * math.sin((day_of_year - 80) * 2 * math.pi / 365) + 0.5
        
        # Base temperature with variation
        temp_range = season_config['max'] - season_config['min']
        base_temp = season_config['min'] + (temp_range * seasonal_factor)
        
        # Add daily variation (±10°F swing)
        daily_swing = 10 * (daily_factor - 0.5) * 2
        
        # Add random noise
        noise = self.np_random.normal(0, 2)
        
        temperature = base_temp + daily_swing + noise
        
        return temperature, season
        
    def _get_occupancy_ratio(self, timestamp: datetime) -> float:
        """Get occupancy ratio for timestamp.
        
        Args:
            timestamp: Datetime for occupancy
            
        Returns:
            Occupancy ratio (0-1)
        """
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5
        
        if is_weekend:
            return self.config['schedules']['weekend']['default']
            
        # Find closest hour in weekday schedule
        weekday_schedule = self.config['schedules']['weekday']
        hour_key = f"{hour:02d}:00"
        
        if hour_key in weekday_schedule:
            base_occupancy = weekday_schedule[hour_key]
        else:
            # Interpolate between closest hours
            hours = sorted([int(h.split(':')[0]) for h in weekday_schedule.keys()])
            
            # Find surrounding hours
            lower_hour = max([h for h in hours if h <= hour], default=hours[0])
            upper_hour = min([h for h in hours if h > hour], default=hours[-1])
            
            if lower_hour == upper_hour:
                base_occupancy = weekday_schedule[f"{lower_hour:02d}:00"]
            else:
                lower_val = weekday_schedule[f"{lower_hour:02d}:00"]
                upper_val = weekday_schedule[f"{upper_hour:02d}:00"]
                ratio = (hour - lower_hour) / (upper_hour - lower_hour)
                base_occupancy = lower_val + ratio * (upper_val - lower_val)
                
        # Add some randomness
        noise = self.np_random.normal(0, 0.05)
        occupancy = max(0, min(1, base_occupancy + noise))
        
        return occupancy
        
    def _generate_timestamp_data(self, timestamp: datetime, outdoor_temp: float,
                               season: str, occupancy_ratio: float) -> List[Dict]:
        """Generate data for all points at a specific timestamp.
        
        Args:
            timestamp: Current timestamp
            outdoor_temp: Outdoor temperature
            season: Season name
            occupancy_ratio: Building occupancy ratio
            
        Returns:
            List of data point dictionaries
        """
        data_points = []
        
        # Generate chiller data
        data_points.extend(self._generate_chiller_data(
            timestamp, outdoor_temp, season, occupancy_ratio
        ))
        
        # Generate AHU data
        data_points.extend(self._generate_ahu_data(
            timestamp, outdoor_temp, season, occupancy_ratio
        ))
        
        # Generate VAV data
        data_points.extend(self._generate_vav_data(
            timestamp, outdoor_temp, season, occupancy_ratio
        ))
        
        # Generate meter data
        data_points.extend(self._generate_meter_data(
            timestamp, outdoor_temp, season, occupancy_ratio
        ))
        
        return data_points
        
    def _generate_chiller_data(self, timestamp: datetime, outdoor_temp: float,
                             season: str, occupancy_ratio: float) -> List[Dict]:
        """Generate chiller data points."""
        data_points = []
        chiller_count = self.config['equipment']['chillers']['count']
        
        # Calculate cooling load based on occupancy and outdoor temperature
        base_load = max(0.2, occupancy_ratio) * 0.8  # Base load from occupancy
        temp_load = max(0, (outdoor_temp - 70) / 25) * 0.3  # Additional load from temperature
        total_load = min(1.0, base_load + temp_load)
        
        # Primary chiller takes most load, backup only runs if needed
        chiller_loads = [total_load] if total_load < 0.85 else [0.85, total_load - 0.85]
        if len(chiller_loads) == 1:
            chiller_loads.append(0)  # Backup chiller off
            
        for i in range(1, chiller_count + 1):
            load_ratio = chiller_loads[i-1] if i <= len(chiller_loads) else 0
            
            # Status
            status = load_ratio > 0.05
            entity_id = self.entity_map[f"point-chiller-{i}-status"]
            data_points.append({
                'entity_id': entity_id,
                'ts': timestamp,
                'value_b': status,
                'status': self._get_data_status()
            })
            
            if status:
                # Supply temperature (42-48°F based on load)
                supply_temp = 42 + (48-42) * (1 - load_ratio) + self.np_random.normal(0, 0.5)
                entity_id = self.entity_map[f"point-chiller-{i}-chwSupplyTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(supply_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Return temperature (52-58°F)
                return_temp = supply_temp + 10 + self.np_random.normal(0, 0.5)
                entity_id = self.entity_map[f"point-chiller-{i}-chwReturnTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(return_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Flow rate (based on load)
                max_flow = 800  # gpm
                flow_rate = max_flow * load_ratio + self.np_random.normal(0, 20)
                entity_id = self.entity_map[f"point-chiller-{i}-chwFlow"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(flow_rate, 0),
                    'status': self._get_data_status()
                })
                
                # Power consumption
                capacity_tons = self.config['equipment']['chillers']['capacity']
                cop = self._calculate_chiller_cop(load_ratio, outdoor_temp)
                power_kw = (capacity_tons * load_ratio * 3.517) / cop  # 3.517 kW/ton baseline
                power_kw += self.np_random.normal(0, power_kw * 0.02)  # 2% noise
                
                entity_id = self.entity_map[f"point-chiller-{i}-power"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(power_kw, 1),
                    'status': self._get_data_status()
                })
                
                # COP
                entity_id = self.entity_map[f"point-chiller-{i}-cop"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(cop, 2),
                    'status': self._get_data_status()
                })
                
                # Condenser temperature (heat rejection side)
                # Condenser temp = outdoor temp + approach temp based on load and efficiency
                heat_rejection_kw = power_kw + (capacity_tons * load_ratio * 3.517)  # Power + cooling load
                approach_temp = 10 + (heat_rejection_kw / capacity_tons) * 1.5  # Approach increases with load
                condenser_temp = outdoor_temp + approach_temp + self.np_random.normal(0, 1)
                
                # Ensure condenser temp is always higher than return water temp (thermodynamics)
                # The condenser must reject heat, so it must be warmer than the chilled water
                min_condenser_temp = return_temp + 15  # At least 15°F above CHW return
                condenser_temp = max(condenser_temp, min_condenser_temp)
                
                entity_id = self.entity_map[f"point-chiller-{i}-condenserTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(condenser_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Energy totalizer (accumulating kWh)
                interval_hours = self.config['generation']['data_interval_minutes'] / 60.0
                if i not in self.totalizers['chiller_energy']:
                    self.totalizers['chiller_energy'][i] = 0.0
                self.totalizers['chiller_energy'][i] += power_kw * interval_hours
                
                entity_id = self.entity_map[f"point-chiller-{i}-energy"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(self.totalizers['chiller_energy'][i], 1),
                    'status': self._get_data_status()
                })
                
        return data_points
        
    def _generate_ahu_data(self, timestamp: datetime, outdoor_temp: float,
                         season: str, occupancy_ratio: float) -> List[Dict]:
        """Generate AHU data points."""
        data_points = []
        ahu_count = self.config['equipment']['ahus']['count']
        
        for i in range(1, ahu_count + 1):
            # AHU runs if building is occupied or needs heating/cooling
            operating = occupancy_ratio > 0.1 or abs(outdoor_temp - 70) > 10
            
            # Status
            entity_id = self.entity_map[f"point-ahu-{i}-status"]
            data_points.append({
                'entity_id': entity_id,
                'ts': timestamp,
                'value_b': operating,
                'status': self._get_data_status()
            })
            
            if operating:
                # Supply air temperature (55-65°F based on season and load)
                if season in ['summer']:
                    supply_temp = 55 + (65-55) * (1 - occupancy_ratio)
                else:
                    supply_temp = 65 + (75-65) * occupancy_ratio
                supply_temp += self.np_random.normal(0, 1.0)
                
                entity_id = self.entity_map[f"point-ahu-{i}-supplyTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(supply_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Return air temperature
                return_temp = 72 + self.np_random.normal(0, 1.5)
                entity_id = self.entity_map[f"point-ahu-{i}-returnTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(return_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Fan speed (based on load)
                fan_speed = 40 + occupancy_ratio * 50 + self.np_random.normal(0, 5)
                fan_speed = max(30, min(95, fan_speed))
                
                entity_id = self.entity_map[f"point-ahu-{i}-supplyFanSpeed"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(fan_speed, 0),
                    'status': self._get_data_status()
                })
                
                # Mixed air temperature (blend of return and outdoor air)
                # Determine outdoor air fraction based on economizer logic
                if season in ['spring', 'fall'] and 55 <= outdoor_temp <= 70:
                    # Free cooling mode - use more outdoor air
                    oa_fraction = 0.7 + self.np_random.normal(0, 0.05)
                elif occupancy_ratio > 0.1:
                    # Minimum outdoor air for ventilation (ASHRAE 62.1)
                    oa_fraction = 0.15 + occupancy_ratio * 0.15  # 15-30% based on occupancy
                else:
                    # Unoccupied - minimum OA
                    oa_fraction = 0.1
                    
                oa_fraction = max(0.1, min(1.0, oa_fraction))
                mixed_temp = return_temp * (1 - oa_fraction) + outdoor_temp * oa_fraction
                mixed_temp += self.np_random.normal(0, 0.5)
                
                entity_id = self.entity_map[f"point-ahu-{i}-mixedTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(mixed_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Static pressure (inches of water column)
                # Pressure varies with fan speed (affinity laws) and system resistance
                base_pressure = 1.5  # Design static pressure at 100% flow
                pressure = base_pressure * (fan_speed / 100) ** 2  # Pressure follows square law
                
                # Add variation based on VAV damper positions (assumed from occupancy)
                # Higher occupancy = more VAVs open = lower static pressure
                resistance_factor = 1.0 + (1 - occupancy_ratio) * 0.3  # Up to 30% increase when VAVs close
                pressure *= resistance_factor
                pressure += self.np_random.normal(0, 0.05)
                pressure = max(0.5, min(3.0, pressure))  # Typical range 0.5-3.0 inH2O
                
                entity_id = self.entity_map[f"point-ahu-{i}-staticPressure"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(pressure, 2),
                    'status': self._get_data_status()
                })
                
        return data_points
        
    def _generate_vav_data(self, timestamp: datetime, outdoor_temp: float,
                         season: str, occupancy_ratio: float) -> List[Dict]:
        """Generate VAV box data points."""
        data_points = []
        total_floors = self.config['site']['floors']
        zones = self.config['equipment']['vav_boxes']['zones']
        
        for floor in range(1, total_floors + 1):
            for zone in zones:
                zone_key = zone.lower()
                
                # Zone-specific occupancy (some variation)
                zone_occupancy = occupancy_ratio + self.np_random.normal(0, 0.1)
                zone_occupancy = max(0, min(1, zone_occupancy))
                
                # Zone temperature with realistic setpoint control
                occupied = zone_occupancy > 0.1
                if occupied:
                    if season in ['summer']:
                        target_temp = self.config['setpoints']['occupied']['cooling']
                    else:
                        target_temp = self.config['setpoints']['occupied']['heating']
                else:
                    if season in ['summer']:
                        target_temp = self.config['setpoints']['unoccupied']['cooling']
                    else:
                        target_temp = self.config['setpoints']['unoccupied']['heating']
                
                # Add control variation and external factors
                temp_variation = self.np_random.normal(0, 1.5)
                if zone_key in ['south', 'west']:  # Solar load
                    hour = timestamp.hour
                    if 10 <= hour <= 16 and season == 'summer':
                        temp_variation += 2  # Solar heating
                        
                zone_temp = target_temp + temp_variation
                
                # Zone temperature
                entity_id = self.entity_map[f"point-vav-{floor}-{zone_key}-zoneTemp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(zone_temp, 1),
                    'status': self._get_data_status()
                })
                
                # Zone setpoint
                entity_id = self.entity_map[f"point-vav-{floor}-{zone_key}-zoneTempSp"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': target_temp,
                    'status': self._get_data_status()
                })
                
                # Airflow based on demand
                max_flow = self.config['performance']['vav']['max_flow_cfm']
                min_flow_ratio = self.config['performance']['vav']['min_flow_ratio']
                
                # Calculate flow demand
                temp_error = abs(zone_temp - target_temp)
                flow_demand = min_flow_ratio + (1 - min_flow_ratio) * min(1, temp_error / 3)
                if not occupied:
                    flow_demand = min_flow_ratio
                    
                airflow = max_flow * flow_demand + self.np_random.normal(0, 20)
                airflow = max(max_flow * min_flow_ratio, min(max_flow, airflow))
                
                entity_id = self.entity_map[f"point-vav-{floor}-{zone_key}-airFlow"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(airflow, 0),
                    'status': self._get_data_status()
                })
                
                # Damper position
                damper_pos = (airflow / max_flow) * 100
                entity_id = self.entity_map[f"point-vav-{floor}-{zone_key}-damperPos"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_n': round(damper_pos, 0),
                    'status': self._get_data_status()
                })
                
                # Occupancy status
                entity_id = self.entity_map[f"point-vav-{floor}-{zone_key}-occupied"]
                data_points.append({
                    'entity_id': entity_id,
                    'ts': timestamp,
                    'value_b': occupied,
                    'status': self._get_data_status()
                })
                
        return data_points
        
    def _generate_meter_data(self, timestamp: datetime, outdoor_temp: float,
                           season: str, occupancy_ratio: float) -> List[Dict]:
        """Generate utility meter data points."""
        data_points = []
        interval_hours = self.config['generation']['data_interval_minutes'] / 60.0
        
        # Electric meter - mainly HVAC load
        base_electric_kw = 200  # Base building load
        hvac_load_kw = occupancy_ratio * 300  # HVAC load
        temp_adjustment = max(0, abs(outdoor_temp - 70) / 25) * 150
        
        total_electric_kw = base_electric_kw + hvac_load_kw + temp_adjustment
        total_electric_kw += self.np_random.normal(0, total_electric_kw * 0.03)
        
        entity_id = self.entity_map["point-meter-main-electric-power"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(total_electric_kw, 1),
            'status': self._get_data_status()
        })
        
        # Electric energy totalizer (accumulating kWh)
        self.totalizers['electric_energy'] += total_electric_kw * interval_hours
        entity_id = self.entity_map["point-meter-main-electric-energy"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(self.totalizers['electric_energy'], 1),
            'status': self._get_data_status()
        })
        
        # Power factor (realistic range 0.85-0.95, worse at low loads)
        load_ratio = total_electric_kw / 800  # Assume 800kW max capacity
        base_pf = 0.92  # Good power factor at optimal load
        # Power factor degrades at low loads
        if load_ratio < 0.3:
            power_factor = base_pf - 0.05
        elif load_ratio > 0.8:
            power_factor = base_pf - 0.02  # Slightly worse at very high loads
        else:
            power_factor = base_pf
        power_factor += self.np_random.normal(0, 0.01)
        power_factor = max(0.80, min(0.98, power_factor))
        
        entity_id = self.entity_map["point-meter-main-electric-powerFactor"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(power_factor, 3),
            'status': self._get_data_status()
        })
        
        # Gas meter - heating load
        gas_flow = 0
        if season in ['winter', 'fall'] and outdoor_temp < 60:
            heating_load = max(0, (60 - outdoor_temp) / 40) * occupancy_ratio
            gas_flow = heating_load * 500 + self.np_random.normal(0, 50)
            
        entity_id = self.entity_map["point-meter-main-gas-flow"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(gas_flow, 0),
            'status': self._get_data_status()
        })
        
        # Gas volume totalizer (accumulating ft³)
        self.totalizers['gas_volume'] += gas_flow * interval_hours
        entity_id = self.entity_map["point-meter-main-gas-volume"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(self.totalizers['gas_volume'], 0),
            'status': self._get_data_status()
        })
        
        # Water meter - mainly HVAC and occupancy
        water_flow = occupancy_ratio * 20 + 5  # Base flow in gal/min
        
        # Add cooling tower makeup water when chillers are running
        # Check if any chillers are running
        chiller_running = False
        for i in range(1, self.config['equipment']['chillers']['count'] + 1):
            if f'point-chiller-{i}-status' in self.entity_map:
                # Assume chiller is running if outdoor temp > 65 and occupied
                if outdoor_temp > 65 and occupancy_ratio > 0.1:
                    chiller_running = True
                    break
        
        if chiller_running:
            # Cooling tower makeup water proportional to heat rejection
            cooling_load_factor = max(0, (outdoor_temp - 65) / 30)
            water_flow += cooling_load_factor * 15  # Additional flow for cooling tower
        
        water_flow += self.np_random.normal(0, 1)
        water_flow = max(0, water_flow)
        
        entity_id = self.entity_map["point-meter-main-water-flow"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(water_flow, 1),
            'status': self._get_data_status()
        })
        
        # Water volume totalizer (accumulating gallons)
        # Convert flow rate (gal/min) to volume (gal) over interval
        water_volume_increment = water_flow * (interval_hours * 60)  # gal/min * minutes
        self.totalizers['water_volume'] += water_volume_increment
        entity_id = self.entity_map["point-meter-main-water-volume"]
        data_points.append({
            'entity_id': entity_id,
            'ts': timestamp,
            'value_n': round(self.totalizers['water_volume'], 0),
            'status': self._get_data_status()
        })
        
        return data_points
        
    def _calculate_chiller_cop(self, load_ratio: float, outdoor_temp: float) -> float:
        """Calculate chiller COP based on load and conditions."""
        base_cop = self.config['performance']['chiller']['base_cop']
        cop_curve = self.config['performance']['chiller']['cop_curve']
        
        # Find efficiency factor from curve
        load_ratios = sorted(cop_curve.keys())
        
        # Find surrounding load ratios
        lower_ratio = max([r for r in load_ratios if r <= load_ratio], default=load_ratios[0])
        upper_ratio = min([r for r in load_ratios if r > load_ratio], default=load_ratios[-1])
        
        if lower_ratio == upper_ratio:
            efficiency_factor = cop_curve[lower_ratio]
        else:
            lower_eff = cop_curve[lower_ratio]
            upper_eff = cop_curve[upper_ratio]
            ratio = (load_ratio - lower_ratio) / (upper_ratio - lower_ratio)
            efficiency_factor = lower_eff + ratio * (upper_eff - lower_eff)
            
        # Temperature impact (degraded performance at high outdoor temps)
        temp_factor = 1.0 - max(0, (outdoor_temp - 85) * 0.02)
        
        cop = base_cop * efficiency_factor * temp_factor
        return max(2.0, cop)  # Minimum COP
        
    def _get_data_status(self) -> str:
        """Get data status based on quality settings."""
        rand = self.random.random() * 100
        
        good_pct = self.config['generation']['good_data_percentage']
        stale_pct = self.config['generation']['stale_data_percentage']
        
        if rand < good_pct:
            return 'ok'
        elif rand < good_pct + stale_pct:
            return 'stale'
        else:
            return 'fault'