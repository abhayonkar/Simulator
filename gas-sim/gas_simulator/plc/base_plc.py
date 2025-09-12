# Base PLC class for all custom PLC implementations
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PLCInput:
    """PLC input data structure"""
    address: str
    value: Any
    timestamp: datetime
    quality: str = "GOOD"  # GOOD, BAD, UNCERTAIN

@dataclass
class PLCOutput:
    """PLC output data structure"""
    address: str
    value: Any
    timestamp: datetime

@dataclass
class PLCAlarm:
    """PLC alarm data structure"""
    alarm_id: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    timestamp: datetime
    acknowledged: bool = False

class BasePLC(ABC):
    """Base class for all PLC implementations"""
    
    def __init__(self, plc_id: str, node_id: str, plc_type: str):
        self.plc_id = plc_id
        self.node_id = node_id
        self.plc_type = plc_type
        self.inputs = {}
        self.outputs = {}
        self.memory = {}
        self.timers = {}
        self.counters = {}
        self.alarms = []
        self.is_active = True
        self.scan_time = 0.1  # PLC scan time in seconds
        self.last_scan = time.time()
        
        logger.info(f"Initialized {plc_type} PLC {plc_id} at node {node_id}")
    
    def update_input(self, address: str, value: Any, quality: str = "GOOD"):
        """Update PLC input value"""
        self.inputs[address] = PLCInput(
            address=address,
            value=value,
            timestamp=datetime.now(),
            quality=quality
        )
    
    def set_output(self, address: str, value: Any):
        """Set PLC output value"""
        self.outputs[address] = PLCOutput(
            address=address,
            value=value,
            timestamp=datetime.now()
        )
    
    def get_input(self, address: str, default=None):
        """Get input value safely"""
        input_data = self.inputs.get(address)
        return input_data.value if input_data else default
    
    def get_output(self, address: str, default=None):
        """Get output value safely"""
        output_data = self.outputs.get(address)
        return output_data.value if output_data else default
    
    def add_alarm(self, alarm_id: str, severity: str, message: str):
        """Add new alarm"""
        alarm = PLCAlarm(
            alarm_id=alarm_id,
            severity=severity,
            message=message,
            timestamp=datetime.now()
        )
        self.alarms.append(alarm)
        logger.warning(f"PLC {self.plc_id}: {severity} alarm - {message}")
    
    def acknowledge_alarm(self, alarm_id: str):
        """Acknowledge alarm"""
        for alarm in self.alarms:
            if alarm.alarm_id == alarm_id:
                alarm.acknowledged = True
                logger.info(f"PLC {self.plc_id}: Acknowledged alarm {alarm_id}")
    
    def clear_acknowledged_alarms(self):
        """Clear acknowledged alarms"""
        self.alarms = [alarm for alarm in self.alarms if not alarm.acknowledged]
    
    def update_timer(self, timer_name: str, preset_time: float):
        """Update timer"""
        if timer_name not in self.timers:
            self.timers[timer_name] = {'start_time': time.time(), 'preset': preset_time, 'done': False}
        
        timer = self.timers[timer_name]
        elapsed = time.time() - timer['start_time']
        timer['done'] = elapsed >= timer['preset']
        return timer['done']
    
    def reset_timer(self, timer_name: str):
        """Reset timer"""
        if timer_name in self.timers:
            self.timers[timer_name]['start_time'] = time.time()
            self.timers[timer_name]['done'] = False
    
    def increment_counter(self, counter_name: str, max_count: int = 999999):
        """Increment counter"""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        
        self.counters[counter_name] = min(self.counters[counter_name] + 1, max_count)
        return self.counters[counter_name]
    
    def reset_counter(self, counter_name: str):
        """Reset counter"""
        self.counters[counter_name] = 0
    
    def should_scan(self):
        """Check if it's time for the next PLC scan"""
        return (time.time() - self.last_scan) >= self.scan_time
    
    def execute_scan(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PLC scan cycle"""
        if not self.is_active or not self.should_scan():
            return {}
        
        try:
            # Update inputs from sensor data
            self.update_inputs(sensor_data)
            
            # Execute ladder logic
            self.execute_logic()
            
            # Update scan timestamp
            self.last_scan = time.time()
            
            # Return output values
            return {addr: output.value for addr, output in self.outputs.items()}
            
        except Exception as e:
            logger.error(f"PLC {self.plc_id} scan error: {e}")
            self.add_alarm(f"SCAN_ERROR_{self.plc_id}", "HIGH", f"PLC scan error: {str(e)}")
            return {}
    
    @abstractmethod
    def update_inputs(self, sensor_data: Dict[str, Any]):
        """Update PLC inputs from sensor data - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def execute_logic(self):
        """Execute PLC ladder logic - must be implemented by subclasses"""
        pass
    
    def get_status(self):
        """Get PLC status information"""
        return {
            'plc_id': self.plc_id,
            'node_id': self.node_id,
            'plc_type': self.plc_type,
            'is_active': self.is_active,
            'inputs': {addr: inp.value for addr, inp in self.inputs.items()},
            'outputs': {addr: out.value for addr, out in self.outputs.items()},
            'alarms': len([alarm for alarm in self.alarms if not alarm.acknowledged]),
            'timers': len(self.timers),
            'counters': len(self.counters),
            'last_scan': self.last_scan
        }