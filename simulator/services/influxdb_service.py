# InfluxDB Service for Time-Series Data Storage
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from django.conf import settings
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)

class InfluxDBService:
    """
    Service for handling time-series data storage in InfluxDB.
    Manages sensor readings, PLC data, and simulation time-series data.
    """
    
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self._lock = threading.Lock()
        self._connected = False
        
        # Get InfluxDB configuration from Django settings
        self.config = getattr(settings, 'INFLUXDB_CONFIG', {
            'url': 'http://localhost:8086',
            'token': '',
            'org': 'gas_sim',
            'bucket': 'gas_pipeline_data'
        })
        
        # Initialize connection
        self.connect()
    
    def connect(self) -> bool:
        """Connect to InfluxDB"""
        try:
            with self._lock:
                if self._connected:
                    return True
                
                # For local development without InfluxDB, use dummy mode
                if not self.config['token']:
                    logger.warning("InfluxDB token not provided. Running in dummy mode.")
                    self._connected = False
                    return False
                
                self.client = InfluxDBClient(
                    url=self.config['url'],
                    token=self.config['token'],
                    org=self.config['org']
                )
                
                # Test connection
                ready = self.client.ready()
                if ready:
                    self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                    self.query_api = self.client.query_api()
                    self._connected = True
                    logger.info(f"Connected to InfluxDB at {self.config['url']}")
                    return True
                else:
                    logger.error("InfluxDB not ready")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from InfluxDB"""
        try:
            with self._lock:
                if self.client:
                    self.client.close()
                    self.client = None
                    self.write_api = None
                    self.query_api = None
                    self._connected = False
                    logger.info("Disconnected from InfluxDB")
        except Exception as e:
            logger.error(f"Error disconnecting from InfluxDB: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to InfluxDB"""
        return self._connected
    
    def write_sensor_data(self, sensor_id: str, sensor_type: str, value: float, 
                         timestamp: Optional[datetime] = None, 
                         tags: Optional[Dict[str, str]] = None,
                         fields: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write sensor data to InfluxDB
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor (pressure, temperature, flow)
            value: Sensor reading value
            timestamp: Timestamp of reading (defaults to now)
            tags: Additional tags for the measurement
            fields: Additional fields for the measurement
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._connected:
            logger.debug(f"InfluxDB not connected. Skipping sensor data write for {sensor_id}")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Build tags
            measurement_tags = {
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
            }
            if tags:
                measurement_tags.update(tags)
            
            # Build fields
            measurement_fields = {'value': value}
            if fields:
                measurement_fields.update(fields)
            
            # Create point
            point = Point("sensor_reading") \
                .tag("sensor_id", sensor_id) \
                .tag("sensor_type", sensor_type)
            
            # Add additional tags
            for key, val in measurement_tags.items():
                if key not in ['sensor_id', 'sensor_type']:  # Avoid duplicates
                    point = point.tag(key, str(val))
            
            # Add fields
            for key, val in measurement_fields.items():
                if isinstance(val, (int, float)):
                    point = point.field(key, val)
                else:
                    point = point.field(key, str(val))
            
            # Set timestamp
            point = point.time(timestamp, WritePrecision.S)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.config['bucket'], record=point)
            
            logger.debug(f"Wrote sensor data: {sensor_id} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write sensor data to InfluxDB: {e}")
            return False
    
    def write_plc_data(self, plc_id: str, plc_type: str, outputs: Dict[str, Any],
                      timestamp: Optional[datetime] = None,
                      tags: Optional[Dict[str, str]] = None) -> bool:
        """
        Write PLC output data to InfluxDB
        
        Args:
            plc_id: PLC identifier
            plc_type: Type of PLC
            outputs: PLC output dictionary
            timestamp: Timestamp of data
            tags: Additional tags
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._connected:
            logger.debug(f"InfluxDB not connected. Skipping PLC data write for {plc_id}")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Write each output as a separate measurement
            for output_name, output_value in outputs.items():
                point = Point("plc_output") \
                    .tag("plc_id", plc_id) \
                    .tag("plc_type", plc_type) \
                    .tag("output_name", output_name)
                
                # Add additional tags
                if tags:
                    for key, val in tags.items():
                        point = point.tag(key, str(val))
                
                # Add value field
                if isinstance(output_value, (int, float)):
                    point = point.field("value", output_value)
                elif isinstance(output_value, bool):
                    point = point.field("value", 1 if output_value else 0)
                    point = point.field("bool_value", output_value)
                else:
                    point = point.field("value", str(output_value))
                
                # Set timestamp
                point = point.time(timestamp, WritePrecision.S)
                
                # Write to InfluxDB
                self.write_api.write(bucket=self.config['bucket'], record=point)
            
            logger.debug(f"Wrote PLC data: {plc_id} with {len(outputs)} outputs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write PLC data to InfluxDB: {e}")
            return False
    
    def write_simulation_data(self, simulation_id: str, step: int, time_elapsed: float,
                            node_data: Dict[str, Dict[str, float]],
                            pipe_data: Dict[str, Dict[str, float]],
                            timestamp: Optional[datetime] = None) -> bool:
        """
        Write simulation step data to InfluxDB
        
        Args:
            simulation_id: Simulation run identifier
            step: Simulation step number
            time_elapsed: Elapsed simulation time
            node_data: Node data dictionary
            pipe_data: Pipe data dictionary
            timestamp: Timestamp of data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._connected:
            logger.debug(f"InfluxDB not connected. Skipping simulation data write for {simulation_id}")
            return False
            
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Write node data
            for node_id, node_values in node_data.items():
                point = Point("simulation_node") \
                    .tag("simulation_id", simulation_id) \
                    .tag("node_id", node_id) \
                    .field("step", step) \
                    .field("time_elapsed", time_elapsed)
                
                # Add node field values
                for field_name, field_value in node_values.items():
                    if isinstance(field_value, (int, float)):
                        point = point.field(field_name, field_value)
                
                point = point.time(timestamp, WritePrecision.S)
                self.write_api.write(bucket=self.config['bucket'], record=point)
            
            # Write pipe data
            for pipe_id, pipe_values in pipe_data.items():
                point = Point("simulation_pipe") \
                    .tag("simulation_id", simulation_id) \
                    .tag("pipe_id", pipe_id) \
                    .field("step", step) \
                    .field("time_elapsed", time_elapsed)
                
                # Add pipe field values
                for field_name, field_value in pipe_values.items():
                    if isinstance(field_value, (int, float)):
                        point = point.field(field_name, field_value)
                
                point = point.time(timestamp, WritePrecision.S)
                self.write_api.write(bucket=self.config['bucket'], record=point)
            
            logger.debug(f"Wrote simulation data for step {step}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write simulation data to InfluxDB: {e}")
            return False
    
    def query_sensor_data(self, sensor_id: str, start_time: datetime, 
                         end_time: Optional[datetime] = None,
                         limit: int = 1000) -> List[Dict]:
        """
        Query sensor data from InfluxDB
        
        Args:
            sensor_id: Sensor identifier to query
            start_time: Start time for query
            end_time: End time for query (defaults to now)
            limit: Maximum number of records to return
            
        Returns:
            List of sensor data records
        """
        if not self._connected:
            logger.debug("InfluxDB not connected. Returning empty sensor data")
            return []
            
        try:
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            
            # Build query
            query = f'''
                from(bucket: "{self.config['bucket']}")
                |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, 
                        stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
                |> filter(fn: (r) => r._measurement == "sensor_reading")
                |> filter(fn: (r) => r.sensor_id == "{sensor_id}")
                |> limit(n: {limit})
            '''
            
            # Execute query
            tables = self.query_api.query(query)
            
            # Convert to list of dictionaries
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        'time': record.get_time(),
                        'sensor_id': record.values.get('sensor_id'),
                        'sensor_type': record.values.get('sensor_type'),
                        'value': record.get_value(),
                        'field': record.get_field()
                    })
            
            logger.debug(f"Queried {len(results)} sensor records for {sensor_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query sensor data from InfluxDB: {e}")
            return []
    
    def query_simulation_data(self, simulation_id: str, measurement_type: str = "simulation_node",
                            start_step: int = 0, end_step: Optional[int] = None,
                            limit: int = 1000) -> List[Dict]:
        """
        Query simulation data from InfluxDB
        
        Args:
            simulation_id: Simulation identifier
            measurement_type: Type of measurement (simulation_node or simulation_pipe)
            start_step: Starting step number
            end_step: Ending step number (optional)
            limit: Maximum number of records
            
        Returns:
            List of simulation data records
        """
        if not self._connected:
            logger.debug("InfluxDB not connected. Returning empty simulation data")
            return []
            
        try:
            # Build query
            query = f'''
                from(bucket: "{self.config['bucket']}")
                |> range(start: -24h)
                |> filter(fn: (r) => r._measurement == "{measurement_type}")
                |> filter(fn: (r) => r.simulation_id == "{simulation_id}")
                |> filter(fn: (r) => r.step >= {start_step})
            '''
            
            if end_step is not None:
                query += f'|> filter(fn: (r) => r.step <= {end_step})'
            
            query += f'|> limit(n: {limit})'
            
            # Execute query
            tables = self.query_api.query(query)
            
            # Convert to list of dictionaries
            results = []
            for table in tables:
                for record in table.records:
                    result_dict = {
                        'time': record.get_time(),
                        'simulation_id': record.values.get('simulation_id'),
                        'step': record.values.get('step'),
                        'time_elapsed': record.values.get('time_elapsed'),
                        'field': record.get_field(),
                        'value': record.get_value()
                    }
                    
                    # Add measurement-specific fields
                    if measurement_type == "simulation_node":
                        result_dict['node_id'] = record.values.get('node_id')
                    elif measurement_type == "simulation_pipe":
                        result_dict['pipe_id'] = record.values.get('pipe_id')
                    
                    results.append(result_dict)
            
            logger.debug(f"Queried {len(results)} simulation records for {simulation_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query simulation data from InfluxDB: {e}")
            return []
    
    def get_latest_sensor_values(self, sensor_ids: List[str]) -> Dict[str, float]:
        """
        Get latest values for multiple sensors
        
        Args:
            sensor_ids: List of sensor identifiers
            
        Returns:
            Dictionary mapping sensor_id to latest value
        """
        if not self._connected:
            return {}
            
        try:
            results = {}
            
            for sensor_id in sensor_ids:
                query = f'''
                    from(bucket: "{self.config['bucket']}")
                    |> range(start: -1h)
                    |> filter(fn: (r) => r._measurement == "sensor_reading")
                    |> filter(fn: (r) => r.sensor_id == "{sensor_id}")
                    |> filter(fn: (r) => r._field == "value")
                    |> last()
                '''
                
                tables = self.query_api.query(query)
                for table in tables:
                    for record in table.records:
                        results[sensor_id] = record.get_value()
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get latest sensor values: {e}")
            return {}

# Global instance
influxdb_service = InfluxDBService()

def get_influxdb_service() -> InfluxDBService:
    """Get the global InfluxDB service instance"""
    return influxdb_service