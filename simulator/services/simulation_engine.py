# Django Simulation Engine - Python-only gas pipeline simulation
import logging
import time
import random
import math
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import (
    GasNetwork, Node, Pipe, Sensor, PLC, PLCAlarm, Valve, 
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
        
        # PID parameters
        setpoint = 50.0
        kp, ki, kd = 1.0, 0.1, 0.01
        
        # PID calculation
        error = setpoint - current_pressure
        self.integral_error += error * 0.1
        derivative_error = (error - self.last_error) / 0.1
        
        pid_output = kp * error + ki * self.integral_error + kd * derivative_error
        valve_position = max(0, min(100, 50 + pid_output))
        
        self.last_error = error
        
        # Safety checks
        if current_pressure > 80.0:
            self._create_alarm('HIGH_PRESSURE', 'HIGH', f'Pressure {current_pressure:.1f} bar exceeds limit')
        
        return {
            'CONTROL_VALVE_POSITION': valve_position,
            'PRESSURE_IN_TOLERANCE': abs(error) <= 2.0,
            'PID_OUTPUT': pid_output
        }
    
    def _flow_regulation_logic(self, sensor_data, simulation_time):
        """Flow regulation PLC logic"""
        node_id = self.plc.node.node_id
        current_flow = sensor_data.get(f'flow_{node_id}', 100.0)
        
        # Simple flow control
        target_flow = 100.0
        flow_error = target_flow - current_flow
        
        # Adjust valve position based on flow error
        valve_adjustment = flow_error * 0.5
        valve_position = max(0, min(100, 50 + valve_adjustment))
        
        return {
            'FLOW_CONTROL_VALVE': valve_position,
            'FLOW_IN_RANGE': abs(flow_error) <= 10.0,
            'FLOW_ERROR': flow_error
        }
    
    def _compressor_management_logic(self, sensor_data, simulation_time):
        """Compressor management PLC logic"""
        node_id = self.plc.node.node_id
        pressure = sensor_data.get(f'pressure_{node_id}', 50.0)
        
        # Start compressor if pressure is low
        compressor_running = pressure < 45.0
        compressor_speed = 1500 if compressor_running else 0  # RPM
        
        if compressor_running:
            self._create_alarm('COMPRESSOR_START', 'LOW', 'Compressor started due to low pressure')
        
        return {
            'COMPRESSOR_RUNNING': compressor_running,
            'COMPRESSOR_SPEED': compressor_speed,
            'SUCTION_VALVE': compressor_running,
            'DISCHARGE_VALVE': compressor_running
        }
    
    def _valve_control_logic(self, sensor_data, simulation_time):
        """Valve control PLC logic"""
        # Simple valve control based on pressure differential
        positions = {}
        for i in range(3):  # Control up to 3 valves
            valve_id = f'VALVE_{i+1}'
            positions[valve_id] = 50.0 + random.gauss(0, 5)  # Small variations
        
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
        # Simulate occasional leak detection
        leak_detected = random.random() < 0.001  # 0.1% chance per scan
        
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
        
        # Simple temperature control
        target_temp = 25.0
        temp_error = target_temp - temperature
        
        # Heating/cooling control
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
        # Monitor critical parameters
        pressure_ok = all(p <= 80.0 for p in sensor_data.values() if 'pressure' in str(p))
        temperature_ok = all(t <= 70.0 for t in sensor_data.values() if 'temperature' in str(t))
        
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
            
            # Initialize sensors and PLCs
            self._initialize_sensors(network)
            self._initialize_plcs(network)
            self._initialize_valves(network)
            
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
                
                # Update physics simulation
                self._update_physics(simulation_run.network, sensor_data, simulation_time)
                
                # Execute PLC scans
                plc_data = self._execute_plcs(simulation_run.network, sensor_data, simulation_time)
                
                # Update valve positions
                valve_data = self._update_valves(simulation_run.network, plc_data, simulation_time)
                
                # Collect node and pipe data
                node_data = self._collect_node_data(simulation_run.network)
                pipe_data = self._collect_pipe_data(simulation_run.network)
                
                # Store simulation data to PostgreSQL TSDB
                self._write_to_postgres(simulation_run, simulation_time, 
                                      sensor_data, plc_data, valve_data, 
                                      node_data, pipe_data)
                
                # Log progress every 60 seconds
                if step % 60 == 0:
                    logger.info(f"Simulation {simulation_run.run_id}: Step {step}, Time {simulation_time:.1f}s")
                
                # Wait for next time step
                elapsed = time.time() - step_start
                if elapsed < simulation_run.time_step:
                    time.sleep(simulation_run.time_step - elapsed)
                
                step += 1
            
            # Complete simulation
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
                          sensor_data, plc_data, valve_data, node_data, pipe_data):
        """Write simulation data to the PostgreSQL TSDB table"""
        try:
            # Write sensor data
            for sensor_id, value in sensor_data.items():
                self.tsdb_service.write_data_point(
                    simulation_run=simulation_run,
                    timestamp=simulation_time,
                    measurement_type='sensor_reading',
                    object_id=sensor_id,
                    data={'value': value}
                )
            
            # Write PLC data
            for plc_id, outputs in plc_data.items():
                self.tsdb_service.write_data_point(
                    simulation_run=simulation_run,
                    timestamp=simulation_time,
                    measurement_type='plc_output',
                    object_id=plc_id,
                    data=outputs
                )
            
            # Write node data
            for node_id, data in node_data.items():
                self.tsdb_service.write_data_point(
                    simulation_run=simulation_run,
                    timestamp=simulation_time,
                    measurement_type='node_state',
                    object_id=node_id,
                    data=data
                )
                
            # Write pipe data
            for pipe_id, data in pipe_data.items():
                self.tsdb_service.write_data_point(
                    simulation_run=simulation_run,
                    timestamp=simulation_time,
                    measurement_type='pipe_state',
                    object_id=pipe_id,
                    data=data
                )
            
        except Exception as e:
            logger.error(f"Failed to write simulation data to PostgreSQL: {e}")
    
    def _initialize_sensors(self, network):
        """Initialize sensors for the network"""
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
    
    def _initialize_valves(self, network):
        """Initialize valves on pipes"""
        for pipe in network.pipes.all():
            valve_id = f'valve_{pipe.pipe_id}'
            
            Valve.objects.get_or_create(
                valve_id=valve_id,
                defaults={
                    'valve_type': 'CONTROL',
                    'pipe': pipe,
                    'position': 50.0,
                    'is_operational': True,
                    'max_pressure': 100.0,
                    'flow_coefficient': 1.0
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
                    base_value = sensor.node.current_flow
                elif sensor.pipe:
                    base_value = sensor.pipe.current_flow * 3600  # Convert to m³/h
                else:
                    base_value = 100.0
                
                noise = random.gauss(0, 2.0)
                sensor.current_value = max(0, base_value + noise)
            
            sensor.save()
            sensor_data[sensor.sensor_id] = sensor.current_value
        
        return sensor_data
    
    def _update_physics(self, network, sensor_data, simulation_time):
        """Update physics simulation"""
        # Simple physics update - pressure and flow calculations
        for node in network.nodes.all():
            if node.node_type == 'source':
                # Sources maintain pressure with small variations
                node.current_pressure = node.pressure_max * 0.8 + random.gauss(0, 1.0)
                node.current_flow = 100.0 + random.gauss(0, 10.0)
            
            elif node.node_type == 'sink':
                # Sinks consume gas
                node.current_pressure = node.pressure_min * 1.5 + random.gauss(0, 1.0)
                node.current_flow = 80.0 + random.gauss(0, 8.0)
            
            else:  # innode
                # Junctions have intermediate pressures
                node.current_pressure = 50.0 + random.gauss(0, 2.0)
            
            node.save()
        
        # Update pipe flows
        for pipe in network.pipes.all():
            # Simple flow based on pressure difference
            dp = pipe.from_node.current_pressure - pipe.to_node.current_pressure
            pipe.current_flow = max(0, dp * 2.0 + random.gauss(0, 0.5))
            pipe.save()
    
    def _execute_plcs(self, network, sensor_data, simulation_time):
        """Execute all PLC scans"""
        plc_data = {}
        
        for plc in PLC.objects.filter(node__network=network, is_active=True):
            simulator = PLCSimulator(plc)
            outputs = simulator.execute_scan(sensor_data, simulation_time)
            
            # Update PLC outputs
            plc.outputs = outputs
            plc.save()
            
            plc_data[plc.plc_id] = outputs
        
        return plc_data
    
    def _update_valves(self, network, plc_data, simulation_time):
        """Update valve positions based on PLC outputs"""
        valve_data = {}
        
        for valve in Valve.objects.filter(pipe__network=network, is_operational=True):
            # Update valve position based on PLC control or default behavior
            if valve.plc:
                # Get position from PLC output
                control_key = f'CONTROL_VALVE_POSITION'
                if control_key in plc_data.get(valve.plc.plc_id, {}):
                    valve.position = plc_data[valve.plc.plc_id][control_key]
            else:
                # Small random variations if no PLC control
                valve.position += random.gauss(0, 1.0)
                valve.position = max(0, min(100, valve.position))
            
            valve.save()
            valve_data[valve.valve_id] = valve.position
        
        return valve_data
    
    def _collect_node_data(self, network):
        """Collect current node states"""
        node_data = {}
        for node in network.nodes.all():
            node_data[node.node_id] = {
                'pressure': node.current_pressure,
                'flow': node.current_flow,
                'temperature': node.gas_temperature,
                'type': node.node_type
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
