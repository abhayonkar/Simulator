# Valve Control PLC - Manages various valve operations
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class ValveControlPLC(BasePLC):
    """PLC for valve control and monitoring"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "VALVE_CONTROL")
        
        # Valve parameters
        self.valve_positions = {}  # Track multiple valves
        self.valve_travel_time = 30.0  # seconds for full stroke
        self.position_tolerance = 2.0  # % tolerance
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Main control valve position
        valve_position = sensor_data.get(f'valve_position_{self.node_id}', 50.0)
        self.update_input('MAIN_VALVE_POSITION', valve_position)
        
        # Valve position feedback
        position_feedback = sensor_data.get(f'position_feedback_{self.node_id}', valve_position)
        self.update_input('POSITION_FEEDBACK', position_feedback)
        
        # Valve commands
        open_command = sensor_data.get(f'valve_open_{self.node_id}', False)
        self.update_input('OPEN_COMMAND', open_command)
        
        close_command = sensor_data.get(f'valve_close_{self.node_id}', False)
        self.update_input('CLOSE_COMMAND', close_command)
        
        # Position setpoint
        position_setpoint = sensor_data.get(f'position_setpoint_{self.node_id}', 50.0)
        self.update_input('POSITION_SETPOINT', position_setpoint)
        
        # Limit switches
        fully_open = sensor_data.get(f'valve_fully_open_{self.node_id}', False)
        self.update_input('FULLY_OPEN_LS', fully_open)
        
        fully_closed = sensor_data.get(f'valve_fully_closed_{self.node_id}', False)
        self.update_input('FULLY_CLOSED_LS', fully_closed)
        
        # Torque sensor
        torque = sensor_data.get(f'valve_torque_{self.node_id}', 0.0)
        self.update_input('VALVE_TORQUE', torque)
        
    def execute_logic(self):
        """Execute valve control ladder logic"""
        # Get current readings
        current_position = self.get_input('POSITION_FEEDBACK', 50.0)
        position_setpoint = self.get_input('POSITION_SETPOINT', 50.0)
        open_command = self.get_input('OPEN_COMMAND', False)
        close_command = self.get_input('CLOSE_COMMAND', False)
        fully_open = self.get_input('FULLY_OPEN_LS', False)
        fully_closed = self.get_input('FULLY_CLOSED_LS', False)
        torque = self.get_input('VALVE_TORQUE', 0.0)
        
        # Safety checks
        if torque > 500.0:  # Nm - high torque limit
            self.add_alarm('HIGH_TORQUE', 'HIGH', f'Valve torque {torque:.1f} Nm exceeds limit')
            self.set_output('TORQUE_LIMIT_ACTIVE', True)
        else:
            self.set_output('TORQUE_LIMIT_ACTIVE', False)
        
        # Position error calculation
        position_error = position_setpoint - current_position
        position_in_tolerance = abs(position_error) <= self.position_tolerance
        
        # Valve movement control
        if not self.get_output('TORQUE_LIMIT_ACTIVE', False):
            if open_command and not fully_open:
                self.set_output('VALVE_OPEN', True)
                self.set_output('VALVE_CLOSE', False)
                self.set_output('VALVE_MOVING', True)
            elif close_command and not fully_closed:
                self.set_output('VALVE_OPEN', False)
                self.set_output('VALVE_CLOSE', True)
                self.set_output('VALVE_MOVING', True)
            elif not position_in_tolerance:
                # Automatic positioning
                if position_error > self.position_tolerance:
                    self.set_output('VALVE_OPEN', True)
                    self.set_output('VALVE_CLOSE', False)
                    self.set_output('VALVE_MOVING', True)
                elif position_error < -self.position_tolerance:
                    self.set_output('VALVE_OPEN', False)
                    self.set_output('VALVE_CLOSE', True)
                    self.set_output('VALVE_MOVING', True)
            else:
                # Stop movement - in position
                self.set_output('VALVE_OPEN', False)
                self.set_output('VALVE_CLOSE', False)
                self.set_output('VALVE_MOVING', False)
        else:
            # Stop due to torque limit
            self.set_output('VALVE_OPEN', False)
            self.set_output('VALVE_CLOSE', False)
            self.set_output('VALVE_MOVING', False)
        
        # Travel time monitoring
        if self.get_output('VALVE_MOVING', False):
            if not self.update_timer('TRAVEL_TIMER', self.valve_travel_time + 10):
                # Still within expected travel time
                pass
            else:
                # Travel time exceeded
                self.add_alarm('VALVE_TRAVEL_TIME', 'MEDIUM', 'Valve travel time exceeded')
                self.set_output('VALVE_OPEN', False)
                self.set_output('VALVE_CLOSE', False)
                self.set_output('VALVE_MOVING', False)
        else:
            self.reset_timer('TRAVEL_TIMER')
        
        # Position status
        self.set_output('POSITION_IN_TOLERANCE', position_in_tolerance)
        self.set_output('CURRENT_POSITION', current_position)
        
        # Valve state indication
        if fully_open:
            valve_state = "FULLY_OPEN"
        elif fully_closed:
            valve_state = "FULLY_CLOSED" 
        elif self.get_output('VALVE_MOVING', False):
            valve_state = "MOVING"
        else:
            valve_state = "INTERMEDIATE"
            
        self.set_output('VALVE_STATE', valve_state)
        
        # Update memory
        self.memory['CURRENT_POSITION'] = current_position
        self.memory['POSITION_ERROR'] = position_error
        self.memory['VALVE_STATE'] = valve_state