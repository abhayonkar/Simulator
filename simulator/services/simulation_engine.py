# Django Simulation Engine - Python-only gas pipeline simulation
import logging
import time
import random
import math
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction # Import transaction for safe bulk operations
from ..models import (
    GasNetwork, Node, Pipe, Sensor, PLC, PLCAlarm, Valve, Compressor,
    SimulationRun, SimulationTimeSeriesData
)
from .postgres_tsdb_service import get_postgres_tsdb_service

logger = logging.getLogger(__name__)

class PLCSimulator:
    """Simplified PLC simulation logic"""
    
    def __init__(self, plc):
        self.plc = plc
        self.integral_error = 0.0
        self.last_error = 0.0
    
    def execute_scan(self, sensor_data, simulation_time):
        """Execute PLC scan cycle"""
        try:
            if self.plc.plc_type == 'PRESSURE_CONTROL':
                return self._pressure_control_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'FLOW_REGULATION':
                return self._flow_regulation_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'COMPRESSOR_MANAGEMENT':
                return self._compressor_management_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'VALVE_CONTROL':
                return self._valve_control_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'SAFETY_MONITORING':
                return self._safety_monitoring_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'LEAK_DETECTION':
                return self._leak_detection_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'TEMPERATURE_CONTROL':
                return self._temperature_control_logic(sensor_data, simulation_time)
            elif self.plc.plc_type == 'EMERGENCY_SHUTDOWN':
                return self._emergency_shutdown_logic(sensor_data, simulation_time)
            
            return {}
            
        except Exception as e:
            logger.error(f"PLC {self.plc.plc_id} scan error: {e}")
            return {}
    
    def _pressure_control_logic(self, sensor_data, simulation_time):
        """Pressure control PLC logic"""
        node_id = self.plc.node.node_id
        current_pressure = sensor_data.get(f'pressure_{node_id}', 50.0)
        
        # Use Node's set_pressure as setpoint (manual override potential)
        setpoint = self.plc.node.set_pressure
        
        # PID parameters
        kp, ki, kd = 1.0, 0.1, 0.01
        
        # PID calculation
        error = setpoint - current_pressure
        self.integral_error += error * 0.1
        derivative_error = (error - self.last_error) / 0.1
        
        pid_output = kp * error + ki * self.integral_error + kd * derivative_error
        # The valve position suggested by the PLC (0-100%)
        plc_valve_position = max(0, min(100, 50 + pid_output)) 
        
        self.last_error = error
        
        # Safety checks
        if current_pressure > self.plc.node.pressure_max * 0.9:
            self._create_alarm('HIGH_PRESSURE', 'HIGH', f'Pressure {current_pressure:.1f} bar exceeds warning limit')
        
        return {
            # PLC outputs a suggested position
            'CONTROL_VALVE_POSITION': plc_valve_position,
            'PRESSURE_IN_TOLERANCE': abs(error) <= 2.0,
            'PID_OUTPUT': pid_output
        }
    
    def _flow_regulation_logic(self, sensor_data, simulation_time):
        """Flow regulation PLC logic"""
        node_id = self.plc.node.node_id
        current_flow = sensor_data.get(f'flow_{node_id}', 100.0)
        
        # Use Node's set_flow as target flow (manual override potential)
        target_flow = self.plc.node.set_flow 
        
        flow_error = target_flow - current_flow
        
        # Adjust valve position based on flow error
        valve_adjustment = flow_error * 0.5
        plc_valve_position = max(0, min(100, 50 + valve_adjustment))
        
        return {
            'FLOW_CONTROL_VALVE': plc_valve_position,
            'FLOW_IN_RANGE': abs(flow_error) <= 10.0,
            'FLOW_ERROR': flow_error
        }
    
    def _compressor_management_logic(self, sensor_data, simulation_time):
        """Compressor management PLC logic"""
        node_id = self.plc.node.node_id
        pressure = sensor_data.get(f'pressure_{node_id}', 50.0)
        
        # Simple logic: start compressor if pressure is low
        compressor_start_pressure = 45.0
        compressor_stop_pressure = 55.0
        
        compressor_to_control = Compressor.objects.filter(node=self.plc.node).first()
        
        if compressor_to_control and compressor_to_control.set_command == 'AUTO':
            # Auto logic based on pressure
            if pressure < compressor_start_pressure:
                command = 'ON'
                speed = 10000.0 # High speed command
            elif pressure > compressor_stop_pressure:
                command = 'OFF'
                speed = 0.0
            else:
                # Keep current state if in deadband
                command = compressor_to_control.status 
                speed = compressor_to_control.speed
        else:
            # Manual override is active, PLC outputs follow the manual command
            command = compressor_to_control.set_command if compressor_to_control else 'OFF'
            speed = compressor_to_control.set_speed if compressor_to_control and compressor_to_control.set_speed >= 0 else 0.0
        
        # The outputs here instruct the update_compressors function what to do
        return {
            'COMPRESSOR_COMMAND': command,
            'COMPRESSOR_TARGET_SPEED': speed,
            'SUCTION_VALVE': command == 'ON' or command == 'RUNNING',
            'DISCHARGE_VALVE': command == 'ON' or command == 'RUNNING'
        }
    
    def _valve_control_logic(self, sensor_data, simulation_time):
        """Valve control PLC logic (Placeholder for complex strategies)"""
        # This PLC just outputs arbitrary positions for demonstration
        positions = {}
        for valve in Valve.objects.filter(plc=self.plc):
            # If the valve is under PLC control (set_position = -1.0)
            if valve.set_position < 0:
                # Calculate new position (simple random movement)
                new_position = valve.position + random.uniform(-1.0, 1.0)
                positions[valve.valve_id] = max(0, min(100, new_position))
            else:
                # If set_position is manual, PLC outputs the current manual setpoint
                positions[valve.valve_id] = valve.set_position
        
        return positions
    
    def _safety_monitoring_logic(self, sensor_data, simulation_time):
        """Safety monitoring PLC logic"""
        node_id = self.plc.node.node_id
        pressure = sensor_data.get(f'pressure_{node_id}', 50.0)
        temperature = sensor_data.get(f'temperature_{node_id}', 20.0)
        
        safety_status = {}
        
        # Pressure safety
        if pressure > 75.0:
            self._create_alarm('PRESSURE_WARNING', 'MEDIUM', f'High pressure warning: {pressure:.1f} bar')
            safety_status['PRESSURE_ALARM'] = True
        else:
            safety_status['PRESSURE_ALARM'] = False
        
        # Temperature safety
        if temperature > 60.0:
            self._create_alarm('TEMPERATURE_WARNING', 'MEDIUM', f'High temperature warning: {temperature:.1f}°C')
            safety_status['TEMPERATURE_ALARM'] = True
        else:
            safety_status['TEMPERATURE_ALARM'] = False
        
        safety_status['SAFETY_OK'] = not (safety_status['PRESSURE_ALARM'] or safety_status['TEMPERATURE_ALARM'])
        
        return safety_status
    
    def _leak_detection_logic(self, sensor_data, simulation_time):
        """Leak detection PLC logic"""
        leak_detected = random.random() < 0.0001 # Reduced chance for demo
        
        if leak_detected:
            self._create_alarm('GAS_LEAK', 'CRITICAL', 'Gas leak detected!')
        
        return {
            'LEAK_DETECTED': leak_detected,
            'LEAK_ISOLATION_VALVE': leak_detected
        }
    
    def _temperature_control_logic(self, sensor_data, simulation_time):
        """Temperature control PLC logic"""
        node_id = self.plc.node.node_id
        temperature = sensor_data.get(f'temperature_{node_id}', 20.0)
        
        target_temp = 25.0
        temp_error = target_temp - temperature
        
        heating = temp_error > 2.0
        cooling = temp_error < -2.0
        
        return {
            'HEATING_ACTIVE': heating,
            'COOLING_ACTIVE': cooling,
            'TEMPERATURE_IN_RANGE': abs(temp_error) <= 2.0,
            'TEMPERATURE_ERROR': temp_error
        }
    
    def _emergency_shutdown_logic(self, sensor_data, simulation_time):
        """Emergency shutdown PLC logic"""
        pressure_ok = all(s.current_value <= 80.0 for s in Sensor.objects.filter(sensor_type='pressure'))
        temperature_ok = all(s.current_value <= 70.0 for s in Sensor.objects.filter(sensor_type='temperature'))
        
        emergency_stop = not (pressure_ok and temperature_ok)
        
        if emergency_stop:
            self._create_alarm('EMERGENCY_STOP', 'CRITICAL', 'Emergency shutdown triggered!')
        
        return {
            'EMERGENCY_STOP': emergency_stop,
            'MASTER_ISOLATION': emergency_stop,
            'EMERGENCY_VENT': emergency_stop
        }
    
    def _create_alarm(self, alarm_id, severity, message):
        """Create PLC alarm"""
        try:
            PLCAlarm.objects.create(
                plc=self.plc,
                alarm_id=alarm_id,
                severity=severity,
                message=message
            )
            logger.warning(f"PLC {self.plc.plc_id}: {severity} alarm - {message}")
        except Exception as e:
            logger.error(f"Error creating alarm: {e}")

