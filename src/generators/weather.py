"""Weather simulation module for realistic outdoor conditions."""

import logging
import math
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WeatherSimulator:
    """Simulates realistic weather patterns for building simulation."""
    
    def __init__(self, config: Dict[str, Any], timezone: str = "America/New_York"):
        """Initialize weather simulator.
        
        Args:
            config: Weather configuration from building config
            timezone: Timezone for weather simulation
        """
        self.config = config
        self.timezone = timezone
        self.random_state = np.random.RandomState(42)
        
    def generate_weather_data(self, start_date: datetime, 
                            end_date: datetime, 
                            interval_minutes: int = 60) -> pd.DataFrame:
        """Generate weather data for date range.
        
        Args:
            start_date: Start date for weather data
            end_date: End date for weather data
            interval_minutes: Data interval in minutes
            
        Returns:
            DataFrame with weather data including:
            - timestamp
            - dry_bulb_temp (°F)
            - wet_bulb_temp (°F)
            - humidity (%)
            - wind_speed (mph)
            - solar_irradiance (W/m²)
            - cloud_cover (0-1)
            - season
        """
        logger.info(f"Generating weather data from {start_date} to {end_date}")
        
        # Create timestamp range
        timestamps = pd.date_range(
            start=start_date,
            end=end_date,
            freq=f'{interval_minutes}min'
        )
        
        weather_data = []
        
        for timestamp in timestamps:
            weather_point = self._generate_weather_point(timestamp)
            weather_data.append(weather_point)
            
        df = pd.DataFrame(weather_data)
        logger.info(f"Generated {len(df)} weather data points")
        
        return df
        
    def _generate_weather_point(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate weather data for a single timestamp.
        
        Args:
            timestamp: Timestamp for weather data
            
        Returns:
            Dictionary with weather parameters
        """
        # Determine season
        season = self._get_season(timestamp)
        season_config = self.config['seasons'][season]
        
        # Generate temperature with seasonal and daily variation
        dry_bulb_temp = self._generate_temperature(timestamp, season_config)
        
        # Generate humidity (inversely related to temperature)
        humidity = self._generate_humidity(dry_bulb_temp, season)
        
        # Calculate wet bulb temperature
        wet_bulb_temp = self._calculate_wet_bulb_temp(dry_bulb_temp, humidity)
        
        # Generate wind speed
        wind_speed = self._generate_wind_speed(season, timestamp.hour)
        
        # Generate solar irradiance
        solar_irradiance, cloud_cover = self._generate_solar_data(timestamp, season)
        
        return {
            'timestamp': timestamp,
            'dry_bulb_temp': round(dry_bulb_temp, 1),
            'wet_bulb_temp': round(wet_bulb_temp, 1),
            'humidity': round(humidity, 0),
            'wind_speed': round(wind_speed, 1),
            'solar_irradiance': round(solar_irradiance, 0),
            'cloud_cover': round(cloud_cover, 2),
            'season': season
        }
        
    def _get_season(self, timestamp: datetime) -> str:
        """Determine season from timestamp.
        
        Args:
            timestamp: Datetime to check
            
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
        else:  # 9, 10, 11
            return 'fall'
            
    def _generate_temperature(self, timestamp: datetime, 
                            season_config: Dict[str, float]) -> float:
        """Generate realistic temperature with seasonal and daily variation.
        
        Args:
            timestamp: Current timestamp
            season_config: Season configuration
            
        Returns:
            Temperature in Fahrenheit
        """
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        
        # Base temperature from season
        typical_temp = season_config['typical']
        temp_range = season_config['max'] - season_config['min']
        
        # Seasonal variation (sinusoidal over the year)
        # Peak summer around day 200, peak winter around day 20/385
        seasonal_offset = math.sin((day_of_year - 80) * 2 * math.pi / 365)
        seasonal_temp = typical_temp + seasonal_offset * (temp_range * 0.3)
        
        # Daily variation (cooler at night, warmer in afternoon)
        daily_amplitude = temp_range * 0.25  # Daily swing
        daily_offset = math.sin((hour - 6) * math.pi / 12)  # Peak at 2 PM
        daily_temp = daily_amplitude * daily_offset
        
        # Multi-day weather patterns (simulate weather fronts)
        multi_day_period = 7  # 7-day weather cycles
        multi_day_phase = (day_of_year % multi_day_period) * 2 * math.pi / multi_day_period
        multi_day_offset = math.sin(multi_day_phase) * (temp_range * 0.15)
        
        # Random noise
        noise = self.random_state.normal(0, 2.0)
        
        # Combine all factors
        temperature = seasonal_temp + daily_temp + multi_day_offset + noise
        
        # Clamp to reasonable bounds
        temperature = max(season_config['min'], 
                         min(season_config['max'], temperature))
        
        return temperature
        
    def _generate_humidity(self, temperature: float, season: str) -> float:
        """Generate relative humidity based on temperature and season.
        
        Args:
            temperature: Dry bulb temperature
            season: Season name
            
        Returns:
            Relative humidity percentage
        """
        # Base humidity by season
        season_humidity = {
            'winter': 45,
            'spring': 55,
            'summer': 70,
            'fall': 60
        }
        
        base_humidity = season_humidity[season]
        
        # Humidity tends to be inversely related to temperature
        temp_factor = -(temperature - 70) * 0.3
        
        # Add some randomness
        noise = self.random_state.normal(0, 8)
        
        humidity = base_humidity + temp_factor + noise
        
        # Clamp to valid range
        return max(20, min(95, humidity))
        
    def _calculate_wet_bulb_temp(self, dry_bulb: float, humidity: float) -> float:
        """Calculate wet bulb temperature from dry bulb and humidity.
        
        Args:
            dry_bulb: Dry bulb temperature (°F)
            humidity: Relative humidity (%)
            
        Returns:
            Wet bulb temperature (°F)
        """
        # Simplified wet bulb calculation
        # Convert to Celsius for calculation
        tc = (dry_bulb - 32) * 5/9
        rh_decimal = humidity / 100
        
        # Approximation formula
        tw_c = tc * math.atan(0.151977 * (rh_decimal * 100 + 8.313659) ** 0.5) + \
               math.atan(tc + rh_decimal * 100) - \
               math.atan(rh_decimal * 100 - 1.676331) + \
               0.00391838 * (rh_decimal * 100) ** 1.5 * math.atan(0.023101 * rh_decimal * 100) - 4.686035
        
        # Convert back to Fahrenheit
        tw_f = tw_c * 9/5 + 32
        
        # Wet bulb can't be higher than dry bulb
        return min(tw_f, dry_bulb)
        
    def _generate_wind_speed(self, season: str, hour: int) -> float:
        """Generate wind speed with seasonal and diurnal variation.
        
        Args:
            season: Season name
            hour: Hour of day
            
        Returns:
            Wind speed in mph
        """
        # Base wind speed by season
        season_wind = {
            'winter': 12,
            'spring': 10,
            'summer': 6,
            'fall': 8
        }
        
        base_wind = season_wind[season]
        
        # Diurnal variation (typically windier during day)
        if 8 <= hour <= 18:
            diurnal_factor = 1.2
        else:
            diurnal_factor = 0.8
            
        # Random variation
        noise = self.random_state.normal(0, base_wind * 0.3)
        
        wind_speed = base_wind * diurnal_factor + noise
        
        return max(0, wind_speed)
        
    def _generate_solar_data(self, timestamp: datetime, 
                           season: str) -> Tuple[float, float]:
        """Generate solar irradiance and cloud cover.
        
        Args:
            timestamp: Current timestamp
            season: Season name
            
        Returns:
            Tuple of (solar_irradiance W/m², cloud_cover 0-1)
        """
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        
        # No solar irradiance at night
        if hour < 6 or hour > 19:
            return 0.0, self.random_state.uniform(0.2, 0.8)
            
        # Calculate solar elevation angle (simplified)
        # Solar noon is around hour 12
        hour_angle = (hour - 12) * 15  # degrees
        
        # Declination angle varies with day of year
        declination = 23.45 * math.sin(math.radians((360/365) * (day_of_year - 81)))
        
        # Assume latitude of 40° (typical US)
        latitude = 40
        
        # Solar elevation angle
        elevation = math.asin(
            math.sin(math.radians(declination)) * math.sin(math.radians(latitude)) +
            math.cos(math.radians(declination)) * math.cos(math.radians(latitude)) *
            math.cos(math.radians(hour_angle))
        )
        
        # Convert to degrees and ensure positive
        elevation_deg = max(0, math.degrees(elevation))
        
        # Maximum possible irradiance (clear sky)
        max_irradiance = 1000 * math.sin(math.radians(elevation_deg))
        
        # Generate cloud cover (affects irradiance)
        # More clouds in spring/winter, fewer in summer
        season_cloudiness = {
            'winter': 0.6,
            'spring': 0.5,
            'summer': 0.3,
            'fall': 0.4
        }
        
        base_clouds = season_cloudiness[season]
        cloud_noise = self.random_state.normal(0, 0.2)
        cloud_cover = max(0, min(1, base_clouds + cloud_noise))
        
        # Reduce irradiance based on cloud cover
        cloud_factor = 1 - (cloud_cover * 0.8)  # Clouds block up to 80% of solar
        
        irradiance = max_irradiance * cloud_factor
        
        # Add some random variation
        irradiance += self.random_state.normal(0, irradiance * 0.1)
        
        return max(0, irradiance), cloud_cover
        
    def get_current_weather(self, timestamp: datetime) -> Dict[str, Any]:
        """Get weather conditions for a specific timestamp.
        
        Args:
            timestamp: Timestamp for weather
            
        Returns:
            Dictionary with current weather conditions
        """
        return self._generate_weather_point(timestamp)