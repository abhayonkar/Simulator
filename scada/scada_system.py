# SCADA System - Supervisory Control and Data Acquisition
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SCADASystem:
    """SCADA system for monitoring and control"""
    
    def __init__(self, plc_manager=None, sensor_manager=None):
        self.plc_manager = plc_manager
        self.sensor_manager = sensor_manager
        self.system_status = 'NORMAL'
        self.alarms = []
        logger.info("SCADA System initialized")
    
    def update(self, network_data: Dict[str, Any], sensor_data: Dict[str, Any], 
               plc_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Update SCADA system with latest data"""
        
        # Determine overall system status
        self.system_status = self.evaluate_system_status(network_data, sensor_data, plc_outputs)
        
        # Collect alarms from PLCs
        if self.plc_manager:
            self.alarms = self.plc_manager.get_all_alarms()
        
        return {
            'system_status': self.system_status,
            'alarm_count': len(self.alarms),
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_system_status(self, network_data: Dict[str, Any], 
                             sensor_data: Dict[str, Any], 
                             plc_outputs: Dict[str, Any]) -> str:
        """Evaluate overall system status"""
        
        # Check for critical conditions
        critical_alarms = len([a for a in self.alarms if a.get('severity') == 'CRITICAL'])
        high_alarms = len([a for a in self.alarms if a.get('severity') == 'HIGH'])
        
        if critical_alarms > 0:
            return 'CRITICAL'
        elif high_alarms > 2:
            return 'ALARM'
        elif high_alarms > 0:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'status': self.system_status,
            'alarms': len(self.alarms),
            'timestamp': datetime.now().isoformat()
        }