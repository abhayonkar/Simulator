# Sensor Manager - Manages various sensor types
import random
import math
import logging
import time
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SensorManager:
    """Manages all sensors in the gas pipeline system"""
    
    def __init__(self):
        self.sensors = {}
        self.sensor_types = [
            'pressure', 'temperature', 'flow', 'vibration', 'gas_composition',
            'leak_detection', 'valve_position', 'compressor_status'
        ]
        logger.info("Sensor Manager initialized")
    
    def initialize_sensors(self, network_data: Dict[str, Any]):
        """Initialize sensors at network nodes"""
        nodes = network_data.get('nodes', {})
        pipes = network_data.get('pipes', {})
        
        # Create sensors for each node
        for node_id, node_data in nodes.items():
            node_type = node_data.get('type', 'junction')
            
            # Base sensors for all nodes
            self.add_sensor(f'pressure_{node_id}', 'pressure', node_id)
            self.add_sensor(f'temperature_{node_id}', 'temperature', node_id)
            
            # Type-specific sensors
            if node_type == 'source':
                self.add_sensor(f'flow_{node_id}', 'flow', node_id)
                self.add_sensor(f'gas_composition_{node_id}', 'gas_composition', node_id)
            elif node_type == 'compressor':
                self.add_sensor(f'compressor_speed_{node_id}', 'compressor_status', node_id)
                self.add_sensor(f'vibration_{node_id}', 'vibration', node_id)
                self.add_sensor(f'oil_temperature_{node_id}', 'temperature', node_id)
                self.add_sensor(f'suction_pressure_{node_id}', 'pressure', node_id)
                self.add_sensor(f'discharge_pressure_{node_id}', 'pressure', node_id)
            elif node_type == 'sink':
                self.add_sensor(f'flow_{node_id}', 'flow', node_id)
            
            # Safety sensors for all nodes
            self.add_sensor(f'gas_leak_{node_id}', 'leak_detection', node_id)
            self.add_sensor(f'fire_detector_{node_id}', 'leak_detection', node_id)
            
        # Sensors for pipes/valves
        for pipe_id, pipe_data in pipes.items():
            self.add_sensor(f'valve_position_{pipe_id}', 'valve_position', pipe_id)
            self.add_sensor(f'flow_{pipe_id}', 'flow', pipe_id)
            self.add_sensor(f'differential_pressure_{pipe_id}', 'pressure', pipe_id)
        
        logger.info(f"Initialized {len(self.sensors)} sensors")
    
    def add_sensor(self, sensor_id: str, sensor_type: str, location: str):
        """Add a sensor to the system"""
        self.sensors[sensor_id] = {
            'type': sensor_type,
            'location': location,
            'value': self.get_initial_value(sensor_type),
            'last_update': time.time(),
            'quality': 'GOOD',
            'calibration_date': datetime.now().isoformat()
        }
    
    def get_initial_value(self, sensor_type: str):
        """Get appropriate initial value for sensor type"""
        initial_values = {
            'pressure': 50.0,  # bar
            'temperature': 20.0,  # °C
            'flow': 100.0,  # kg/s
            'vibration': 0.5,  # mm/s
            'gas_composition': 95.0,  # % methane
            'leak_detection': False,
            'valve_position': 50.0,  # % open
            'compressor_status': 0  # RPM
        }
        return initial_values.get(sensor_type, 0.0)
    
    def update_all_sensors(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update all sensor readings"""
        sensor_data = {}
        current_time = time.time()
        
        for sensor_id, sensor in self.sensors.items():
            # Simulate sensor reading based on type and network conditions
            new_value = self.simulate_sensor_reading(sensor, network_data, current_time)
            sensor['value'] = new_value
            sensor['last_update'] = current_time
            sensor_data[sensor_id] = new_value
        
        return sensor_data
    
    def simulate_sensor_reading(self, sensor: Dict[str, Any], network_data: Dict[str, Any], current_time: float):
        """Simulate realistic sensor reading"""
        sensor_type = sensor['type']
        location = sensor['location']
        current_value = sensor['value']
        
        # Base simulation with some noise and drift
        if sensor_type == 'pressure':
            # Pressure varies with small random fluctuations
            base_pressure = network_data.get('nodes', {}).get(location, {}).get('pressure', 50.0)
            noise = random.gauss(0, 0.5)  # Small pressure noise
            return max(0, base_pressure + noise)
        
        elif sensor_type == 'temperature':
            # Temperature changes slowly
            ambient = 20.0
            seasonal_variation = 5.0 * math.sin(current_time / 8640)  # Daily variation
            noise = random.gauss(0, 0.1)
            return ambient + seasonal_variation + noise
        
        elif sensor_type == 'flow':
            # Flow rate with some variation
            base_flow = 100.0
            variation = random.gauss(0, 5.0)
            return max(0, base_flow + variation)
        
        elif sensor_type == 'vibration':
            # Vibration increases over time (wear)
            base_vibration = 0.5
            wear_factor = min(2.0, current_time / 100000)  # Increases over time
            noise = random.gauss(0, 0.1)
            return max(0, base_vibration + wear_factor + noise)
        
        elif sensor_type == 'gas_composition':
            # Gas composition is fairly stable
            base_composition = 95.0  # % methane
            drift = random.gauss(0, 0.5)
            return max(90.0, min(100.0, base_composition + drift))
        
        elif sensor_type == 'leak_detection':
            # Leak detection - mostly false, occasional random "leak"
            return random.random() < 0.001  # 0.1% chance of detected leak
        
        elif sensor_type == 'valve_position':
            # Valve position changes slowly
            target_position = 50.0  # Default 50% open
            # Move slowly towards target
            diff = target_position - current_value
            movement = diff * 0.1  # 10% of difference per update
            return max(0, min(100, current_value + movement))
        
        elif sensor_type == 'compressor_status':
            # Compressor RPM - either off (0) or running (~3000 RPM)
            if location.startswith('compressor') or 'compressor' in location:
                if random.random() < 0.8:  # 80% chance of running
                    return 3000 + random.gauss(0, 50)  # Some RPM variation
                else:
                    return 0
            else:
                return 0
        
        else:
            # Default: small random walk
            change = random.gauss(0, abs(current_value) * 0.01 + 0.1)
            return current_value + change
    
    def get_sensor_data(self, sensor_id: str) -> Dict[str, Any]:
        """Get specific sensor data"""
        return self.sensors.get(sensor_id, {})
    
    def get_all_sensor_data(self) -> Dict[str, Any]:
        """Get all sensor data"""
        return {sid: sensor['value'] for sid, sensor in self.sensors.items()}
    
    def get_active_sensor_count(self) -> int:
        """Get count of active sensors"""
        return len([s for s in self.sensors.values() if s.get('quality') == 'GOOD'])