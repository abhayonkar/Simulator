# Pressure Control PLC - Manages pressure regulation at key nodes
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class PressureControlPLC(BasePLC):
    """PLC for pressure control and regulation"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "PRESSURE_CONTROL")
        
        # Pressure control parameters
        self.pressure_setpoint = 50.0  # bar
        self.pressure_tolerance = 2.0  # bar
        self.pressure_high_limit = 80.0  # bar
        self.pressure_low_limit = 5.0   # bar
        
        # PID control parameters
        self.kp = 1.0  # Proportional gain
        self.ki = 0.1  # Integral gain
        self.kd = 0.01 # Derivative gain
        self.integral_error = 0.0
        self.last_error = 0.0
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Pressure sensor
        pressure = sensor_data.get(f'pressure_{self.node_id}', 50.0)
        self.update_input('PRESSURE_SENSOR', pressure)
        
        # Pressure transmitter
        pressure_transmitter = sensor_data.get(f'pressure_transmitter_{self.node_id}', pressure)
        self.update_input('PRESSURE_TRANSMITTER', pressure_transmitter)
        
        # Manual setpoint input
        manual_setpoint = sensor_data.get(f'manual_setpoint_{self.node_id}', self.pressure_setpoint)
        self.update_input('MANUAL_SETPOINT', manual_setpoint)
        
    def execute_logic(self):
        """Execute pressure control ladder logic"""
        # Get current pressure readings
        current_pressure = self.get_input('PRESSURE_SENSOR', 50.0)
        setpoint = self.get_input('MANUAL_SETPOINT', self.pressure_setpoint)
        
        # Safety checks
        if current_pressure > self.pressure_high_limit:
            self.add_alarm('HIGH_PRESSURE', 'HIGH', f'Pressure {current_pressure:.1f} bar exceeds limit {self.pressure_high_limit} bar')
            self.set_output('PRESSURE_RELIEF_VALVE', True)
            self.set_output('EMERGENCY_VENT', True)
        elif current_pressure < self.pressure_low_limit:
            self.add_alarm('LOW_PRESSURE', 'MEDIUM', f'Pressure {current_pressure:.1f} bar below limit {self.pressure_low_limit} bar')
            self.set_output('BOOSTER_PUMP', True)
        else:
            self.set_output('PRESSURE_RELIEF_VALVE', False)
            self.set_output('EMERGENCY_VENT', False)
            self.set_output('BOOSTER_PUMP', False)
        
        # PID control for pressure regulation
        error = setpoint - current_pressure
        self.integral_error += error * self.scan_time
        derivative_error = (error - self.last_error) / self.scan_time
        
        pid_output = (self.kp * error + 
                     self.ki * self.integral_error + 
                     self.kd * derivative_error)
        
        # Convert PID output to control valve position (0-100%)
        valve_position = max(0, min(100, 50 + pid_output))
        self.set_output('CONTROL_VALVE_POSITION', valve_position)
        
        # Pressure regulation status
        in_tolerance = abs(error) <= self.pressure_tolerance
        self.set_output('PRESSURE_IN_TOLERANCE', in_tolerance)
        
        # Store for next iteration
        self.last_error = error
        
        # Update memory registers
        self.memory['CURRENT_PRESSURE'] = current_pressure
        self.memory['PRESSURE_ERROR'] = error
        self.memory['PID_OUTPUT'] = pid_output