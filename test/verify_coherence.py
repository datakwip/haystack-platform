"""Verify coherence of the generated data relationships."""

import yaml
from datetime import datetime
from src.generators.time_series import TimeSeriesGenerator

# Load configuration
with open('config/building_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create a mock entity map
entity_map = {}
point_id = 1000

# Add all points (simplified)
point_names = []

# Add VAV points first (needed for complete generation)
total_floors = config['site']['floors']
zones = config['equipment']['vav_boxes']['zones']
for floor in range(1, total_floors + 1):
    for zone in zones:
        zone_key = zone.lower()
        for suffix in ['zoneTemp', 'zoneTempSp', 'airFlow', 'damperPos', 'occupied']:
            name = f"point-vav-{floor}-{zone_key}-{suffix}"
            entity_map[name] = point_id
            point_id += 1

# Add gas and water meter points
entity_map["point-meter-main-gas-flow"] = point_id
point_id += 1
entity_map["point-meter-main-gas-volume"] = point_id
point_id += 1
entity_map["point-meter-main-water-flow"] = point_id
point_id += 1
entity_map["point-meter-main-water-volume"] = point_id
point_id += 1

for i in range(1, 3):  # 2 chillers
    for suffix in ['status', 'chwSupplyTemp', 'chwReturnTemp', 'condenserTemp', 
                   'chwFlow', 'power', 'energy', 'cop']:
        name = f"point-chiller-{i}-{suffix}"
        entity_map[name] = point_id
        point_names.append(name)
        point_id += 1

for i in range(1, 5):  # 4 AHUs
    for suffix in ['status', 'supplyTemp', 'returnTemp', 'mixedTemp', 
                   'supplyFanSpeed', 'staticPressure']:
        name = f"point-ahu-{i}-{suffix}"
        entity_map[name] = point_id
        point_names.append(name)
        point_id += 1

# Add meter points
for suffix in ['power', 'energy', 'powerFactor']:
    name = f"point-meter-main-electric-{suffix}"
    entity_map[name] = point_id
    point_names.append(name)
    point_id += 1

# Generate data for multiple scenarios
scenarios = [
    ("Low Load", 65.0, 'spring', 0.2),
    ("Medium Load", 75.0, 'summer', 0.5),
    ("High Load", 95.0, 'summer', 0.95),
    ("Winter Heating", 30.0, 'winter', 0.7),
]

print("COHERENCE VERIFICATION REPORT")
print("=" * 60)

for scenario_name, outdoor_temp, season, occupancy in scenarios:
    print(f"\nScenario: {scenario_name}")
    print(f"  Outdoor Temp: {outdoor_temp}°F, Season: {season}, Occupancy: {occupancy*100:.0f}%")
    print("-" * 40)
    
    generator = TimeSeriesGenerator(config, entity_map)
    timestamp = datetime.now()
    
    data_points = generator._generate_timestamp_data(
        timestamp, outdoor_temp, season, occupancy
    )
    
    # Convert to dict for easy lookup
    data_dict = {}
    for dp in data_points:
        for name, pid in entity_map.items():
            if pid == dp['entity_id']:
                value_key = 'value_n' if 'value_n' in dp else 'value_b'
                data_dict[name] = dp.get(value_key, None)
                break
    
    # Verify Chiller Coherence
    print("\n  CHILLER COHERENCE:")
    for i in range(1, 3):
        if f"point-chiller-{i}-status" in data_dict:
            status = data_dict.get(f"point-chiller-{i}-status", False)
            if status:
                supply = data_dict.get(f"point-chiller-{i}-chwSupplyTemp", 0)
                return_ = data_dict.get(f"point-chiller-{i}-chwReturnTemp", 0)
                condenser = data_dict.get(f"point-chiller-{i}-condenserTemp", 0)
                cop = data_dict.get(f"point-chiller-{i}-cop", 0)
                
                print(f"    Chiller {i}:")
                print(f"      Supply: {supply:.1f}°F, Return: {return_:.1f}°F, Delta-T: {return_-supply:.1f}°F")
                print(f"      Condenser: {condenser:.1f}°F (Outdoor+{condenser-outdoor_temp:.1f}°F)")
                print(f"      COP: {cop:.2f}")
                
                # Verify relationships
                if return_ <= supply:
                    print(f"      ERROR: Return temp <= Supply temp!")
                if condenser <= outdoor_temp:
                    print(f"      ERROR: Condenser temp <= Outdoor temp!")
                if condenser <= return_:
                    print(f"      ERROR: Condenser temp <= Return temp!")
    
    # Verify AHU Coherence
    print("\n  AHU COHERENCE:")
    for i in range(1, 3):  # Just check first 2 AHUs
        if f"point-ahu-{i}-status" in data_dict:
            status = data_dict.get(f"point-ahu-{i}-status", False)
            if status:
                supply = data_dict.get(f"point-ahu-{i}-supplyTemp", 0)
                return_ = data_dict.get(f"point-ahu-{i}-returnTemp", 0)
                mixed = data_dict.get(f"point-ahu-{i}-mixedTemp", 0)
                fan_speed = data_dict.get(f"point-ahu-{i}-supplyFanSpeed", 0)
                static = data_dict.get(f"point-ahu-{i}-staticPressure", 0)
                
                print(f"    AHU {i}:")
                print(f"      Temps - Mixed: {mixed:.1f}°F, Supply: {supply:.1f}°F, Return: {return_:.1f}°F")
                print(f"      Mixed vs Outdoor/Return: {mixed:.1f} should be between {min(outdoor_temp, return_):.1f}-{max(outdoor_temp, return_):.1f}")
                print(f"      Fan: {fan_speed:.0f}%, Static: {static:.2f} inH2O")
                
                # Verify mixed air is between outdoor and return
                if not (min(outdoor_temp, return_) - 5 <= mixed <= max(outdoor_temp, return_) + 5):
                    print(f"      WARNING: Mixed air temp outside expected range!")
    
    # Verify Energy Totalizers
    print("\n  TOTALIZER COHERENCE:")
    electric_power = data_dict.get("point-meter-main-electric-power", 0)
    electric_energy = data_dict.get("point-meter-main-electric-energy", 0)
    power_factor = data_dict.get("point-meter-main-electric-powerFactor", 0)
    
    print(f"    Electric - Power: {electric_power:.1f} kW, Energy: {electric_energy:.1f} kWh")
    print(f"    Power Factor: {power_factor:.3f}")
    
    # Energy should be accumulating
    if electric_energy > 0:
        print(f"    Energy is accumulating (good)")
    
print("\n" + "=" * 60)
print("COHERENCE VERIFICATION COMPLETE")