"""Sensor behavior models for realistic data generation."""

import logging
import math
import random
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SensorType(Enum):
    """Types of sensors with different characteristics."""
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW = "flow"
    POWER = "power"
    BOOLEAN = "boolean"
    POSITION = "position"
    HUMIDITY = "humidity"
    SPEED = "speed"


@dataclass
class SensorCharacteristics:
    """Physical characteristics of a sensor."""
    sensor_type: SensorType
    accuracy_percent: float = 1.0  # ±% of reading
    resolution: float = 0.1  # Minimum detectable change
    response_time_seconds: float = 30.0  # Time constant
    drift_rate_per_day: float = 0.01  # % per day
    noise_stddev: float = 0.1  # Standard deviation of noise
    min_value: float = 0.0
    max_value: float = 100.0
    
    
class SensorModel:
    """Models realistic sensor behavior including noise, drift, and failures."""
    
    def __init__(self, sensor_id: str, characteristics: SensorCharacteristics):
        """Initialize sensor model.
        
        Args:
            sensor_id: Unique identifier for sensor
            characteristics: Physical characteristics of the sensor
        """
        self.sensor_id = sensor_id
        self.char = characteristics
        self.last_calibration = datetime.now()
        self.accumulated_drift = 0.0
        self.last_value = None
        self.last_timestamp = None
        self.failure_mode = None
        self.random = random.Random(hash(sensor_id))  # Reproducible per sensor
        
    def read_value(self, true_value: float, timestamp: datetime) -> Tuple[float, str]:
        """Simulate sensor reading with realistic effects.
        
        Args:
            true_value: Actual physical value being measured
            timestamp: Current timestamp
            
        Returns:
            Tuple of (sensor_reading, status)
        """
        # Check for failure modes
        if self.failure_mode:
            return self._handle_failure_mode(true_value, timestamp)
            
        # Calculate drift since last calibration
        days_since_cal = (timestamp - self.last_calibration).total_seconds() / 86400
        drift_amount = self.char.drift_rate_per_day * days_since_cal
        
        # Apply sensor lag (first-order response)
        if self.last_value is not None and self.last_timestamp is not None:
            dt = (timestamp - self.last_timestamp).total_seconds()
            tau = self.char.response_time_seconds
            alpha = 1 - math.exp(-dt / tau) if tau > 0 else 1.0
            lagged_value = self.last_value + alpha * (true_value - self.last_value)
        else:
            lagged_value = true_value
            
        # Add drift
        drifted_value = lagged_value * (1 + drift_amount / 100)
        
        # Add accuracy error (systematic)
        accuracy_error = self.char.accuracy_percent / 100 * drifted_value
        accuracy_error *= self.random.uniform(-1, 1)
        
        # Add noise (random)
        noise = self.random.gauss(0, self.char.noise_stddev)
        
        # Combine all effects
        sensor_reading = drifted_value + accuracy_error + noise
        
        # Apply resolution quantization
        if self.char.resolution > 0:
            sensor_reading = round(sensor_reading / self.char.resolution) * self.char.resolution
            
        # Clamp to physical limits
        sensor_reading = max(self.char.min_value, 
                           min(self.char.max_value, sensor_reading))
        
        # Update state
        self.last_value = sensor_reading
        self.last_timestamp = timestamp
        
        # Determine status
        status = self._determine_status(sensor_reading, true_value, drift_amount)
        
        return sensor_reading, status
        
    def _determine_status(self, sensor_reading: float, true_value: float, 
                         drift_amount: float) -> str:
        """Determine data quality status.
        
        Args:
            sensor_reading: Sensor reading value
            true_value: True physical value
            drift_amount: Current drift percentage
            
        Returns:
            Status string
        """
        # Check for excessive drift
        if abs(drift_amount) > 2.0:  # 2% drift threshold
            return "stale"
            
        # Check for out-of-range readings
        if (sensor_reading <= self.char.min_value or 
            sensor_reading >= self.char.max_value):
            return "fault"
            
        # Random communication issues (1% chance)
        if self.random.random() < 0.01:
            return "stale"
            
        return "ok"
        
    def _handle_failure_mode(self, true_value: float, timestamp: datetime) -> Tuple[float, str]:
        """Handle sensor failure modes.
        
        Args:
            true_value: True physical value
            timestamp: Current timestamp
            
        Returns:
            Tuple of (failed_reading, status)
        """
        if self.failure_mode == "stuck":
            # Sensor stuck at last reading
            return self.last_value or 0.0, "fault"
            
        elif self.failure_mode == "noisy":
            # Excessive noise
            noise = self.random.gauss(0, self.char.noise_stddev * 10)
            return true_value + noise, "fault"
            
        elif self.failure_mode == "offset":
            # Fixed offset error
            offset = self.char.max_value * 0.1  # 10% offset
            return true_value + offset, "fault"
            
        elif self.failure_mode == "communication":
            # Communication failure
            return self.last_value or 0.0, "stale"
            
        return true_value, "fault"
        
    def calibrate(self, timestamp: datetime):
        """Calibrate sensor (reset drift).
        
        Args:
            timestamp: Calibration timestamp
        """
        self.last_calibration = timestamp
        self.accumulated_drift = 0.0
        logger.info(f"Sensor {self.sensor_id} calibrated at {timestamp}")
        
    def induce_failure(self, failure_mode: str):
        """Induce a failure mode for testing.
        
        Args:
            failure_mode: Type of failure ('stuck', 'noisy', 'offset', 'communication')
        """
        self.failure_mode = failure_mode
        logger.warning(f"Sensor {self.sensor_id} failure induced: {failure_mode}")
        
    def clear_failure(self):
        """Clear failure mode."""
        self.failure_mode = None
        logger.info(f"Sensor {self.sensor_id} failure cleared")


