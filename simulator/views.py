from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from django.utils import timezone
import json
import os
import logging

from .models import (
    Run, GasNetwork, Node, Pipe, Sensor, PLC, PLCAlarm, Valve, Compressor,
    SimulationRun, SimulationTimeSeriesData
)
from .services.gaslib_parser import GasLibParser
from .services.simulation_engine import SimulationEngine
from .services.postgres_tsdb_service import get_postgres_tsdb_service

logger = logging.getLogger(__name__)

# Global simulation engine instance
simulation_engine = SimulationEngine()

def index(request):
    """Main dashboard for gas pipeline simulator"""
    # Get network and simulation statistics
    network_count = GasNetwork.objects.count()
    node_count = Node.objects.count()
    pipe_count = Pipe.objects.count()
    plc_count = PLC.objects.count()
    sensor_count = Sensor.objects.count()
    valve_count = Valve.objects.count() # New count
    compressor_count = Compressor.objects.count() # New count
    simulation_count = SimulationRun.objects.count()
    active_alarms = PLCAlarm.objects.filter(acknowledged=False).count()
    
    # Get recent simulations
    recent_simulations = SimulationRun.objects.order_by('-created')[:5]
    
    # Get networks
    networks = GasNetwork.objects.all()
    
    # Get control components for the new section
    valves = Valve.objects.all()
    compressors = Compressor.objects.all()
    nodes = Node.objects.filter(node_type__in=['source', 'sink']).all()
    
    context = {
        'title': 'Gas Pipeline Simulator - GasLib-40',
        'network_count': network_count,
        'node_count': node_count,
        'pipe_count': pipe_count,
        'plc_count': plc_count,
        'sensor_count': sensor_count,
        'valve_count': valve_count, # Pass new count
        'compressor_count': compressor_count, # Pass new count
        'simulation_count': simulation_count,
        'active_alarms': active_alarms,
        'recent_simulations': recent_simulations,
        'networks': networks,
        'total_runs': Run.objects.count(),  # Legacy compatibility
        
        # New control data
        'valves': valves,
        'compressors': compressors,
        'control_nodes': nodes,
    }
    
    return render(request, 'simulator/index.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def load_gaslib_network(request):
    """Load GasLib-40 network from XML file"""
    try:
        # Path to GasLib-40 file
        gaslib_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'GasLib-40-v1-20211130',
            'GasLib-40-v1-20211130.net'
        )
        
        if not os.path.exists(gaslib_file):
            return JsonResponse({
                'status': 'error',
                'message': f'GasLib-40 file not found at {gaslib_file}'
            })
        
        # Parse and create network
        parser = GasLibParser(gaslib_file)
        
        with transaction.atomic():
            network = parser.parse_and_create_network()
        
        # NOTE: Sensors, PLCs, Valves, Compressors are initialized when simulation starts.
        logger.info(f"Successfully loaded GasLib-40 network: {network.name}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'GasLib-40 network loaded successfully',
            'network_id': network.id,
            'network_name': network.name,
            'nodes': network.nodes.count(),
            'pipes': network.pipes.count()
        })
        
    except Exception as e:
        logger.error(f"Error loading GasLib-40 network: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error loading network: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def start_simulation(request):
    """Start a new simulation run"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        # Get network
        network_id = data.get('network_id')
        if not network_id:
            network = GasNetwork.objects.first()
            if not network:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No network available. Please load GasLib-40 network first.'
                })
        else:
            network = get_object_or_404(GasNetwork, id=network_id)
        
        duration = data.get('duration', 600)  # seconds
        time_step = data.get('time_step', 1.0)  # seconds
        
        if duration <= 0 or duration > 3600:  # Max 1 hour
            return JsonResponse({
                'status': 'error',
                'message': 'Duration must be between 1 and 3600 seconds'
            })
        
        if time_step <= 0 or time_step > 60:
            return JsonResponse({
                'status': 'error',
                'message': 'Time step must be between 0.1 and 60 seconds'
            })
        
        # Start simulation
        simulation_run = simulation_engine.start_simulation(
            network_id=network.id,
            duration=duration,
            time_step=time_step
        )
        
        # Create legacy Run record for compatibility
        run = Run.objects.create(
            path=f'/tmp/sim_run_{simulation_run.run_id}',
            simulation_run=simulation_run
        )
        
        logger.info(f"Started simulation {simulation_run.run_id}")
        
        return JsonResponse({
            'status': 'success',
            'run_id': simulation_run.run_id,
            'simulation_id': simulation_run.id,
            'legacy_run_id': run.id,
            'network': network.name,
            'duration': duration,
            'time_step': time_step,
            'message': 'Simulation started successfully. Components initialized.'
        })
        
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error starting simulation: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def stop_simulation(request):
    """Stop the current simulation"""
    try:
        simulation_engine.stop_simulation()
        
        running_sims = SimulationRun.objects.filter(status='RUNNING')
        running_sims.update(status='STOPPED')
        
        return JsonResponse({
            'status': 'success',
            'message': 'Simulation stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error stopping simulation: {str(e)}'
        })

def simulation_status(request):
    """Get simulation status"""
    try:
        latest_simulation = SimulationRun.objects.order_by('-created').first()
        
        total_networks = GasNetwork.objects.count()
        total_nodes = Node.objects.count()
        total_pipes = Pipe.objects.count()
        total_sensors = Sensor.objects.count()
        total_plcs = PLC.objects.count()
        total_valves = Valve.objects.count() # New count
        total_compressors = Compressor.objects.count() # New count
        active_alarms = PLCAlarm.objects.filter(acknowledged=False).count()
        
        response_data = {
            'status': 'operational',
            'message': 'Gas Pipeline Simulator is operational',
            'total_runs': Run.objects.count(),
            'simulation_runs': SimulationRun.objects.count(),
            'networks': total_networks,
            'nodes': total_nodes,
            'pipes': total_pipes,
            'sensors': total_sensors,
            'plcs': total_plcs,
            'valves': total_valves, # Add to status
            'compressors': total_compressors, # Add to status
            'active_alarms': active_alarms,
            'engine_running': simulation_engine.running
        }
        
        if latest_simulation:
            response_data.update({
                'latest_simulation': {
                    'run_id': latest_simulation.run_id,
                    'status': latest_simulation.status,
                    'network': latest_simulation.network.name,
                    'duration': latest_simulation.duration,
                    'total_steps': latest_simulation.total_steps,
                    'created': latest_simulation.created.isoformat()
                }
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error getting simulation status: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting status: {str(e)}'
        })
        
# --- New Control Endpoints ---

@csrf_exempt
@require_http_methods(["POST"])
def control_valve(request, valve_id):
    """Set the control position for a specific valve (manual override)"""
    try:
        data = json.loads(request.body)
        position = data.get('position')
        
        if position is None or not 0 <= position <= 100:
            return JsonResponse({'status': 'error', 'message': 'Invalid position. Must be between 0 and 100.'}, status=400)
        
        valve = get_object_or_404(Valve, valve_id=valve_id)
        
        # Set set_position to enable manual override. -1.0 means PLC control.
        valve.set_position = float(position)
        valve.save()
        
        logger.info(f"Manual control set for Valve {valve_id}: Position {position}%")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Valve {valve_id} position set to {position}%. Control is now Manual.',
            'new_setpoint': valve.set_position
        })
        
    except Valve.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': f'Valve {valve_id} not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error controlling valve {valve_id}: {e}")
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def control_valve_auto(request, valve_id):
    """Set the control mode for a specific valve back to Auto (PLC)"""
    try:
        valve = get_object_or_404(Valve, valve_id=valve_id)
        
        # Setting set_position to -1.0 disables manual override, reverting to PLC control.
        valve.set_position = -1.0
        valve.save()
        
        logger.info(f"Auto control enabled for Valve {valve_id}.")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Valve {valve_id} control set to Auto (PLC).',
            'new_setpoint': valve.set_position
        })
        
    except Valve.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': f'Valve {valve_id} not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error setting valve {valve_id} to auto: {e}")
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def control_compressor(request, compressor_id):
    """Set the command and speed for a specific compressor (manual override)"""
    try:
        data = json.loads(request.body)
        command = data.get('command') # ON, OFF, AUTO
        speed = data.get('speed') # Target speed (RPM)
        
        compressor = get_object_or_404(Compressor, compressor_id=compressor_id)
        
        if command not in ['ON', 'OFF', 'AUTO']:
             return JsonResponse({'status': 'error', 'message': 'Invalid command. Must be ON, OFF, or AUTO.'}, status=400)
        
        # Only validate speed if not AUTO and command is ON
        if command == 'ON' and speed is None:
            return JsonResponse({'status': 'error', 'message': 'Speed must be provided when command is ON.'}, status=400)

        # Set the manual control fields
        compressor.set_command = command
        
        if command == 'AUTO':
             # Set speed back to auto signal
             compressor.set_speed = -1.0
             message = f'Compressor {compressor_id} control set to Auto (PLC).'
        else:
             # Manual control: set target speed if provided and valid
             if speed is not None and 0 <= speed <= compressor.max_speed:
                 compressor.set_speed = float(speed)
                 message = f'Compressor {compressor_id} command set to {command} with speed {speed} RPM. Control is Manual.'
             elif command == 'OFF':
                 compressor.set_speed = 0.0
                 message = f'Compressor {compressor_id} command set to OFF. Control is Manual.'
             else:
                 return JsonResponse({'status': 'error', 'message': f'Invalid speed. Must be between 0 and {compressor.max_speed}.'}, status=400)
                 

        compressor.save()
        logger.info(message)
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'new_command': compressor.set_command,
            'new_speed_setpoint': compressor.set_speed
        })
        
    except Compressor.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': f'Compressor {compressor_id} not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error controlling compressor {compressor_id}: {e}")
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def control_node(request, node_id):
    """Set the target pressure or flow for a source/sink node (manual override)"""
    try:
        data = json.loads(request.body)
        set_pressure = data.get('set_pressure')
        set_flow = data.get('set_flow')
        
        node = get_object_or_404(Node, node_id=node_id)
        message = []
        
        if set_pressure is not None:
            pressure = float(set_pressure)
            if node.pressure_min <= pressure <= node.pressure_max:
                node.set_pressure = pressure
                message.append(f"Set Pressure to {pressure} bar.")
            else:
                return JsonResponse({'status': 'error', 'message': f'Pressure setpoint {pressure} out of safe range ({node.pressure_min} - {node.pressure_max}).'}, status=400)

        if set_flow is not None:
            flow = float(set_flow)
            if node.flow_min <= flow <= node.flow_max:
                node.set_flow = flow
                message.append(f"Set Flow to {flow} x1000m³/h.")
            else:
                return JsonResponse({'status': 'error', 'message': f'Flow setpoint {flow} out of safe range ({node.flow_min} - {node.flow_max}).'}, status=400)
        
        if not message:
            return JsonResponse({'status': 'error', 'message': 'No valid setpoint (set_pressure or set_flow) provided.'}, status=400)
        
        node.save()
        final_message = f'Node {node_id} controls updated: ' + ' '.join(message)
        logger.info(final_message)
        
        return JsonResponse({
            'status': 'success',
            'message': final_message,
            'new_set_pressure': node.set_pressure,
            'new_set_flow': node.set_flow
        })
        
    except Node.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': f'Node {node_id} not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error controlling node {node_id}: {e}")
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)


# Remaining functions are kept as they were in the original file (simulation_data, alarms_list, acknowledge_alarm, plc_status, sensor_readings, api_root, network_data)
def network_data(request, network_id):
    """Get network topology and current state"""
    try:
        network = get_object_or_404(GasNetwork, id=network_id)
        
        # Get nodes data
        nodes_data = []
        for node in network.nodes.all():
            nodes_data.append({
                'id': node.node_id,
                'type': node.node_type,
                'x': node.x,
                'y': node.y,
                'pressure': node.current_pressure,
                'flow': node.current_flow,
                'temperature': node.gas_temperature,
                'pressure_min': node.pressure_min,
                'pressure_max': node.pressure_max
            })
        
        # Get pipes data
        pipes_data = []
        for pipe in network.pipes.all():
            pipes_data.append({
                'id': pipe.pipe_id,
                'from': pipe.from_node.node_id,
                'to': pipe.to_node.node_id,
                'flow': pipe.current_flow,
                'length': pipe.length,
                'diameter': pipe.diameter,
                'active': pipe.is_active
            })
        
        # Get sensors data
        sensors_data = []
        for sensor in Sensor.objects.filter(node__network=network):
            sensors_data.append({
                'id': sensor.sensor_id,
                'type': sensor.sensor_type,
                'location': sensor.node.node_id if sensor.node else sensor.pipe.pipe_id,
                'value': sensor.current_value,
                'unit': sensor.unit,
                'quality': sensor.quality
            })
        
        # Get PLCs data
        plcs_data = []
        for plc in PLC.objects.filter(node__network=network):
            plcs_data.append({
                'id': plc.plc_id,
                'type': plc.plc_type,
                'node': plc.node.node_id,
                'active': plc.is_active,
                'inputs': len(plc.inputs),
                'outputs': len(plc.outputs),
                'alarms': plc.alarms.filter(acknowledged=False).count()
            })
        
        return JsonResponse({
            'status': 'success',
            'network': {
                'id': network.id,
                'name': network.name,
                'description': network.description
            },
            'nodes': nodes_data,
            'pipes': pipes_data,
            'sensors': sensors_data,
            'plcs': plcs_data
        })
        
    except Exception as e:
        logger.error(f"Error getting network data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting network data: {str(e)}'
        })

def simulation_data(request, simulation_id):
    """Get simulation data points from PostgreSQL"""
    try:
        simulation = get_object_or_404(SimulationRun, id=simulation_id)
        
        # Get limit from request parameters
        limit = int(request.GET.get('limit', 1000))
        
        # Query PostgreSQL for simulation data
        tsdb_service = get_postgres_tsdb_service()
        data_points = tsdb_service.get_simulation_data(simulation_id=simulation.id, limit=limit)
        
        # Process data into time series format
        timestamps = []
        sensor_series = {}
        plc_series = {}
        
        # Process data points
        for point in data_points:
            timestamp = point.timestamp
            
            # Use timestamp from the record, not the current time
            if timestamp not in timestamps:
                timestamps.append(timestamp)
            
            if point.measurement_type == 'sensor_reading':
                sensor_id = point.object_id
                if sensor_id not in sensor_series:
                    sensor_series[sensor_id] = []
                sensor_series[sensor_id].append(point.data.get('value'))
            
            elif point.measurement_type == 'plc_output':
                plc_id = point.object_id
                if plc_id not in plc_series:
                    plc_series[plc_id] = {}
                
                # Iterate over outputs in the JSONField and append to series
                for output_key, output_value in point.data.items():
                    if output_key not in plc_series[plc_id]:
                        plc_series[plc_id][output_key] = []
                    plc_series[plc_id][output_key].append(output_value)
        
        return JsonResponse({
            'status': 'success',
            'simulation': {
                'run_id': simulation.run_id,
                'status': simulation.status,
                'duration': simulation.duration,
                'total_steps': simulation.total_steps
            },
            'timestamps': timestamps,
            'sensors': sensor_series,
            'plcs': plc_series,
            'data_points': len(data_points),
            'tsdb_status': 'connected' if data_points else 'no_data'
        })
        
    except Exception as e:
        logger.error(f"Error getting simulation data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting simulation data: {str(e)}'
        })

def alarms_list(request):
    """Get list of alarms"""
    try:
        # Get active alarms
        active_alarms = PLCAlarm.objects.filter(acknowledged=False).order_by('-timestamp')[:50]
        
        alarms_data = []
        for alarm in active_alarms:
            alarms_data.append({
                'id': alarm.id,
                'plc_id': alarm.plc.plc_id,
                'plc_type': alarm.plc.get_plc_type_display(),
                'node_id': alarm.plc.node.node_id,
                'alarm_id': alarm.alarm_id,
                'severity': alarm.severity,
                'message': alarm.message,
                'timestamp': alarm.timestamp.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'alarms': alarms_data,
            'total_active': len(alarms_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting alarms: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting alarms: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_alarm(request, alarm_id):
    """Acknowledge an alarm"""
    try:
        data = json.loads(request.body) if request.body else {}
        acknowledged_by = data.get('acknowledged_by', 'User')
        
        alarm = get_object_or_404(PLCAlarm, id=alarm_id)
        alarm.acknowledged = True
        alarm.acknowledged_by = acknowledged_by
        alarm.acknowledged_at = timezone.now()
        alarm.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Alarm {alarm.alarm_id} acknowledged successfully'
        })
        
    except Exception as e:
        logger.error(f"Error acknowledging alarm: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error acknowledging alarm: {str(e)}'
        })

def plc_status(request):
    """Get PLC status overview"""
    try:
        plcs_data = []
        for plc in PLC.objects.filter(is_active=True):
            plcs_data.append({
                'id': plc.plc_id,
                'type': plc.get_plc_type_display(),
                'node': plc.node.node_id,
                'scan_time': plc.scan_time,
                'active': plc.is_active,
                'inputs': len(plc.inputs),
                'outputs': len(plc.outputs),
                'memory_used': len(plc.memory),
                'active_alarms': plc.alarms.filter(acknowledged=False).count(),
                'last_scan': plc.last_scan.isoformat() if plc.last_scan else None
            })
        
        return JsonResponse({
            'status': 'success',
            'plcs': plcs_data,
            'total_active': len(plcs_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting PLC status: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting PLC status: {str(e)}'
        })

def sensor_readings(request):
    """Get current sensor readings"""
    try:
        sensors_data = []
        for sensor in Sensor.objects.filter(is_active=True):
            location = sensor.node.node_id if sensor.node else sensor.pipe.pipe_id
            sensors_data.append({
                'id': sensor.sensor_id,
                'type': sensor.get_sensor_type_display(),
                'location': location,
                'value': sensor.current_value,
                'unit': sensor.unit,
                'quality': sensor.quality,
                'last_update': sensor.last_update.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'sensors': sensors_data,
            'total_active': len(sensors_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting sensor readings: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting sensor readings: {str(e)}'
        })

def api_root(request):
    """API root endpoint to prevent 404 spam"""
    return JsonResponse({
        'api_version': '1.1',
        'simulator': 'Gas Pipeline Digital Twin - GasLib-40',
        'endpoints': {
            'status': '/api/status/',
            'start': '/api/simulation/start/', 
            'stop': '/api/simulation/stop/',
            'load_network': '/api/network/load/',
            'control_valve': '/api/control/valve/<valve_id>/', # New
            'control_valve_auto': '/api/control/valve/<valve_id>/auto/', # New
            'control_compressor': '/api/control/compressor/<compressor_id>/', # New
            'control_node': '/api/control/node/<node_id>/', # New (for Source/Sink setpoints)
            'network_data': '/api/network/<id>/',
            'simulation_data': '/api/simulation/<id>/data/',
            'sensors': '/api/sensors/readings/',
            'plcs': '/api/plcs/status/',
            'alarms': '/api/alarms/'
        },
        'message': 'Django-only Gas Pipeline Simulator using GasLib-40 network data'
    })
