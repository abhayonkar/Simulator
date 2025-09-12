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
    Run, GasNetwork, Node, Pipe, Sensor, PLC, PLCAlarm, Valve,
    SimulationRun, SimulationData
)
from .services.gaslib_parser import GasLibParser
from .services.simulation_engine import SimulationEngine

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
    simulation_count = SimulationRun.objects.count()
    active_alarms = PLCAlarm.objects.filter(acknowledged=False).count()
    
    # Get recent simulations
    recent_simulations = SimulationRun.objects.order_by('-created')[:5]
    
    # Get networks
    networks = GasNetwork.objects.all()
    
    context = {
        'title': 'Gas Pipeline Simulator - GasLib-40',
        'network_count': network_count,
        'node_count': node_count,
        'pipe_count': pipe_count,
        'plc_count': plc_count,
        'sensor_count': sensor_count,
        'simulation_count': simulation_count,
        'active_alarms': active_alarms,
        'recent_simulations': recent_simulations,
        'networks': networks,
        'total_runs': Run.objects.count(),  # Legacy compatibility
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
            # Use first available network
            network = GasNetwork.objects.first()
            if not network:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No network available. Please load GasLib-40 network first.'
                })
        else:
            network = get_object_or_404(GasNetwork, id=network_id)
        
        # Simulation parameters
        duration = data.get('duration', 600)  # seconds
        time_step = data.get('time_step', 1.0)  # seconds
        
        # Validate parameters
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
            'message': 'Simulation started successfully'
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
        
        # Update any running simulations to stopped
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
        # Get latest simulation
        latest_simulation = SimulationRun.objects.order_by('-created').first()
        
        # Get system statistics
        total_networks = GasNetwork.objects.count()
        total_nodes = Node.objects.count()
        total_pipes = Pipe.objects.count()
        total_sensors = Sensor.objects.count()
        total_plcs = PLC.objects.count()
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
    """Get simulation data points"""
    try:
        simulation = get_object_or_404(SimulationRun, id=simulation_id)
        
        # Get data points (limit to last 1000 for performance)
        data_points = simulation.data_points.order_by('timestamp')[:1000]
        
        timestamps = []
        sensor_series = {}
        plc_series = {}
        
        for point in data_points:
            timestamps.append(point.timestamp)
            
            # Extract sensor data
            for sensor_id, value in point.sensor_data.items():
                if sensor_id not in sensor_series:
                    sensor_series[sensor_id] = []
                sensor_series[sensor_id].append(value)
            
            # Extract PLC data
            for plc_id, outputs in point.plc_data.items():
                if plc_id not in plc_series:
                    plc_series[plc_id] = {}
                for output_key, output_value in outputs.items():
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
            'data_points': len(timestamps)
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
        'api_version': '1.0',
        'simulator': 'Gas Pipeline Digital Twin - GasLib-40',
        'endpoints': {
            'status': '/api/status/',
            'start': '/api/start/', 
            'stop': '/api/stop/',
            'load_gaslib': '/api/load_gaslib/',
            'network': '/api/network/<id>/',
            'simulation': '/api/simulation/<id>/',
            'sensors': '/api/sensors/',
            'plcs': '/api/plcs/',
            'alarms': '/api/alarms/'
        },
        'message': 'Django-only Gas Pipeline Simulator using GasLib-40 network data'
    })