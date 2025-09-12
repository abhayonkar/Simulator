# Flow Regulation PLC - Manages gas flow rates through pipes
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class FlowRegulationPLC(BasePLC):
    """PLC for flow regulation and control"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "FLOW_REGULATION")
        
        # Flow control parameters
        self.flow_setpoint = 100.0  # kg/s
        self.flow_tolerance = 5.0   # kg/s
        self.flow_high_limit = 200.0 # kg/s
        self.flow_low_limit = 0.0    # kg/s
        
        # Flow totalizer
        self.total_flow = 0.0
        self.flow_rate_previous = 0.0
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Flow meter reading
        flow_rate = sensor_data.get(f'flow_{self.node_id}', 100.0)
        self.update_input('FLOW_METER', flow_rate)
        
        # Differential pressure for flow calculation
        dp = sensor_data.get(f'differential_pressure_{self.node_id}', 10.0)
        self.update_input('DIFFERENTIAL_PRESSURE', dp)
        
        # Flow setpoint
        setpoint = sensor_data.get(f'flow_setpoint_{self.node_id}', self.flow_setpoint)
        self.update_input('FLOW_SETPOINT', setpoint)
        
        # Temperature for flow compensation
        temperature = sensor_data.get(f'temperature_{self.node_id}', 20.0)
        self.update_input('TEMPERATURE', temperature)
        
    def execute_logic(self):
        """Execute flow regulation ladder logic"""
        # Get current readings
        current_flow = self.get_input('FLOW_METER', 100.0)
        setpoint = self.get_input('FLOW_SETPOINT', self.flow_setpoint)
        temperature = self.get_input('TEMPERATURE', 20.0)
        
        # Temperature compensation (simplified)
        temp_factor = (temperature + 273.15) / 293.15  # Standard temperature 20°C
        compensated_flow = current_flow * temp_factor
        
        # Flow rate monitoring
        if compensated_flow > self.flow_high_limit:
            self.add_alarm('HIGH_FLOW', 'MEDIUM', f'Flow rate {compensated_flow:.1f} kg/s exceeds limit')
            self.set_output('FLOW_LIMITER_VALVE', True)
        elif compensated_flow < self.flow_low_limit and setpoint > 0:
            self.add_alarm('LOW_FLOW', 'MEDIUM', f'Flow rate {compensated_flow:.1f} kg/s below expected')
            self.set_output('FLOW_BOOSTER', True)
        else:
            self.set_output('FLOW_LIMITER_VALVE', False)
            self.set_output('FLOW_BOOSTER', False)
        
        # Flow control valve positioning
        flow_error = setpoint - compensated_flow
        if abs(flow_error) > self.flow_tolerance:
            if flow_error > 0:
                # Need more flow - open valve
                current_position = self.get_output('FLOW_CONTROL_VALVE', 50)
                new_position = min(100, current_position + 2)
            else:
                # Need less flow - close valve
                current_position = self.get_output('FLOW_CONTROL_VALVE', 50)
                new_position = max(0, current_position - 2)
            self.set_output('FLOW_CONTROL_VALVE', new_position)
        
        # Flow totalizer
        if abs(current_flow - self.flow_rate_previous) < 100:  # Avoid spikes
            self.total_flow += (current_flow * self.scan_time)
        self.flow_rate_previous = current_flow
        
        # Status outputs
        self.set_output('FLOW_IN_TOLERANCE', abs(flow_error) <= self.flow_tolerance)
        self.set_output('FLOW_TOTALIZER', self.total_flow)
        
        # Update memory
        self.memory['CURRENT_FLOW'] = compensated_flow
        self.memory['FLOW_ERROR'] = flow_error
        self.memory['TOTAL_FLOW'] = self.total_flow