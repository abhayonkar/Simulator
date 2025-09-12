# Safety Monitoring PLC - Monitors overall system safety
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class SafetyMonitoringPLC(BasePLC):
    """PLC for comprehensive safety monitoring"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "SAFETY_MONITORING")
        self.safety_zones = ['NORMAL', 'WARNING', 'ALARM', 'EMERGENCY']
        self.current_safety_zone = 'NORMAL'
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Safety sensors
        pressure = sensor_data.get(f'pressure_{self.node_id}', 50.0)
        self.update_input('PRESSURE_SENSOR', pressure)
        
        gas_leak = sensor_data.get(f'gas_leak_{self.node_id}', False)
        self.update_input('GAS_LEAK_DETECTOR', gas_leak)
        
        fire_detector = sensor_data.get(f'fire_detector_{self.node_id}', False)
        self.update_input('FIRE_DETECTOR', fire_detector)
        
        emergency_stop = sensor_data.get(f'emergency_stop_{self.node_id}', False)
        self.update_input('EMERGENCY_STOP', emergency_stop)
        
    def execute_logic(self):
        """Execute safety monitoring logic"""
        pressure = self.get_input('PRESSURE_SENSOR', 50.0)
        gas_leak = self.get_input('GAS_LEAK_DETECTOR', False)
        fire_detected = self.get_input('FIRE_DETECTOR', False)
        emergency_stop = self.get_input('EMERGENCY_STOP', False)
        
        # Determine safety zone
        if emergency_stop or fire_detected:
            self.current_safety_zone = 'EMERGENCY'
            self.add_alarm('EMERGENCY', 'CRITICAL', 'Emergency condition detected')
        elif gas_leak or pressure > 85.0:
            self.current_safety_zone = 'ALARM'
            self.add_alarm('ALARM_CONDITION', 'HIGH', 'Alarm condition detected')
        elif pressure > 75.0 or pressure < 10.0:
            self.current_safety_zone = 'WARNING'
        else:
            self.current_safety_zone = 'NORMAL'
        
        self.set_output('SAFETY_ZONE', self.current_safety_zone)
        self.set_output('SAFETY_OK', self.current_safety_zone in ['NORMAL', 'WARNING'])