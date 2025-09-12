# Leak Detection PLC - Detects and manages gas leaks
from .base_plc import BasePLC
import logging
import random

logger = logging.getLogger(__name__)

class LeakDetectionPLC(BasePLC):
    """PLC for gas leak detection and response"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "LEAK_DETECTION")
        self.leak_threshold = 1000  # ppm
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Gas concentration sensors
        gas_concentration = sensor_data.get(f'gas_concentration_{self.node_id}', random.randint(0, 100))
        self.update_input('GAS_CONCENTRATION', gas_concentration)
        
        # Acoustic leak detector
        acoustic_signal = sensor_data.get(f'acoustic_leak_{self.node_id}', False)
        self.update_input('ACOUSTIC_DETECTOR', acoustic_signal)
        
    def execute_logic(self):
        """Execute leak detection logic"""
        gas_concentration = self.get_input('GAS_CONCENTRATION', 0)
        acoustic_signal = self.get_input('ACOUSTIC_DETECTOR', False)
        
        leak_detected = gas_concentration > self.leak_threshold or acoustic_signal
        
        if leak_detected:
            self.add_alarm('GAS_LEAK', 'CRITICAL', f'Gas leak detected - {gas_concentration} ppm')
            self.set_output('ISOLATION_VALVE', False)  # Close isolation valve
            self.set_output('VENTILATION_FAN', True)   # Start ventilation
        
        self.set_output('LEAK_DETECTED', leak_detected)