# Temperature Control PLC - Manages gas temperature
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class TemperatureControlPLC(BasePLC):
    """PLC for temperature monitoring and control"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "TEMPERATURE_CONTROL")
        self.temp_setpoint = 20.0  # °C
        self.temp_tolerance = 5.0  # °C
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        temperature = sensor_data.get(f'temperature_{self.node_id}', 20.0)
        self.update_input('TEMPERATURE_SENSOR', temperature)
        
    def execute_logic(self):
        """Execute temperature control logic"""
        temperature = self.get_input('TEMPERATURE_SENSOR', 20.0)
        
        if temperature > self.temp_setpoint + self.temp_tolerance:
            self.set_output('COOLING_FAN', True)
            self.set_output('HEATER', False)
        elif temperature < self.temp_setpoint - self.temp_tolerance:
            self.set_output('COOLING_FAN', False) 
            self.set_output('HEATER', True)
        else:
            self.set_output('COOLING_FAN', False)
            self.set_output('HEATER', False)
        
        self.set_output('TEMPERATURE_OK', abs(temperature - self.temp_setpoint) <= self.temp_tolerance)