class SensorFactory:
    """Factory for creating sensor models with realistic characteristics."""
    
    @staticmethod
    def create_temperature_sensor(sensor_id: str, range_f: Tuple[float, float] = (-20, 120)) -> SensorModel:
        """Create temperature sensor model.
        
        Args:
            sensor_id: Sensor identifier
            range_f: Temperature range in Fahrenheit
            
        Returns:
            SensorModel configured for temperature
        """
        char = SensorCharacteristics(
            sensor_type=SensorType.TEMPERATURE,
            accuracy_percent=0.5,  # ±0.5% typical for RTD
            resolution=0.1,  # 0.1°F
            response_time_seconds=15.0,
            drift_rate_per_day=0.005,  # 0.005% per day
            noise_stddev=0.1,
            min_value=range_f[0],
            max_value=range_f[1]
        )
        return SensorModel(sensor_id, char)
        
    @staticmethod
    def create_pressure_sensor(sensor_id: str, range_psi: Tuple[float, float] = (0, 100)) -> SensorModel:
        """Create pressure sensor model."""
        char = SensorCharacteristics(
            sensor_type=SensorType.PRESSURE,
            accuracy_percent=0.25,  # ±0.25% typical
            resolution=0.1,
            response_time_seconds=2.0,  # Fast response
            drift_rate_per_day=0.01,
            noise_stddev=0.05,
            min_value=range_psi[0],
            max_value=range_psi[1]
        )
        return SensorModel(sensor_id, char)
        
    @staticmethod
    def create_flow_sensor(sensor_id: str, range_gpm: Tuple[float, float] = (0, 1000)) -> SensorModel:
        """Create flow sensor model."""
        char = SensorCharacteristics(
            sensor_type=SensorType.FLOW,
            accuracy_percent=1.0,  # ±1% typical for mag flow meter
            resolution=1.0,
            response_time_seconds=5.0,
            drift_rate_per_day=0.02,
            noise_stddev=2.0,
            min_value=range_gpm[0],
            max_value=range_gpm[1]
        )
        return SensorModel(sensor_id, char)
        
    @staticmethod
    def create_power_sensor(sensor_id: str, range_kw: Tuple[float, float] = (0, 1000)) -> SensorModel:
        """Create power sensor model."""
        char = SensorCharacteristics(
            sensor_type=SensorType.POWER,
            accuracy_percent=0.5,  # ±0.5% typical
            resolution=0.1,
            response_time_seconds=1.0,  # Very fast
            drift_rate_per_day=0.005,
            noise_stddev=0.5,
            min_value=range_kw[0],
            max_value=range_kw[1]
        )
        return SensorModel(sensor_id, char)
        
    @staticmethod
    def create_position_sensor(sensor_id: str, range_percent: Tuple[float, float] = (0, 100)) -> SensorModel:
        """Create position sensor (damper, valve) model."""
        char = SensorCharacteristics(
            sensor_type=SensorType.POSITION,
            accuracy_percent=2.0,  # ±2% typical for actuator feedback
            resolution=1.0,  # 1%
            response_time_seconds=10.0,
            drift_rate_per_day=0.01,
            noise_stddev=0.5,
            min_value=range_percent[0],
            max_value=range_percent[1]
        )
        return SensorModel(sensor_id, char)
        
    @staticmethod
    def create_humidity_sensor(sensor_id: str) -> SensorModel:
        """Create humidity sensor model."""
        char = SensorCharacteristics(
            sensor_type=SensorType.HUMIDITY,
            accuracy_percent=3.0,  # ±3% typical
            resolution=1.0,  # 1% RH
            response_time_seconds=60.0,  # Slow response
            drift_rate_per_day=0.05,  # Higher drift
            noise_stddev=1.0,
            min_value=0.0,
            max_value=100.0
        )
        return SensorModel(sensor_id, char)


