# Emergency Shutdown PLC - Manages emergency shutdown procedures
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class EmergencyShutdownPLC(BasePLC):
    """PLC for emergency shutdown system (ESD)"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "EMERGENCY_SHUTDOWN")
        self.esd_active = False
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Emergency triggers
        emergency_button = sensor_data.get(f'emergency_button_{self.node_id}', False)
        self.update_input('EMERGENCY_BUTTON', emergency_button)
        
        high_pressure = sensor_data.get(f'pressure_{self.node_id}', 50.0) > 90.0
        self.update_input('HIGH_PRESSURE_TRIP', high_pressure)
        
        fire_detected = sensor_data.get(f'fire_detector_{self.node_id}', False)
        self.update_input('FIRE_DETECTED', fire_detected)
        
        gas_leak = sensor_data.get(f'gas_leak_{self.node_id}', False)
        self.update_input('GAS_LEAK', gas_leak)
        
    def execute_logic(self):
        """Execute emergency shutdown logic"""
        emergency_button = self.get_input('EMERGENCY_BUTTON', False)
        high_pressure = self.get_input('HIGH_PRESSURE_TRIP', False)
        fire_detected = self.get_input('FIRE_DETECTED', False)
        gas_leak = self.get_input('GAS_LEAK', False)
        
        # ESD triggers
        should_shutdown = emergency_button or high_pressure or fire_detected or gas_leak
        
        if should_shutdown and not self.esd_active:
            self.esd_active = True
            self.add_alarm('EMERGENCY_SHUTDOWN', 'CRITICAL', 'Emergency shutdown activated')
            logger.critical(f"Emergency shutdown activated at node {self.node_id}")
        
        if self.esd_active:
            # Close all valves
            self.set_output('ESD_VALVE_1', False)
            self.set_output('ESD_VALVE_2', False)
            self.set_output('MAIN_SUPPLY_VALVE', False)
            
            # Stop compressors
            self.set_output('COMPRESSOR_STOP', True)
            
            # Vent to atmosphere if safe
            if not fire_detected:
                self.set_output('VENT_VALVE', True)
        
        self.set_output('ESD_ACTIVE', self.esd_active)