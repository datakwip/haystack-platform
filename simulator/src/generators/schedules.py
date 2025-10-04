"""Occupancy and operational schedule generators."""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, time, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class ScheduleGenerator:
    """Generates realistic occupancy and operational schedules."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize schedule generator.
        
        Args:
            config: Building configuration dictionary
        """
        self.config = config
        self.random_state = np.random.RandomState(42)
        
    def get_occupancy_ratio(self, timestamp: datetime) -> float:
        """Get occupancy ratio for a specific timestamp.
        
        Args:
            timestamp: Timestamp to get occupancy for
            
        Returns:
            Occupancy ratio (0.0 to 1.0)
        """
        hour = timestamp.hour
        minute = timestamp.minute
        is_weekend = timestamp.weekday() >= 5
        is_holiday = self._is_holiday(timestamp)
        
        if is_weekend or is_holiday:
            # Weekend/holiday schedule - minimal occupancy
            base_ratio = self.config['schedules']['weekend']['default']
            
            # Slight variation during daytime
            if 8 <= hour <= 17:
                base_ratio += 0.02
                
        else:
            # Weekday schedule
            base_ratio = self._get_weekday_occupancy(hour, minute)
            
        # Add random variation (±5%)
        variation = self.random_state.normal(0, 0.05)
        final_ratio = max(0.0, min(1.0, base_ratio + variation))
        
        return final_ratio
        
    def _get_weekday_occupancy(self, hour: int, minute: int) -> float:
        """Get weekday occupancy ratio for hour and minute.
        
        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
            
        Returns:
            Occupancy ratio
        """
        # Convert to decimal hours
        decimal_hour = hour + minute / 60.0
        
        # Get schedule points
        schedule = self.config['schedules']['weekday']
        
        # Convert schedule keys to decimal hours and sort
        schedule_points = []
        for time_str, ratio in schedule.items():
            hour_part, minute_part = map(int, time_str.split(':'))
            decimal_time = hour_part + minute_part / 60.0
            schedule_points.append((decimal_time, ratio))
            
        schedule_points.sort()
        
        # Find surrounding points for interpolation
        if decimal_hour <= schedule_points[0][0]:
            return schedule_points[0][1]
        elif decimal_hour >= schedule_points[-1][0]:
            return schedule_points[-1][1]
        
        # Find bracketing points
        for i in range(len(schedule_points) - 1):
            time1, ratio1 = schedule_points[i]
            time2, ratio2 = schedule_points[i + 1]
            
            if time1 <= decimal_hour <= time2:
                # Linear interpolation
                if time2 == time1:
                    return ratio1
                    
                weight = (decimal_hour - time1) / (time2 - time1)
                return ratio1 + weight * (ratio2 - ratio1)
                
        return schedule_points[-1][1]
        
    def _is_holiday(self, timestamp: datetime) -> bool:
        """Check if timestamp falls on a holiday.
        
        Args:
            timestamp: Timestamp to check
            
        Returns:
            True if holiday, False otherwise
        """
        # Simple holiday detection for US federal holidays
        month = timestamp.month
        day = timestamp.day
        
        # Fixed date holidays
        fixed_holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas Day
        ]
        
        if (month, day) in fixed_holidays:
            return True
            
        # Martin Luther King Jr. Day (3rd Monday in January)
        if month == 1 and self._is_nth_weekday(timestamp, 1, 3):
            return True
            
        # Presidents Day (3rd Monday in February)
        if month == 2 and self._is_nth_weekday(timestamp, 1, 3):
            return True
            
        # Memorial Day (last Monday in May)
        if month == 5 and self._is_last_weekday(timestamp, 1):
            return True
            
        # Labor Day (1st Monday in September)
        if month == 9 and self._is_nth_weekday(timestamp, 1, 1):
            return True
            
        # Columbus Day (2nd Monday in October)
        if month == 10 and self._is_nth_weekday(timestamp, 1, 2):
            return True
            
        # Thanksgiving (4th Thursday in November)
        if month == 11 and self._is_nth_weekday(timestamp, 4, 4):
            return True
            
        return False
        
    def _is_nth_weekday(self, timestamp: datetime, weekday: int, n: int) -> bool:
        """Check if timestamp is the nth occurrence of weekday in month.
        
        Args:
            timestamp: Timestamp to check
            weekday: Day of week (0=Monday, 6=Sunday)
            n: Which occurrence (1st, 2nd, etc.)
            
        Returns:
            True if nth occurrence, False otherwise
        """
        if timestamp.weekday() != weekday:
            return False
            
        # Count occurrences of this weekday in the month
        first_day = timestamp.replace(day=1)
        count = 0
        current_day = first_day
        
        while current_day.month == timestamp.month:
            if current_day.weekday() == weekday:
                count += 1
                if current_day.day == timestamp.day:
                    return count == n
            current_day += timedelta(days=1)
            
        return False
        
    def _is_last_weekday(self, timestamp: datetime, weekday: int) -> bool:
        """Check if timestamp is the last occurrence of weekday in month.
        
        Args:
            timestamp: Timestamp to check
            weekday: Day of week (0=Monday, 6=Sunday)
            
        Returns:
            True if last occurrence, False otherwise
        """
        if timestamp.weekday() != weekday:
            return False
            
        # Check if there's another occurrence after this date
        next_week = timestamp + timedelta(days=7)
        return next_week.month != timestamp.month
        
    def get_hvac_schedule(self, timestamp: datetime, occupancy_ratio: float) -> Dict[str, Any]:
        """Get HVAC operational schedule.
        
        Args:
            timestamp: Current timestamp
            occupancy_ratio: Current occupancy ratio
            
        Returns:
            Dictionary with HVAC schedule parameters
        """
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5
        season = self._get_season(timestamp)
        
        # Determine if building systems should be running
        # HVAC typically starts 1-2 hours before occupancy
        pre_occupancy_start = 6
        post_occupancy_end = 20
        
        systems_running = True
        if is_weekend:
            # Weekend operation only if occupied or extreme weather
            systems_running = occupancy_ratio > 0.05
        elif hour < pre_occupancy_start or hour > post_occupancy_end:
            # Night setback - minimal operation
            systems_running = occupancy_ratio > 0.05
            
        # Temperature setpoints
        if occupancy_ratio > 0.1:  # Occupied
            cooling_sp = self.config['setpoints']['occupied']['cooling']
            heating_sp = self.config['setpoints']['occupied']['heating']
        else:  # Unoccupied
            cooling_sp = self.config['setpoints']['unoccupied']['cooling']
            heating_sp = self.config['setpoints']['unoccupied']['heating']
            
        return {
            'systems_running': systems_running,
            'cooling_setpoint': cooling_sp,
            'heating_setpoint': heating_sp,
            'ventilation_required': occupancy_ratio > 0.05,
            'economizer_enabled': season in ['spring', 'fall'],
            'night_setback': hour < pre_occupancy_start or hour > post_occupancy_end
        }
        
    def get_lighting_schedule(self, timestamp: datetime, occupancy_ratio: float) -> Dict[str, Any]:
        """Get lighting schedule parameters.
        
        Args:
            timestamp: Current timestamp
            occupancy_ratio: Current occupancy ratio
            
        Returns:
            Dictionary with lighting parameters
        """
        hour = timestamp.hour
        
        # Daylight hours (approximate)
        sunrise = 7
        sunset = 19
        
        # Natural light availability
        daylight_available = sunrise <= hour <= sunset
        
        # Lighting level based on occupancy and daylight
        if occupancy_ratio > 0.1:
            if daylight_available:
                lighting_level = 0.6  # Reduced due to daylight
            else:
                lighting_level = 1.0  # Full lighting
        elif occupancy_ratio > 0.02:
            lighting_level = 0.3  # Security/cleaning lighting
        else:
            lighting_level = 0.1  # Minimal safety lighting
            
        return {
            'lighting_level': lighting_level,
            'daylight_available': daylight_available,
            'occupancy_sensors_active': True,
            'automatic_dimming': daylight_available and occupancy_ratio > 0.1
        }
        
    def get_equipment_schedule(self, timestamp: datetime, equipment_type: str) -> Dict[str, Any]:
        """Get equipment-specific operational schedule.
        
        Args:
            timestamp: Current timestamp
            equipment_type: Type of equipment ('chiller', 'ahu', 'boiler', etc.)
            
        Returns:
            Dictionary with equipment schedule parameters
        """
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5
        season = self._get_season(timestamp)
        
        if equipment_type == 'chiller':
            # Chillers operate during cooling season and occupied hours
            operating = season in ['summer', 'spring'] or hour in range(8, 18)
            staging = 'lead' if operating else 'off'
            
        elif equipment_type == 'boiler':
            # Boilers operate during heating season
            operating = season in ['winter', 'fall']
            staging = 'lead' if operating else 'off'
            
        elif equipment_type == 'ahu':
            # AHUs operate during occupied hours plus pre/post conditioning
            operating = not is_weekend or hour in range(6, 20)
            staging = 'normal' if operating else 'off'
            
        elif equipment_type == 'vav':
            # VAVs modulate based on zone needs
            operating = True  # Always available
            staging = 'modulating'
            
        else:
            # Default schedule
            operating = hour in range(6, 20)
            staging = 'normal' if operating else 'off'
            
        return {
            'operating': operating,
            'staging': staging,
            'maintenance_mode': False,  # Could be expanded for scheduled maintenance
            'energy_savings_mode': is_weekend and hour not in range(8, 17)
        }
        
    def _get_season(self, timestamp: datetime) -> str:
        """Get season for timestamp.
        
        Args:
            timestamp: Timestamp to check
            
        Returns:
            Season name
        """
        month = timestamp.month
        
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
            
    def generate_annual_schedule(self, year: int = None) -> List[Dict[str, Any]]:
        """Generate annual occupancy schedule.
        
        Args:
            year: Year to generate schedule for (default: current year)
            
        Returns:
            List of schedule entries for the year
        """
        if year is None:
            year = datetime.now().year
            
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59)
        
        schedule_entries = []
        current_date = start_date
        
        while current_date <= end_date:
            occupancy = self.get_occupancy_ratio(current_date)
            hvac_schedule = self.get_hvac_schedule(current_date, occupancy)
            lighting_schedule = self.get_lighting_schedule(current_date, occupancy)
            
            entry = {
                'timestamp': current_date,
                'occupancy_ratio': occupancy,
                'is_weekend': current_date.weekday() >= 5,
                'is_holiday': self._is_holiday(current_date),
                'hvac': hvac_schedule,
                'lighting': lighting_schedule
            }
            
            schedule_entries.append(entry)
            current_date += timedelta(hours=1)  # Hourly schedule
            
        logger.info(f"Generated annual schedule with {len(schedule_entries)} entries")
        return schedule_entries