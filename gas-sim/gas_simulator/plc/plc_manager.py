# PLC Manager - Manages all 8 custom PLCs
import logging
from typing import Dict, Any, List
from .pressure_control_plc import PressureControlPLC
from .flow_regulation_plc import FlowRegulationPLC
from .compressor_management_plc import CompressorManagementPLC
from .valve_control_plc import ValveControlPLC
from .safety_monitoring_plc import SafetyMonitoringPLC
from .leak_detection_plc import LeakDetectionPLC
from .temperature_control_plc import TemperatureControlPLC
from .emergency_shutdown_plc import EmergencyShutdownPLC

logger = logging.getLogger(__name__)

class PLCManager:
    """Manages all PLC instances in the gas pipeline system"""
    
    def __init__(self, sensor_manager=None):
        self.sensor_manager = sensor_manager
        self.plcs = {}
        self.plc_types = {
            'PRESSURE_CONTROL': PressureControlPLC,
            'FLOW_REGULATION': FlowRegulationPLC,
            'COMPRESSOR_MANAGEMENT': CompressorManagementPLC,
            'VALVE_CONTROL': ValveControlPLC,
            'SAFETY_MONITORING': SafetyMonitoringPLC,
            'LEAK_DETECTION': LeakDetectionPLC,
            'TEMPERATURE_CONTROL': TemperatureControlPLC,
            'EMERGENCY_SHUTDOWN': EmergencyShutdownPLC
        }
        logger.info("PLC Manager initialized")
    
    def initialize_plcs(self, network_data: Dict[str, Any]):
        """Initialize PLCs across the network nodes"""
        nodes = network_data.get('nodes', {})
        
        # Strategy: Distribute 8 PLCs across key nodes
        node_ids = list(nodes.keys())
        
        if len(node_ids) >= 8:
            # Assign specific PLC types to nodes based on node type
            plc_assignments = []
            for i, node_id in enumerate(node_ids[:8]):
                node = nodes[node_id]
                node_type = node.get('type', 'junction')
                
                if node_type == 'source':
                    plc_type = 'PRESSURE_CONTROL'
                elif node_type == 'compressor':
                    plc_type = 'COMPRESSOR_MANAGEMENT'
                elif node_type == 'sink':
                    plc_type = 'FLOW_REGULATION'
                elif i % 4 == 0:
                    plc_type = 'VALVE_CONTROL'
                elif i % 4 == 1:
                    plc_type = 'SAFETY_MONITORING'
                elif i % 4 == 2:
                    plc_type = 'LEAK_DETECTION'
                elif i % 4 == 3:
                    plc_type = 'TEMPERATURE_CONTROL'
                else:
                    plc_type = 'EMERGENCY_SHUTDOWN'
                
                plc_assignments.append((node_id, plc_type))
            
            # Add emergency shutdown PLC to the first node if not already assigned
            if not any(assignment[1] == 'EMERGENCY_SHUTDOWN' for assignment in plc_assignments):
                plc_assignments[0] = (plc_assignments[0][0], 'EMERGENCY_SHUTDOWN')
        else:
            # For smaller networks, distribute available PLC types
            plc_types_list = list(self.plc_types.keys())
            plc_assignments = []
            for i, node_id in enumerate(node_ids):
                plc_type = plc_types_list[i % len(plc_types_list)]
                plc_assignments.append((node_id, plc_type))
        
        # Create PLC instances
        for node_id, plc_type in plc_assignments:
            plc_id = f"PLC_{plc_type}_{node_id}"
            plc_class = self.plc_types[plc_type]
            plc = plc_class(plc_id, node_id)
            self.plcs[plc_id] = plc
            logger.info(f"Created {plc_type} PLC {plc_id} at node {node_id}")
        
        logger.info(f"Initialized {len(self.plcs)} PLCs across the network")
    
    def execute_all_plcs(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all PLC scan cycles"""
        all_outputs = {}
        
        for plc_id, plc in self.plcs.items():
            try:
                outputs = plc.execute_scan(sensor_data)
                all_outputs[plc_id] = outputs
            except Exception as e:
                logger.error(f"Error executing PLC {plc_id}: {e}")
                all_outputs[plc_id] = {}
        
        return all_outputs
    
    def send_command_to_plc(self, plc_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to specific PLC"""
        if plc_id in self.plcs:
            plc = self.plcs[plc_id]
            try:
                # Update PLC inputs based on command
                for key, value in command.items():
                    plc.update_input(key, value)
                return {"success": True, "message": f"Command sent to {plc_id}"}
            except Exception as e:
                logger.error(f"Error sending command to PLC {plc_id}: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"PLC {plc_id} not found"}
    
    def get_all_plc_status(self) -> Dict[str, Any]:
        """Get status of all PLCs"""
        status = {}
        for plc_id, plc in self.plcs.items():
            status[plc_id] = plc.get_status()
        return status
    
    def get_active_plc_count(self) -> int:
        """Get count of active PLCs"""
        return len([plc for plc in self.plcs.values() if plc.is_active])
    
    def get_all_alarms(self) -> List[Dict[str, Any]]:
        """Get all alarms from all PLCs"""
        all_alarms = []
        for plc_id, plc in self.plcs.items():
            for alarm in plc.alarms:
                alarm_dict = {
                    'plc_id': plc_id,
                    'node_id': plc.node_id,
                    'alarm_id': alarm.alarm_id,
                    'severity': alarm.severity,
                    'message': alarm.message,
                    'timestamp': alarm.timestamp.isoformat(),
                    'acknowledged': alarm.acknowledged
                }
                all_alarms.append(alarm_dict)
        return all_alarms