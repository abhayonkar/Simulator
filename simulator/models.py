from django.db import models
import json
from datetime import datetime

# GasLib-40 Network Models
class GasNetwork(models.Model):
    """Represents the entire GasLib-40 network"""
    name = models.CharField(max_length=100, default="GasLib-40")
    description = models.TextField(default="Gas network with 40 nodes and 45 arcs")
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Node(models.Model):
    """Represents nodes in the gas network (sources, sinks, junctions)"""
    NODE_TYPES = [
        ('source', 'Gas Source'),
        ('sink', 'Gas Sink'), 
        ('innode', 'Junction Node'),
    ]
    
    network = models.ForeignKey(GasNetwork, on_delete=models.CASCADE, related_name='nodes')
    node_id = models.CharField(max_length=50, unique=True)
    node_type = models.CharField(max_length=10, choices=NODE_TYPES)
    alias = models.CharField(max_length=100, blank=True)
    
    # Geographical coordinates
    x = models.FloatField()
    y = models.FloatField()
    geo_longitude = models.FloatField(null=True, blank=True)
    geo_latitude = models.FloatField(null=True, blank=True)
    height = models.FloatField(default=0.0)  # meters
    
    # Pressure limits and properties
    pressure_min = models.FloatField(default=1.01325)  # bar
    pressure_max = models.FloatField(default=81.01325)  # bar
    current_pressure = models.FloatField(default=50.0)  # bar
    
    # Flow properties (for sources and sinks)
    flow_min = models.FloatField(default=0.0)  # 1000m³/hour
    flow_max = models.FloatField(default=10000.0)  # 1000m³/hour
    current_flow = models.FloatField(default=0.0)  # 1000m³/hour
    
    # Gas properties (for sources)
    gas_temperature = models.FloatField(default=20.0)  # Celsius
    calorific_value = models.FloatField(default=36.4543670654)  # MJ/m³
    norm_density = models.FloatField(default=0.785)  # kg/m³
    
    # Additional properties stored as JSON
    properties = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.node_id} ({self.get_node_type_display()})"

class Pipe(models.Model):
    """Represents pipes connecting nodes in the network"""
    network = models.ForeignKey(GasNetwork, on_delete=models.CASCADE, related_name='pipes')
    pipe_id = models.CharField(max_length=50, unique=True)
    alias = models.CharField(max_length=100, blank=True)
    
    from_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outgoing_pipes')
    to_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='incoming_pipes')
    
    # Pipe properties
    length = models.FloatField(default=10.0)  # km
    diameter = models.FloatField(default=0.5)  # m
    roughness = models.FloatField(default=0.0001)  # m
    
    # Current state
    current_flow = models.FloatField(default=0.0)  # m³/s
    is_active = models.BooleanField(default=True)
    
    # Additional properties
    properties = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.pipe_id}: {self.from_node.node_id} → {self.to_node.node_id}"

# Sensor Models (Simplified - only pressure, temperature, flow)
class Sensor(models.Model):
    """Simplified sensor system - pressure, temperature, flow only"""
    SENSOR_TYPES = [
        ('pressure', 'Pressure Sensor'),
        ('temperature', 'Temperature Sensor'),
        ('flow', 'Flow Rate Sensor'),
    ]
    
    sensor_id = models.CharField(max_length=50, unique=True)
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, null=True, blank=True)
    pipe = models.ForeignKey(Pipe, on_delete=models.CASCADE, null=True, blank=True)
    
    # Sensor properties
    current_value = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20, default="")
    is_active = models.BooleanField(default=True)
    quality = models.CharField(max_length=20, default="GOOD")
    last_update = models.DateTimeField(auto_now=True)
    
    # Calibration and limits
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    calibration_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        location = self.node.node_id if self.node else self.pipe.pipe_id
        return f"{self.sensor_id} ({self.get_sensor_type_display()}) @ {location}"