class SensorNetwork:
    """Manages a network of sensors with coordinated behaviors."""
    
    def __init__(self):
        """Initialize sensor network."""
        self.sensors: Dict[str, SensorModel] = {}
        self.maintenance_schedule: Dict[str, datetime] = {}
        
    def add_sensor(self, sensor: SensorModel):
        """Add sensor to network.
        
        Args:
            sensor: SensorModel to add
        """
        self.sensors[sensor.sensor_id] = sensor
        
    def read_all_sensors(self, true_values: Dict[str, float], 
                        timestamp: datetime) -> Dict[str, Tuple[float, str]]:
        """Read all sensors in network.
        
        Args:
            true_values: Dictionary of sensor_id -> true_value
            timestamp: Current timestamp
            
        Returns:
            Dictionary of sensor_id -> (reading, status)
        """
        readings = {}
        
        for sensor_id, sensor in self.sensors.items():
            if sensor_id in true_values:
                reading, status = sensor.read_value(true_values[sensor_id], timestamp)
                readings[sensor_id] = (reading, status)
                
                # Check for scheduled maintenance
                if (sensor_id in self.maintenance_schedule and 
                    timestamp >= self.maintenance_schedule[sensor_id]):
                    sensor.calibrate(timestamp)
                    del self.maintenance_schedule[sensor_id]
                    
        return readings
        
    def schedule_maintenance(self, sensor_id: str, maintenance_time: datetime):
        """Schedule sensor maintenance/calibration.
        
        Args:
            sensor_id: Sensor to maintain
            maintenance_time: When to perform maintenance
        """
        if sensor_id in self.sensors:
            self.maintenance_schedule[sensor_id] = maintenance_time
            logger.info(f"Maintenance scheduled for {sensor_id} at {maintenance_time}")
            
    def simulate_failure_event(self, sensor_id: str, failure_mode: str, 
                             duration_hours: float = 1.0):
        """Simulate sensor failure for testing.
        
        Args:
            sensor_id: Sensor to fail
            failure_mode: Type of failure
            duration_hours: How long failure lasts
        """
        if sensor_id in self.sensors:
            sensor = self.sensors[sensor_id]
            sensor.induce_failure(failure_mode)
            
            # Schedule automatic recovery
            recovery_time = datetime.now() + timedelta(hours=duration_hours)
            self.maintenance_schedule[sensor_id] = recovery_time