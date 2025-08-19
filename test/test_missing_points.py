"""Test script to verify all sensor points generate data."""

import yaml
from datetime import datetime
from src.generators.time_series import TimeSeriesGenerator

# Load configuration
with open('config/building_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create a mock entity map with all expected point IDs
entity_map = {}
point_id = 1000

# Add chiller points
for i in range(1, config['equipment']['chillers']['count'] + 1):
    for suffix in ['status', 'enable', 'chwSupplyTemp', 'chwReturnTemp', 
                   'condenserTemp', 'chwFlow', 'power', 'energy', 'cop']:
        entity_map[f"point-chiller-{i}-{suffix}"] = point_id
        point_id += 1

# Add AHU points
for i in range(1, config['equipment']['ahus']['count'] + 1):
    for suffix in ['status', 'enable', 'supplyTemp', 'returnTemp', 
                   'mixedTemp', 'supplyFanSpeed', 'staticPressure']:
        entity_map[f"point-ahu-{i}-{suffix}"] = point_id
        point_id += 1

# Add VAV points
total_floors = config['site']['floors']
zones = config['equipment']['vav_boxes']['zones']
for floor in range(1, total_floors + 1):
    for zone in zones:
        zone_key = zone.lower()
        for suffix in ['zoneTemp', 'zoneTempSp', 'airFlow', 'damperPos', 'occupied']:
            entity_map[f"point-vav-{floor}-{zone_key}-{suffix}"] = point_id
            point_id += 1

# Add meter points
entity_map["point-meter-main-electric-power"] = point_id
point_id += 1
entity_map["point-meter-main-electric-energy"] = point_id
point_id += 1
entity_map["point-meter-main-electric-powerFactor"] = point_id
point_id += 1
entity_map["point-meter-main-gas-flow"] = point_id
point_id += 1
entity_map["point-meter-main-gas-volume"] = point_id
point_id += 1
entity_map["point-meter-main-water-flow"] = point_id
point_id += 1
entity_map["point-meter-main-water-volume"] = point_id
point_id += 1

# Create generator and generate one timestamp of data
generator = TimeSeriesGenerator(config, entity_map)

# Test data generation for one timestamp
# Use high load conditions to ensure backup chiller runs
timestamp = datetime.now()
outdoor_temp = 95.0  # Hot day
season = 'summer'
occupancy_ratio = 0.95  # High occupancy

# Generate data
data_points = generator._generate_timestamp_data(
    timestamp, outdoor_temp, season, occupancy_ratio
)

# Track which points got data
points_with_data = set()
for dp in data_points:
    points_with_data.add(dp['entity_id'])

# Check for missing points
missing_points = []
sensor_points = []
command_points = []

for point_name, point_id in entity_map.items():
    # Skip command points (they shouldn't have sensor data)
    if 'enable' in point_name.lower() and 'command' not in point_name.lower():
        command_points.append(point_name)
        continue
    
    sensor_points.append(point_name)
    if point_id not in points_with_data:
        missing_points.append(point_name)

print(f"Total entity points defined: {len(entity_map)}")
print(f"Sensor points (should have data): {len(sensor_points)}")
print(f"Command points (no data expected): {len(command_points)}")
print(f"Data points generated: {len(data_points)}")
print(f"Unique points with data: {len(points_with_data)}")
print()

if missing_points:
    print(f"WARNING: MISSING DATA for {len(missing_points)} sensor points:")
    for point in sorted(missing_points):
        print(f"  - {point}")
else:
    print("SUCCESS: All sensor points have data generated!")

print()
print("Sample of generated data (first 10 points):")
for i, dp in enumerate(data_points[:10]):
    # Find point name from ID
    point_name = None
    for name, pid in entity_map.items():
        if pid == dp['entity_id']:
            point_name = name
            break
    
    value_key = 'value_n' if 'value_n' in dp else 'value_b'
    value = dp.get(value_key, 'N/A')
    print(f"  {point_name}: {value}")