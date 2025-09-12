# Gas Pipeline Digital Twin Simulator
# Consolidated version combining all variants with 8 custom PLCs
import os
import sys
import time
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from physics.gas_physics_engine import GasPhysicsEngine
from scada.scada_system import SCADASystem
from plc.plc_manager import PLCManager
from sensors.sensor_manager import SensorManager
from database.data_manager import DataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gas_pipeline_simulator_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class GasPipelineSimulator:
    """Main gas pipeline simulation coordinator"""
    
    def __init__(self):
        logger.info("Initializing Gas Pipeline Digital Twin Simulator")
        
        # Initialize core components
        self.data_manager = DataManager()
        self.physics_engine = GasPhysicsEngine()
        self.sensor_manager = SensorManager()
        self.plc_manager = PLCManager(self.sensor_manager)
        self.scada_system = SCADASystem(self.plc_manager, self.sensor_manager)
        
        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None
        
        # Load GasLib-134 network data
        self.load_network_data()
        
        logger.info("Gas Pipeline Simulator initialized successfully")
    
    def load_network_data(self):
        """Load and initialize GasLib-134 network data"""
        try:
            # Load the network topology from physics engine
            self.network_data = self.physics_engine.load_gaslib_network()
            logger.info(f"Loaded network with {len(self.network_data['nodes'])} nodes and {len(self.network_data['pipes'])} pipes")
            
            # Initialize sensors at strategic nodes
            self.sensor_manager.initialize_sensors(self.network_data)
            
            # Initialize PLCs across the network
            self.plc_manager.initialize_plcs(self.network_data)
            
        except Exception as e:
            logger.error(f"Failed to load network data: {e}")
            # Create a minimal network for testing
            self.create_test_network()
    
    def create_test_network(self):
        """Create a minimal test network if GasLib data is not available"""
        logger.warning("Creating test network - GasLib-134 data not found")
        self.network_data = {
            'nodes': {
                'N1': {'type': 'source', 'x': 0, 'y': 0, 'pressure': 60.0},
                'N2': {'type': 'junction', 'x': 100, 'y': 50, 'pressure': 50.0},
                'N3': {'type': 'compressor', 'x': 200, 'y': 75, 'pressure': 55.0},
                'N4': {'type': 'junction', 'x': 300, 'y': 100, 'pressure': 45.0},
                'N5': {'type': 'sink', 'x': 400, 'y': 125, 'pressure': 40.0},
            },
            'pipes': {
                'P1': {'from_node': 'N1', 'to_node': 'N2', 'length': 10.0, 'diameter': 0.6},
                'P2': {'from_node': 'N2', 'to_node': 'N3', 'length': 10.0, 'diameter': 0.6},
                'P3': {'from_node': 'N3', 'to_node': 'N4', 'length': 10.0, 'diameter': 0.6},
                'P4': {'from_node': 'N4', 'to_node': 'N5', 'length': 10.0, 'diameter': 0.6},
            }
        }
        
        # Initialize with test data
        self.sensor_manager.initialize_sensors(self.network_data)
        self.plc_manager.initialize_plcs(self.network_data)
    
    def simulation_loop(self):
        """Main simulation loop"""
        logger.info("Starting simulation loop")
        step_count = 0
        
        while self.simulation_running:
            try:
                step_count += 1
                
                # Update sensor readings
                sensor_data = self.sensor_manager.update_all_sensors(self.network_data)
                
                # Run physics simulation step
                self.physics_engine.simulate_step(self.network_data, sensor_data)
                
                # Update PLC logic
                plc_outputs = self.plc_manager.execute_all_plcs(sensor_data)
                
                # Update SCADA system
                scada_data = self.scada_system.update(self.network_data, sensor_data, plc_outputs)
                
                # Store data in database
                self.data_manager.store_simulation_data(
                    timestamp=datetime.now(),
                    network_data=self.network_data,
                    sensor_data=sensor_data,
                    plc_outputs=plc_outputs
                )
                
                # Emit real-time data via WebSocket
                if step_count % 10 == 0:  # Emit every 10 steps to avoid overwhelming
                    socketio.emit('simulation_update', {
                        'timestamp': datetime.now().isoformat(),
                        'network_data': self.network_data,
                        'sensor_data': sensor_data,
                        'plc_outputs': plc_outputs,
                        'system_status': scada_data['system_status']
                    })
                
                # Sleep for simulation step interval
                time.sleep(0.1)  # 10 Hz simulation
                
            except Exception as e:
                logger.error(f"Simulation step error: {e}")
                time.sleep(1)
    
    def start_simulation(self):
        """Start the simulation"""
        if not self.simulation_running:
            self.simulation_running = True
            self.simulation_thread = threading.Thread(target=self.simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            logger.info("Simulation started")
            return True
        return False
    
    def stop_simulation(self):
        """Stop the simulation"""
        if self.simulation_running:
            self.simulation_running = False
            if self.simulation_thread:
                self.simulation_thread.join(timeout=5)
            logger.info("Simulation stopped")
            return True
        return False
    
    def get_current_status(self):
        """Get current system status"""
        return {
            'simulation_running': self.simulation_running,
            'network_nodes': len(self.network_data['nodes']),
            'network_pipes': len(self.network_data['pipes']),
            'active_plcs': self.plc_manager.get_active_plc_count(),
            'active_sensors': self.sensor_manager.get_active_sensor_count(),
            'system_status': self.scada_system.get_system_status()
        }

# Initialize the simulator
simulator = GasPipelineSimulator()

# Flask Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html', 
                         system_status=simulator.get_current_status())

@app.route('/api/system/status')
def get_system_status():
    """Get current system status"""
    return jsonify(simulator.get_current_status())

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start simulation"""
    success = simulator.start_simulation()
    return jsonify({'success': success, 'message': 'Simulation started' if success else 'Already running'})

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop simulation"""
    success = simulator.stop_simulation()
    return jsonify({'success': success, 'message': 'Simulation stopped' if success else 'Not running'})

@app.route('/api/network/data')
def get_network_data():
    """Get current network data"""
    return jsonify({
        'nodes': simulator.network_data['nodes'],
        'pipes': simulator.network_data['pipes'],
        'sensors': simulator.sensor_manager.get_all_sensor_data(),
        'plcs': simulator.plc_manager.get_all_plc_status()
    })

@app.route('/api/plc/<plc_id>/control', methods=['POST'])
def control_plc(plc_id):
    """Send control command to specific PLC"""
    command = request.json
    result = simulator.plc_manager.send_command_to_plc(plc_id, command)
    return jsonify(result)

@app.route('/api/historical/data')
def get_historical_data():
    """Get historical simulation data"""
    hours = request.args.get('hours', 1, type=int)
    data = simulator.data_manager.get_historical_data(hours=hours)
    return jsonify(data)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to Gas Pipeline Simulator'})
    emit('system_status', simulator.get_current_status())
    logger.info('Client connected via WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected from WebSocket')

@socketio.on('request_data')
def handle_request_data():
    """Handle real-time data request"""
    emit('simulation_update', {
        'timestamp': datetime.now().isoformat(),
        'network_data': simulator.network_data,
        'sensor_data': simulator.sensor_manager.get_all_sensor_data(),
        'plc_outputs': simulator.plc_manager.get_all_plc_status(),
        'system_status': simulator.scada_system.get_system_status()
    })

if __name__ == '__main__':
    logger.info("Starting Gas Pipeline Digital Twin Simulator")
    
    # Start the simulation automatically
    simulator.start_simulation()
    
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)