# PLC Models - Embedded 8 PLCs
class PLC(models.Model):
    """Represents Programmable Logic Controllers"""
    PLC_TYPES = [
        ('PRESSURE_CONTROL', 'Pressure Control PLC'),
        ('FLOW_REGULATION', 'Flow Regulation PLC'),
        ('COMPRESSOR_MANAGEMENT', 'Compressor Management PLC'),
        ('VALVE_CONTROL', 'Valve Control PLC'),
        ('SAFETY_MONITORING', 'Safety Monitoring PLC'),
        ('LEAK_DETECTION', 'Leak Detection PLC'),
        ('TEMPERATURE_CONTROL', 'Temperature Control PLC'),
        ('EMERGENCY_SHUTDOWN', 'Emergency Shutdown PLC'),
    ]
    
    plc_id = models.CharField(max_length=50, unique=True)
    plc_type = models.CharField(max_length=30, choices=PLC_TYPES)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='plcs')
    
    # PLC status
    is_active = models.BooleanField(default=True)
    scan_time = models.FloatField(default=0.1)  # seconds
    last_scan = models.DateTimeField(auto_now=True)
    
    # PLC data stored as JSON
    inputs = models.JSONField(default=dict, blank=True)
    outputs = models.JSONField(default=dict, blank=True)
    memory = models.JSONField(default=dict, blank=True)
    timers = models.JSONField(default=dict, blank=True)
    counters = models.JSONField(default=dict, blank=True)
    
    # Control parameters (specific to PLC type)
    parameters = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.plc_id} ({self.get_plc_type_display()}) @ {self.node.node_id}"

class PLCAlarm(models.Model):
    """PLC alarms and events"""
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    plc = models.ForeignKey(PLC, on_delete=models.CASCADE, related_name='alarms')
    alarm_id = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.CharField(max_length=100, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.plc.plc_id}: {self.alarm_id} ({self.severity})"

# Valve Models
class Valve(models.Model):
    """Represents valves in the pipeline system"""
    VALVE_TYPES = [
        ('CONTROL', 'Control Valve'),
        ('ISOLATION', 'Isolation Valve'),
        ('PRESSURE_RELIEF', 'Pressure Relief Valve'),
        ('CHECK', 'Check Valve'),
    ]
    
    valve_id = models.CharField(max_length=50, unique=True)
    valve_type = models.CharField(max_length=20, choices=VALVE_TYPES)
    pipe = models.ForeignKey(Pipe, on_delete=models.CASCADE, related_name='valves')
    plc = models.ForeignKey(PLC, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Valve state
    position = models.FloatField(default=50.0)  # 0-100% open
    is_operational = models.BooleanField(default=True)
    last_movement = models.DateTimeField(auto_now=True)
    
    # Valve properties
    max_pressure = models.FloatField(default=100.0)  # bar
    flow_coefficient = models.FloatField(default=1.0)
    
    def __str__(self):
        return f"{self.valve_id} ({self.get_valve_type_display()}) @ {self.pipe.pipe_id}"

# Simulation Models
class SimulationRun(models.Model):
    """Represents a simulation run"""
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('STOPPED', 'Stopped'),
    ]
    
    run_id = models.CharField(max_length=50, unique=True)
    network = models.ForeignKey(GasNetwork, on_delete=models.CASCADE)
    
    # Simulation parameters
    duration = models.IntegerField(default=600)  # seconds
    time_step = models.FloatField(default=1.0)  # seconds
    
    # Simulation status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_steps = models.IntegerField(default=0)
    log_file_path = models.CharField(max_length=512, blank=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Run {self.run_id} ({self.status})"

class SimulationData(models.Model):
    """Stores simulation data points"""
    run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='data_points')
    timestamp = models.FloatField()  # simulation time in seconds
    
    # Sensor readings
    sensor_data = models.JSONField(default=dict, blank=True)
    
    # PLC states
    plc_data = models.JSONField(default=dict, blank=True)
    
    # Valve positions
    valve_data = models.JSONField(default=dict, blank=True)
    
    # Node states
    node_data = models.JSONField(default=dict, blank=True)
    
    # Pipe flows
    pipe_data = models.JSONField(default=dict, blank=True)
    
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['run', 'timestamp']
        ordering = ['timestamp']

# Legacy Run model for compatibility
class Run(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=512)
    
    # Link to new simulation system
    simulation_run = models.ForeignKey(SimulationRun, on_delete=models.SET_NULL, null=True, blank=True)