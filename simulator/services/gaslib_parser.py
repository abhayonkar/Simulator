# GasLib-24 XML Parser for Django Models
import xml.etree.ElementTree as ET
import logging
from django.conf import settings
from ..models import GasNetwork, Node, Pipe

logger = logging.getLogger(__name__)

class GasLibParser:
    """Parser for GasLib-24 network XML files"""
    
    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        self.namespace = {
            'gas': 'http://gaslib.zib.de/Gas',
            'framework': 'http://gaslib.zib.de/Framework'
        }
    
    def parse_and_create_network(self):
        """Parse GasLib-24 XML and create Django models"""
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            # Get network information
            info = root.find('framework:information', self.namespace)
            title = info.find('framework:title', self.namespace).text if info else "GasLib-24"
            doc = info.find('framework:documentation', self.namespace).text if info else "Gas network with 24 nodes"
            
            # --- THIS IS THE FIX ---
            # Delete ALL existing networks and their related components (nodes, pipes, etc.)
            # This ensures a clean import every time.
            logger.info("Deleting all existing network data before reload...")
            GasNetwork.objects.all().delete()
            logger.info("Existing data cleared.")
            # --- END FIX ---

            # Create the new network
            network = GasNetwork.objects.create(
                name=title,
                description=doc
            )
            logger.info(f"Created new network: {title}")
            
            # Parse nodes
            nodes_element = root.find('framework:nodes', self.namespace)
            node_count = 0
            
            if nodes_element is not None:
                # Parse sources
                for source in nodes_element.findall('gas:source', self.namespace):
                    self._create_node(network, source, 'source')
                    node_count += 1
                
                # Parse sinks
                for sink in nodes_element.findall('gas:sink', self.namespace):
                    self._create_node(network, sink, 'sink')
                    node_count += 1
                
                # Parse innodes (junctions)
                for innode in nodes_element.findall('gas:innode', self.namespace):
                    self._create_node(network, innode, 'innode')
                    node_count += 1
            
            # Parse connections (pipes)
            connections_element = root.find('framework:connections', self.namespace)
            pipe_count = 0
            
            if connections_element is not None:
                # We only parse 'pipe' elements for this simulation
                for pipe in connections_element.findall('gas:pipe', self.namespace):
                    self._create_pipe(network, pipe)
                    pipe_count += 1
                
                # Note: compressorStation, resistor, valve elements in the .net file
                # are also under connections, but we model them differently or ignore
                # for this simulation's physics. Compressors and Valves are created
                # separately by the simulation engine.
            
            logger.info(f"Network parsed successfully: {node_count} nodes, {pipe_count} pipes")
            return network
            
        except Exception as e:
            logger.error(f"Error parsing GasLib file: {e}")
            raise
    
    def _create_node(self, network, element, node_type):
        """Create a node from XML element"""
        try:
            node_id = element.get('id')
            alias = element.get('alias', '')
            x = float(element.get('x', 0))
            y = float(element.get('y', 0))
            geo_long = element.get('geoWGS84Long')
            geo_lat = element.get('geoWGS84Lat')
            
            # Height
            height_elem = element.find('gas:height', self.namespace)
            height = float(height_elem.get('value', 0)) if height_elem is not None else 0.0
            
            # Pressure limits
            pressure_min_elem = element.find('gas:pressureMin', self.namespace)
            pressure_max_elem = element.find('gas:pressureMax', self.namespace)
            pressure_min = float(pressure_min_elem.get('value', 1.01325)) if pressure_min_elem is not None else 1.01325
            pressure_max = float(pressure_max_elem.get('value', 81.01325)) if pressure_max_elem is not None else 81.01325
            
            # Flow limits (for sources and sinks)
            flow_min_elem = element.find('gas:flowMin', self.namespace)
            flow_max_elem = element.find('gas:flowMax', self.namespace)
            flow_min = float(flow_min_elem.get('value', 0)) if flow_min_elem is not None else 0.0
            flow_max = float(flow_max_elem.get('value', 10000)) if flow_max_elem is not None else 10000.0
            
            # Gas properties (for sources)
            gas_temp_elem = element.find('gas:gasTemperature', self.namespace)
            calorific_elem = element.find('gas:calorificValue', self.namespace)
            density_elem = element.find('gas:normDensity', self.namespace)
            
            gas_temperature = float(gas_temp_elem.get('value', 20)) if gas_temp_elem is not None else 20.0
            calorific_value = float(calorific_elem.get('value', 36.4543670654)) if calorific_elem is not None else 36.4543670654
            norm_density = float(density_elem.get('value', 0.785)) if density_elem is not None else 0.785
            
            # Set initial pressure and flow
            initial_pressure = (pressure_min + pressure_max) / 2
            initial_flow = 0.0 # Will be controlled by setpoints

            # Create node
            node = Node.objects.create(
                network=network,
                node_id=node_id,
                node_type=node_type,
                alias=alias,
                x=x,
                y=y,
                geo_longitude=float(geo_long) if geo_long else None,
                geo_latitude=float(geo_lat) if geo_lat else None,
                height=height,
                pressure_min=pressure_min,
                pressure_max=pressure_max,
                current_pressure=initial_pressure,
                flow_min=flow_min,
                flow_max=flow_max,
                current_flow=initial_flow,
                # Set initial setpoints based on type
                set_pressure= initial_pressure if node_type == 'source' else pressure_min,
                set_flow= initial_flow,
                gas_temperature=gas_temperature,
                calorific_value=calorific_value,
                norm_density=norm_density
            )
            
            logger.debug(f"Created {node_type} node: {node_id}")
            return node
            
        except Exception as e:
            logger.error(f"Error creating node {element.get('id')}: {e}")
            raise
    
    def _create_pipe(self, network, element):
        """Create a pipe from XML element"""
        try:
            pipe_id = element.get('id')
            alias = element.get('alias', '')
            from_node_id = element.get('from')
            to_node_id = element.get('to')
            
            # Get nodes
            from_node = Node.objects.get(network=network, node_id=from_node_id)
            to_node = Node.objects.get(network=network, node_id=to_node_id)
            
            # Pipe properties (defaults if not specified in XML)
            length_elem = element.find('gas:length', self.namespace)
            diameter_elem = element.find('gas:diameter', self.namespace)
            roughness_elem = element.find('gas:roughness', self.namespace)
            
            # GasLib stores length in km, diameter in mm, roughness in mm
            # Model stores length in km, diameter in m, roughness in m
            
            length = float(length_elem.get('value', 10.0)) if length_elem is not None else 10.0
            
            diameter_mm = float(diameter_elem.get('value', 500)) if diameter_elem is not None else 500.0
            diameter_m = diameter_mm / 1000.0 # Convert mm to m
            
            roughness_mm = float(roughness_elem.get('value', 0.05)) if roughness_elem is not None else 0.05
            roughness_m = roughness_mm / 1000.0 # Convert mm to m
            
            # Create pipe
            pipe = Pipe.objects.create(
                network=network,
                pipe_id=pipe_id,
                alias=alias,
                from_node=from_node,
                to_node=to_node,
                length=length,
                diameter=diameter_m,
                roughness=roughness_m,
                current_flow=0.0,
                is_active=True
            )
            
            logger.debug(f"Created pipe: {pipe_id} ({from_node_id} → {to_node_id})")
            return pipe
            
        except Exception as e:
            logger.error(f"Error creating pipe {element.get('id')}: {e}")
            raise