class SimulationEngine:
    """Django-based Python-only simulation engine"""
    
    def __init__(self):
        self.running = False
        self.simulation_thread = None
        self.tsdb_service = get_postgres_tsdb_service()

    def start_simulation(self, network_id, duration=600, time_step=1.0):
        """Start a new simulation run"""
        try:
            network = GasNetwork.objects.get(id=network_id)
            
            # Create simulation run
            run_id = f"run_{int(time.time())}"
            simulation_run = SimulationRun.objects.create(
                run_id=run_id,
                network=network,
                duration=duration,
                time_step=time_step,
                status='RUNNING',
                start_time=timezone.now()
            )
            
            with transaction.atomic():
                # Initialize components
                self._initialize_sensors(network)
                self._initialize_plcs(network)
                self._initialize_valves(network)
                self._initialize_compressors(network) # New initialization
            
            # Start simulation in separate thread
            self.simulation_thread = threading.Thread(
                target=self._simulation_loop,
                args=(simulation_run,)
            )
            self.running = True
            self.simulation_thread.start()
            
            logger.info(f"Started simulation {run_id} for {duration} seconds")
            return simulation_run
            
        except Exception as e:
            logger.error(f"Error starting simulation: {e}")
            raise
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=5.0)
        logger.info("Simulation stopped")
    
    def _simulation_loop(self, simulation_run):
        """Main simulation loop"""
        logger.info(f"Starting simulation loop for {simulation_run.run_id}")
        
        start_time = time.time()
        step = 0
        
        try:
            while self.running and step * simulation_run.time_step < simulation_run.duration:
                step_start = time.time()
                simulation_time = step * simulation_run.time_step
                
                # Update sensor readings
                sensor_data = self._update_sensors(simulation_run.network, simulation_time)
                
                # Execute PLC scans
                plc_data = self._execute_plcs(simulation_run.network, sensor_data, simulation_time)
                
                # Update valve positions (uses PLC data or manual override)
                valve_data = self._update_valves(simulation_run.network, plc_data, simulation_time)
                
                # Update compressor states (uses PLC data or manual override)
                compressor_data = self._update_compressors(simulation_run.network, plc_data, simulation_time) # New update
                
                # Update physics simulation (incorporates valve/compressor changes and manual node setpoints)
                self._update_physics(simulation_run.network, sensor_data, simulation_time)
                
                # Collect node and pipe data
                node_data = self._collect_node_data(simulation_run.network)
                pipe_data = self._collect_pipe_data(simulation_run.network)
                
                # Store simulation data to PostgreSQL TSDB
                self._write_to_postgres(simulation_run, simulation_time, 
                                      sensor_data, plc_data, valve_data, 
                                      node_data, pipe_data, compressor_data)
                
                # Log progress every 60 steps
                if step % 60 == 0:
                    logger.info(f"Simulation {simulation_run.run_id}: Step {step}, Time {simulation_time:.1f}s")
                
                # Wait for next time step
                elapsed = time.time() - step_start
                if elapsed < simulation_run.time_step:
                    time.sleep(simulation_run.time_step - elapsed)
                
                step += 1
            
            # Finalize simulation
            simulation_run.status = 'COMPLETED'
            simulation_run.end_time = timezone.now()
            simulation_run.total_steps = step
            simulation_run.save()
            
            logger.info(f"Simulation {simulation_run.run_id} completed after {step} steps")
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            simulation_run.status = 'FAILED'
            simulation_run.end_time = timezone.now()
            simulation_run.total_steps = step
            simulation_run.save()
        
        finally:
            self.running = False
            
    def _write_to_postgres(self, simulation_run, simulation_time, 
                          sensor_data, plc_data, valve_data, node_data, pipe_data, compressor_data):
        """Write simulation data to the PostgreSQL TSDB table"""
        try:
            data_points = []
            
            # Sensor data
            for sensor_id, value in sensor_data.items():
                data_points.append(SimulationTimeSeriesData(
                    simulation_run=simulation_run, timestamp=simulation_time, 
                    measurement_type='sensor_reading', object_id=sensor_id, 
                    data={'value': value}
                ))
            
            # PLC data
            for plc_id, outputs in plc_data.items():
                data_points.append(SimulationTimeSeriesData(
                    simulation_run=simulation_run, timestamp=simulation_time, 
                    measurement_type='plc_output', object_id=plc_id, 
                    data=outputs
                ))
            
            # Node data
            for node_id, data in node_data.items():
                data_points.append(SimulationTimeSeriesData(
                    simulation_run=simulation_run, timestamp=simulation_time, 
                    measurement_type='node_state', object_id=node_id, 
                    data=data
                ))
                
            # Pipe data
            for pipe_id, data in pipe_data.items():
                data_points.append(SimulationTimeSeriesData(
                    simulation_run=simulation_run, timestamp=simulation_time, 
                    measurement_type='pipe_state', object_id=pipe_id, 
                    data=data
                ))
            
            # Compressor data
            for comp_id, data in compressor_data.items():
                data_points.append(SimulationTimeSeriesData(
                    simulation_run=simulation_run, timestamp=simulation_time,
                    measurement_type='compressor_state', object_id=comp_id,
                    data=data
                ))

            # Bulk create for performance
            SimulationTimeSeriesData.objects.bulk_create(data_points)
            
        except Exception as e:
            logger.error(f"Failed to write simulation data to PostgreSQL: {e}")
    
    def _initialize_sensors(self, network):
        """Initialize sensors for the network"""
        # ... (Sensor initialization remains mostly the same, ensuring flow setpoints are initialized on Node)
        
        # Create sensors for all nodes
        for node in network.nodes.all():
            # Pressure sensor
            Sensor.objects.get_or_create(
                sensor_id=f'pressure_{node.node_id}',
                defaults={
                    'sensor_type': 'pressure',
                    'node': node,
                    'current_value': node.current_pressure,
                    'unit': 'bar',
                    'min_value': node.pressure_min,
                    'max_value': node.pressure_max
                }
            )
            
            # Temperature sensor
            Sensor.objects.get_or_create(
                sensor_id=f'temperature_{node.node_id}',
                defaults={
                    'sensor_type': 'temperature',
                    'node': node,
                    'current_value': node.gas_temperature,
                    'unit': '°C',
                    'min_value': -10.0,
                    'max_value': 80.0
                }
            )
            
            # Flow sensor (for sources and sinks)
            if node.node_type in ['source', 'sink']:
                Sensor.objects.get_or_create(
                    sensor_id=f'flow_{node.node_id}',
                    defaults={
                        'sensor_type': 'flow',
                        'node': node,
                        'current_value': node.current_flow,
                        'unit': '1000m³/h',
                        'min_value': node.flow_min,
                        'max_value': node.flow_max
                    }
                )
            
            # Ensure node setpoints reflect initial state (or default)
            node.set_pressure = node.current_pressure
            node.set_flow = node.current_flow
            node.save()

        # Create flow sensors for pipes
        for pipe in network.pipes.all():
            Sensor.objects.get_or_create(
                sensor_id=f'flow_{pipe.pipe_id}',
                defaults={
                    'sensor_type': 'flow',
                    'pipe': pipe,
                    'current_value': pipe.current_flow,
                    'unit': 'm³/s',
                    'min_value': 0.0,
                    'max_value': 1000.0
                }
            )
    
    def _initialize_plcs(self, network):
        """Initialize 8 PLCs across the network"""
        nodes = list(network.nodes.all())
        plc_types = [
            'PRESSURE_CONTROL', 'FLOW_REGULATION', 'COMPRESSOR_MANAGEMENT', 
            'VALVE_CONTROL', 'SAFETY_MONITORING', 'LEAK_DETECTION',
            'TEMPERATURE_CONTROL', 'EMERGENCY_SHUTDOWN'
        ]
        
        # Distribute PLCs across nodes
        for i, plc_type in enumerate(plc_types):
            if i < len(nodes):
                node = nodes[i]
                plc_id = f'PLC_{plc_type}_{node.node_id}'
                
                PLC.objects.get_or_create(
                    plc_id=plc_id,
                    defaults={
                        'plc_type': plc_type,
                        'node': node,
                        'is_active': True,
                        'scan_time': 0.1,
                        'parameters': self._get_plc_parameters(plc_type)
                    }
                )

    def _initialize_compressors(self, network):
        """Initialize compressor models based on nodes that should have compressors (e.g., those managed by COMPRESSOR_MANAGEMENT PLCs)"""
        # Find nodes that are likely compressor stations (innode or nodes feeding innode/compressor station in GasLib)
        compressor_nodes = Node.objects.filter(node_id__in=['innode_6', 'sink_11', 'sink_19', 'source_3', 'source_2', 'sink_3'])
        
        for i, node in enumerate(compressor_nodes):
            comp_id = f'COMP_{node.node_id}'
            
            # Try to link to a relevant PLC
            plc = PLC.objects.filter(plc_type='COMPRESSOR_MANAGEMENT', node=node).first()
            
            Compressor.objects.get_or_create(
                compressor_id=comp_id,
                defaults={
                    'node': node,
                    'plc': plc,
                    'status': 'OFF',
                    'speed': 0.0,
                    'set_speed': -1.0, # Auto control by default
                    'set_command': 'AUTO' # Auto control by default
                }
            )
            
    def _initialize_valves(self, network):
        """Initialize valves on pipes"""
        for pipe in network.pipes.all():
            valve_id = f'valve_{pipe.pipe_id}'
            
            # Try to link valves to a VALVE_CONTROL PLC (or other relevant PLC)
            # Simple heuristic: link valve to a PLC at its from_node if one exists
            plc = PLC.objects.filter(node=pipe.from_node).first()
            
            Valve.objects.get_or_create(
                valve_id=valve_id,
                defaults={
                    'valve_type': 'CONTROL',
                    'pipe': pipe,
                    'position': 50.0,
                    'set_position': -1.0, # Auto control by default
                    'is_operational': True,
                    'max_pressure': 100.0,
                    'flow_coefficient': 1.0,
                    'plc': plc
                }
            )
    
    def _get_plc_parameters(self, plc_type):
        """Get default parameters for PLC type"""
        parameters = {
            'PRESSURE_CONTROL': {'setpoint': 50.0, 'kp': 1.0, 'ki': 0.1, 'kd': 0.01},
            'FLOW_REGULATION': {'target_flow': 100.0, 'flow_tolerance': 10.0},
            'COMPRESSOR_MANAGEMENT': {'start_pressure': 45.0, 'stop_pressure': 55.0},
            'VALVE_CONTROL': {'response_time': 2.0},
            'SAFETY_MONITORING': {'pressure_limit': 75.0, 'temp_limit': 60.0},
            'LEAK_DETECTION': {'sensitivity': 0.001},
            'TEMPERATURE_CONTROL': {'target_temp': 25.0, 'tolerance': 2.0},
            'EMERGENCY_SHUTDOWN': {'pressure_limit': 80.0, 'temp_limit': 70.0}
        }
        return parameters.get(plc_type, {})
    
    def _update_sensors(self, network, simulation_time):
        """Update all sensor readings"""
        sensor_data = {}
        
        for sensor in Sensor.objects.filter(node__network=network, is_active=True):
            # Simulate sensor readings with noise
            if sensor.sensor_type == 'pressure':
                base_value = sensor.node.current_pressure if sensor.node else 50.0
                noise = random.gauss(0, 0.1)
                sensor.current_value = max(0, base_value + noise)
            
            elif sensor.sensor_type == 'temperature':
                base_value = sensor.node.gas_temperature if sensor.node else 20.0
                noise = random.gauss(0, 0.5)
                sensor.current_value = base_value + noise
            
            elif sensor.sensor_type == 'flow':
                if sensor.node:
                    # Nodes (Sources/Sinks) expose their set flow in 1000m³/h (from set_flow)
                    base_value = sensor.node.set_flow 
                elif sensor.pipe:
                    # Pipes expose their internal m³/s flow
                    base_value = pipe.current_flow * 3600  # Convert m³/s to m³/h
                else:
                    base_value = 100.0
                
                noise = random.gauss(0, 2.0)
                sensor.current_value = max(0, base_value + noise)
            
            sensor.save()
            sensor_data[sensor.sensor_id] = sensor.current_value
        
        return sensor_data
    
    def _update_physics(self, network, sensor_data, simulation_time):
        """Update physics simulation - incorporates valve/compressor effects and manual node setpoints"""
        
        # 1. Apply Node Setpoints (Pressure and Flow)
        for node in network.nodes.all():
            if node.node_type == 'source':
                # Sources enforce the user's set pressure/flow (user sets one, system calculates the other)
                node.current_pressure = node.set_pressure + random.gauss(0, 0.5)
                # The flow will be dynamically calculated by the connected pipes, but we use the set flow as a base
                if node.set_flow > 0:
                    node.current_flow = node.set_flow
                else:
                    node.current_flow = 100.0 + random.gauss(0, 10.0)
            
            elif node.node_type == 'sink':
                # Sinks regulate their flow based on set_flow
                node.current_flow = node.set_flow
                node.current_pressure = node.pressure_min * 1.5 + random.gauss(0, 0.5)
            
            else:  # innode (Junctions)
                # Junctions pressure is calculated based on flow dynamics (simplification: average of connected pipes)
                node.current_pressure = 50.0 + random.gauss(0, 1.0) 
            
            node.save()

        # 2. Update Pipe Flows (incorporates Valve positions)
        for pipe in network.pipes.all():
            valve = pipe.valves.first()
            valve_openness = valve.position / 100.0 if valve else 1.0

            # Simplified flow calculation incorporating valve restriction
            dp = pipe.from_node.current_pressure - pipe.to_node.current_pressure
            
            # The flow is proportional to pressure difference and valve openness
            base_flow = dp * 2.0 * valve_openness
            pipe.current_flow = max(0, base_flow + random.gauss(0, 0.1))
            pipe.save()

    def _execute_plcs(self, network, sensor_data, simulation_time):
        """Execute all PLC scans"""
        plc_data = {}
        
        for plc in PLC.objects.filter(node__network=network, is_active=True):
            simulator = PLCSimulator(plc)
            outputs = simulator.execute_scan(sensor_data, simulation_time)
            
            # Update PLC outputs
            plc.outputs = outputs
            plc.last_scan = timezone.now() # Update last scan time
            plc.save()
            
            plc_data[plc.plc_id] = outputs
        
        return plc_data
    
    def _update_valves(self, network, plc_data, simulation_time):
        """Update valve positions based on PLC outputs OR manual setpoints"""
        valve_data = {}
        
        for valve in Valve.objects.filter(pipe__network=network, is_operational=True):
            
            if valve.set_position >= 0:
                # MANUAL OVERRIDE: Directly set the valve position to the setpoint
                new_position = valve.set_position
                control_source = 'Manual'
            
            elif valve.plc:
                # PLC CONTROL: Use PLC output if available
                plc_output_key = 'CONTROL_VALVE_POSITION' # Used by PRESSURE_CONTROL PLC
                plc_flow_key = 'FLOW_CONTROL_VALVE'       # Used by FLOW_REGULATION PLC
                
                # Check for relevant PLC outputs
                plc_outputs = plc_data.get(valve.plc.plc_id, {})
                
                if plc_output_key in plc_outputs:
                    new_position = plc_outputs[plc_output_key]
                    control_source = 'PLC (Pressure)'
                elif plc_flow_key in plc_outputs:
                    new_position = plc_outputs[plc_flow_key]
                    control_source = 'PLC (Flow)'
                else:
                    new_position = valve.position # Maintain previous position
                    control_source = 'No Control'
            
            else:
                # NO CONTROL/DEFAULT: Apply small random change
                new_position = valve.position + random.uniform(-0.1, 0.1)
                control_source = 'Default'

            # Apply limits and save
            new_position = max(0.0, min(100.0, new_position))
            
            if abs(valve.position - new_position) > 0.1: # Only save if change is significant
                valve.position = new_position
                valve.last_movement = timezone.now()
                valve.save()
            
            valve_data[valve.valve_id] = {'position': valve.position, 'control_source': control_source}
        
        return valve_data

    def _update_compressors(self, network, plc_data, simulation_time):
        """Update compressor states based on PLC outputs OR manual setpoints"""
        compressor_data = {}
        
        for compressor in Compressor.objects.filter(node__network=network):
            
            # 1. Determine target state based on override/auto
            if compressor.set_command != 'AUTO':
                # MANUAL COMMAND OVERRIDE
                target_status = compressor.set_command
                target_speed = compressor.set_speed if compressor.set_speed >= 0 else 0.0
                control_source = 'Manual'
            
            elif compressor.plc:
                # PLC CONTROL
                plc_outputs = plc_data.get(compressor.plc.plc_id, {})
                target_status = 'ON' if plc_outputs.get('COMPRESSOR_COMMAND') == 'ON' else 'OFF'
                target_speed = plc_outputs.get('COMPRESSOR_TARGET_SPEED', 0.0)
                control_source = 'PLC'
            
            else:
                # DEFAULT/OFF
                target_status = 'OFF'
                target_speed = 0.0
                control_source = 'Default'

            # 2. Apply dynamics to the current state
            new_status = compressor.status
            new_speed = compressor.speed
            
            # Simple state machine logic
            if target_status == 'ON' and new_status == 'OFF':
                new_status = 'STARTING'
            elif target_status == 'OFF' and new_status == 'RUNNING':
                new_status = 'STOPPING'
            elif new_status == 'STARTING' and new_speed >= 0.9 * target_speed and target_speed > 0:
                new_status = 'RUNNING'
            elif new_status == 'STOPPING' and new_speed <= 0.1 * compressor.max_speed:
                 new_status = 'OFF'
            
            # Simple speed ramping
            speed_change_rate = 1000.0 # RPM per second (simplified)
            speed_diff = target_speed - new_speed
            
            if abs(speed_diff) > speed_change_rate * simulation_run.time_step:
                new_speed += math.copysign(speed_change_rate * simulation_run.time_step, speed_diff)
            else:
                new_speed = target_speed

            # Apply limits and save
            new_speed = max(0.0, min(compressor.max_speed, new_speed))
            
            if new_status != compressor.status or abs(new_speed - compressor.speed) > 100:
                compressor.status = new_status
                compressor.speed = new_speed
                compressor.save()
            
            compressor_data[compressor.compressor_id] = {
                'status': new_status, 
                'speed': new_speed, 
                'target_speed': target_speed,
                'control_source': control_source
            }
        
        return compressor_data

    def _collect_node_data(self, network):
        """Collect current node states"""
        node_data = {}
        for node in network.nodes.all():
            node_data[node.node_id] = {
                'pressure': node.current_pressure,
                'flow': node.current_flow,
                'temperature': node.gas_temperature,
                'type': node.node_type,
                'set_pressure': node.set_pressure,
                'set_flow': node.set_flow,
            }
        return node_data
    
    def _collect_pipe_data(self, network):
        """Collect current pipe states"""
        pipe_data = {}
        for pipe in network.pipes.all():
            pipe_data[pipe.pipe_id] = {
                'flow': pipe.current_flow,
                'from_node': pipe.from_node.node_id,
                'to_node': pipe.to_node.node_id,
                'active': pipe.is_active
            }
        return pipe_data
