# PostgreSQL Service for Time-Series Data Storage
import logging
import threading
from django.conf import settings
from ..models import SimulationTimeSeriesData, SimulationRun

logger = logging.getLogger(__name__)

class PostgresTSDBService:
    """
    Service for handling time-series data storage in PostgreSQL.
    Manages simulation readings in a structured format within the Django ORM.
    """
    
    def __init__(self):
        self._connected = True # Connection is managed by Django's ORM
        logger.info("PostgreSQL TSDB Service initialized. Using Django's ORM.")

    def is_connected(self) -> bool:
        """Check if connected to PostgreSQL (always true if Django is running)"""
        return self._connected
        
    def write_data_point(self, 
                         simulation_run: SimulationRun, 
                         timestamp: float,
                         measurement_type: str,
                         object_id: str,
                         data: dict) -> bool:
        """
        Write a single time-series data point to the database.
        
        Args:
            simulation_run: The SimulationRun instance for this data.
            timestamp: The simulation time in seconds.
            measurement_type: The type of measurement (e.g., 'sensor_reading', 'plc_output').
            object_id: The ID of the object the data relates to (e.g., node_id, pipe_id).
            data: A dictionary containing the actual data points.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            SimulationTimeSeriesData.objects.create(
                simulation_run=simulation_run,
                timestamp=timestamp,
                measurement_type=measurement_type,
                object_id=object_id,
                data=data
            )
            return True
        except Exception as e:
            logger.error(f"Failed to write data point to PostgreSQL: {e}")
            return False
            
    def get_simulation_data(self, simulation_id: int, limit: int = 1000):
        """
        Retrieve all time-series data for a specific simulation run.
        
        Args:
            simulation_id: The ID of the simulation run.
            limit: The maximum number of records to retrieve.
            
        Returns:
            A QuerySet of SimulationTimeSeriesData objects.
        """
        try:
            return SimulationTimeSeriesData.objects.filter(
                simulation_run_id=simulation_id
            ).order_by('timestamp')[:limit]
        except Exception as e:
            logger.error(f"Failed to retrieve simulation data from PostgreSQL: {e}")
            return []

def get_postgres_tsdb_service() -> PostgresTSDBService:
    """Get the global PostgreSQL TSDB service instance"""
    return PostgresTSDBService()
