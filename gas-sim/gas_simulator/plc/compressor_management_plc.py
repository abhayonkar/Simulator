# Compressor Management PLC - Controls compressor stations
from .base_plc import BasePLC
import logging

logger = logging.getLogger(__name__)

class CompressorManagementPLC(BasePLC):
    """PLC for compressor station management"""
    
    def __init__(self, plc_id: str, node_id: str):
        super().__init__(plc_id, node_id, "COMPRESSOR_MANAGEMENT")
        
        # Compressor parameters
        self.start_pressure = 35.0  # bar - pressure to start compressor
        self.stop_pressure = 55.0   # bar - pressure to stop compressor
        self.max_suction_pressure = 60.0  # bar
        self.min_suction_pressure = 10.0  # bar
        self.max_discharge_pressure = 85.0 # bar
        
        # Operating parameters
        self.compressor_running = False
        self.run_hours = 0.0
        self.start_attempts = 0
        self.max_start_attempts = 3
        
    def update_inputs(self, sensor_data):
        """Update inputs from sensor data"""
        # Suction pressure
        suction_pressure = sensor_data.get(f'suction_pressure_{self.node_id}', 40.0)
        self.update_input('SUCTION_PRESSURE', suction_pressure)
        
        # Discharge pressure  
        discharge_pressure = sensor_data.get(f'discharge_pressure_{self.node_id}', 50.0)
        self.update_input('DISCHARGE_PRESSURE', discharge_pressure)
        
        # Compressor speed (RPM)
        speed = sensor_data.get(f'compressor_speed_{self.node_id}', 0)
        self.update_input('COMPRESSOR_SPEED', speed)
        
        # Vibration sensor
        vibration = sensor_data.get(f'vibration_{self.node_id}', 0.5)
        self.update_input('VIBRATION', vibration)
        
        # Temperature sensors
        oil_temp = sensor_data.get(f'oil_temperature_{self.node_id}', 80.0)
        self.update_input('OIL_TEMPERATURE', oil_temp)
        
        gas_temp = sensor_data.get(f'gas_temperature_{self.node_id}', 35.0)
        self.update_input('GAS_TEMPERATURE', gas_temp)
        
        # Manual start/stop
        manual_start = sensor_data.get(f'manual_start_{self.node_id}', False)
        self.update_input('MANUAL_START', manual_start)
        
        manual_stop = sensor_data.get(f'manual_stop_{self.node_id}', False)
        self.update_input('MANUAL_STOP', manual_stop)
        
    def execute_logic(self):
        """Execute compressor management ladder logic"""
        # Get current readings
        suction_pressure = self.get_input('SUCTION_PRESSURE', 40.0)
        discharge_pressure = self.get_input('DISCHARGE_PRESSURE', 50.0)
        speed = self.get_input('COMPRESSOR_SPEED', 0)
        vibration = self.get_input('VIBRATION', 0.5)
        oil_temp = self.get_input('OIL_TEMPERATURE', 80.0)
        gas_temp = self.get_input('GAS_TEMPERATURE', 35.0)
        manual_start = self.get_input('MANUAL_START', False)
        manual_stop = self.get_input('MANUAL_STOP', False)
        
        # Safety interlocks
        safety_ok = True
        
        if suction_pressure > self.max_suction_pressure:
            self.add_alarm('HIGH_SUCTION_PRESSURE', 'HIGH', f'Suction pressure {suction_pressure:.1f} bar too high')
            safety_ok = False
        
        if suction_pressure < self.min_suction_pressure:
            self.add_alarm('LOW_SUCTION_PRESSURE', 'HIGH', f'Suction pressure {suction_pressure:.1f} bar too low')
            safety_ok = False
            
        if discharge_pressure > self.max_discharge_pressure:
            self.add_alarm('HIGH_DISCHARGE_PRESSURE', 'CRITICAL', f'Discharge pressure {discharge_pressure:.1f} bar exceeds limit')
            safety_ok = False
            
        if vibration > 5.0:  # mm/s
            self.add_alarm('HIGH_VIBRATION', 'HIGH', f'Compressor vibration {vibration:.1f} mm/s too high')
            safety_ok = False
            
        if oil_temp > 120.0:  # °C
            self.add_alarm('HIGH_OIL_TEMP', 'HIGH', f'Oil temperature {oil_temp:.1f}°C too high')
            safety_ok = False
            
        # Compressor start/stop logic
        should_run = False
        
        if manual_stop:
            should_run = False
        elif manual_start and safety_ok:
            should_run = True
        elif safety_ok:
            # Automatic pressure control
            if not self.compressor_running and suction_pressure <= self.start_pressure:
                should_run = True
            elif self.compressor_running and suction_pressure >= self.stop_pressure:
                should_run = False
            else:
                should_run = self.compressor_running
        
        # Execute start/stop
        if should_run and not self.compressor_running and safety_ok:
            if self.start_attempts < self.max_start_attempts:
                self.set_output('COMPRESSOR_START', True)
                self.set_output('COMPRESSOR_RUN', True)
                self.compressor_running = True
                self.start_attempts += 1
                self.reset_timer('START_DELAY')
                logger.info(f"Compressor {self.node_id} started")
            else:
                self.add_alarm('MAX_START_ATTEMPTS', 'HIGH', 'Maximum start attempts exceeded')
                
        elif not should_run and self.compressor_running:
            self.set_output('COMPRESSOR_START', False)
            self.set_output('COMPRESSOR_RUN', False)
            self.compressor_running = False
            logger.info(f"Compressor {self.node_id} stopped")
        
        # Start delay timer (prevent rapid cycling)
        if self.update_timer('START_DELAY', 60.0):  # 60 second delay
            self.start_attempts = 0
            
        # Run hour counter
        if self.compressor_running:
            self.run_hours += (self.scan_time / 3600.0)  # Convert to hours
            
        # Outputs
        self.set_output('COMPRESSOR_RUNNING', self.compressor_running)
        self.set_output('SAFETY_OK', safety_ok)
        self.set_output('RUN_HOURS', self.run_hours)
        self.set_output('COMPRESSION_RATIO', discharge_pressure / max(suction_pressure, 1.0))
        
        # Update memory
        self.memory['SUCTION_PRESSURE'] = suction_pressure
        self.memory['DISCHARGE_PRESSURE'] = discharge_pressure
        self.memory['COMPRESSOR_RUNNING'] = self.compressor_running
        self.memory['RUN_HOURS'] = self.run_hours