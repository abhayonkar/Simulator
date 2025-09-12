# Gas Physics Engine - Simplified physics simulation
import logging
import random
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GasPhysicsEngine:
    """Physics simulation engine for gas pipeline"""
    
    def __init__(self):
        # Gas properties
        self.gas_density = 0.8  # kg/m³
        self.gas_viscosity = 1.1e-5  # Pa·s
        self.ambient_temperature = 20.0  # °C
        logger.info("Gas Physics Engine initialized")
    
    def load_gaslib_network(self) -> Dict[str, Any]:
        """Load GasLib-134 network data (simplified version)"""
        # Create a representative network based on GasLib-134 structure
        network_data = {
            'nodes': {
                'Source_1': {'type': 'source', 'x': 0, 'y': 0, 'pressure': 60.0, 'temperature': 20.0},
                'Junction_1': {'type': 'junction', 'x': 50, 'y': 25, 'pressure': 55.0, 'temperature': 20.0},
                'Junction_2': {'type': 'junction', 'x': 100, 'y': 50, 'pressure': 52.0, 'temperature': 20.0},
                'Compressor_1': {'type': 'compressor', 'x': 150, 'y': 75, 'pressure': 58.0, 'temperature': 25.0},
                'Junction_3': {'type': 'junction', 'x': 200, 'y': 100, 'pressure': 50.0, 'temperature': 22.0},
                'Junction_4': {'type': 'junction', 'x': 250, 'y': 125, 'pressure': 48.0, 'temperature': 22.0},
                'Sink_1': {'type': 'sink', 'x': 300, 'y': 150, 'pressure': 45.0, 'temperature': 20.0},
                'Sink_2': {'type': 'sink', 'x': 200, 'y': 0, 'pressure': 40.0, 'temperature': 20.0},
            },
            'pipes': {
                'Pipe_1': {'from_node': 'Source_1', 'to_node': 'Junction_1', 'length': 10.0, 'diameter': 0.8},
                'Pipe_2': {'from_node': 'Junction_1', 'to_node': 'Junction_2', 'length': 10.0, 'diameter': 0.8},
                'Pipe_3': {'from_node': 'Junction_2', 'to_node': 'Compressor_1', 'length': 12.0, 'diameter': 0.8},
                'Pipe_4': {'from_node': 'Compressor_1', 'to_node': 'Junction_3', 'length': 10.0, 'diameter': 0.8},
                'Pipe_5': {'from_node': 'Junction_3', 'to_node': 'Junction_4', 'length': 8.0, 'diameter': 0.6},
                'Pipe_6': {'from_node': 'Junction_4', 'to_node': 'Sink_1', 'length': 10.0, 'diameter': 0.6},
                'Pipe_7': {'from_node': 'Junction_2', 'to_node': 'Sink_2', 'length': 15.0, 'diameter': 0.4},
            }
        }
        
        logger.info(f"Loaded physics network: {len(network_data['nodes'])} nodes, {len(network_data['pipes'])} pipes")
        return network_data
    
    def simulate_step(self, network_data: Dict[str, Any], sensor_data: Dict[str, Any]):
        """Execute one physics simulation step"""
        try:
            nodes = network_data['nodes']
            pipes = network_data['pipes']
            
            # Update node pressures based on flow dynamics
            for node_id, node in nodes.items():
                # Add small pressure variations
                base_pressure = node['pressure']
                
                if node['type'] == 'source':
                    # Sources maintain pressure with small variations
                    node['pressure'] = base_pressure + random.gauss(0, 0.5)
                elif node['type'] == 'compressor':
                    # Compressors boost pressure when running
                    compressor_running = sensor_data.get(f'compressor_speed_{node_id}', 0) > 1000
                    if compressor_running:
                        node['pressure'] = min(80.0, base_pressure + 3.0)
                    else:
                        node['pressure'] = max(30.0, base_pressure - 1.0)
                elif node['type'] == 'sink':
                    # Sinks consume gas, reducing pressure
                    consumption = sensor_data.get(f'flow_{node_id}', 50.0)
                    pressure_drop = consumption / 100.0  # Simplified relationship
                    node['pressure'] = max(25.0, base_pressure - pressure_drop)
                else:
                    # Junctions have intermediate pressures
                    node['pressure'] = base_pressure + random.gauss(0, 0.2)
                
                # Temperature variations
                node['temperature'] = self.ambient_temperature + random.gauss(0, 1.0)
            
            # Update pipe flows based on pressure differences
            for pipe_id, pipe in pipes.items():
                from_node = nodes[pipe['from_node']]
                to_node = nodes[pipe['to_node']]
                
                # Simple flow calculation based on pressure difference
                pressure_diff = from_node['pressure'] - to_node['pressure']
                flow_capacity = (pipe['diameter'] ** 2) * 100  # Simplified
                
                # Flow is proportional to pressure difference and pipe capacity
                flow_rate = max(0, pressure_diff * flow_capacity / pipe['length'])
                
                # Store calculated values back to network data for sensors
                pipe['flow_rate'] = flow_rate
                pipe['pressure_drop'] = pressure_diff
            
        except Exception as e:
            logger.error(f"Physics simulation error: {e}")
    
    def calculate_flow_rate(self, pressure_in: float, pressure_out: float, 
                           diameter: float, length: float) -> float:
        """Calculate gas flow rate using simplified equation"""
        if pressure_in <= pressure_out:
            return 0.0
        
        # Simplified Weymouth equation
        pressure_diff_sq = pressure_in**2 - pressure_out**2
        flow_factor = (diameter**2.67) / (length**0.5)
        flow_rate = flow_factor * (pressure_diff_sq**0.5) * 0.01
        
        return max(0, flow_rate)