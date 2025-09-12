# Data Manager - Handles data storage and retrieval using PostgreSQL
import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import sql, extras

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data storage and retrieval using PostgreSQL"""
    
    def __init__(self, db_url=None):
        # Use a connection URL from environment variables for security and portability
        # The DATABASE_URL can be set in a .env file or directly in the environment.
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/gas_simulator')
        self.init_database()
        logger.info("Data Manager initialized with PostgreSQL")
    
    def _get_connection(self):
        """Establishes and returns a database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except psycopg2.OperationalError as e:
            logger.error(f"PostgreSQL connection error: {e}")
            raise ConnectionError("Failed to connect to the database. Please check your DATABASE_URL environment variable and database status.") from e
            
    def init_database(self):
        """Initialize PostgreSQL database tables if they don't exist"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # Create simulation data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS simulation_data (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        network_data JSONB,
                        sensor_data JSONB,
                        plc_outputs JSONB
                    )
                ''')
                
                # Create alarms table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alarms (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        plc_id TEXT,
                        alarm_id TEXT,
                        severity TEXT,
                        message TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE
                    )
                ''')
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def store_simulation_data(self, timestamp: datetime, network_data: Dict[str, Any], 
                            sensor_data: Dict[str, Any], plc_outputs: Dict[str, Any]):
        """Store simulation data in PostgreSQL"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO simulation_data (timestamp, network_data, sensor_data, plc_outputs)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    timestamp,
                    json.dumps(network_data),
                    json.dumps(sensor_data),
                    json.dumps(plc_outputs)
                ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Data storage error: {e}")
    
    def get_historical_data(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get historical simulation data from PostgreSQL"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=extras.DictCursor) as cursor:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor.execute('''
                    SELECT timestamp, network_data, sensor_data, plc_outputs
                    FROM simulation_data
                    WHERE timestamp > %s
                    ORDER BY timestamp DESC
                    LIMIT 1000
                ''', (cutoff_time,))
                
                rows = cursor.fetchall()
                conn.close()
                
                historical_data = []
                for row in rows:
                    historical_data.append({
                        'timestamp': row['timestamp'].isoformat(),
                        'network_data': row['network_data'] or {},
                        'sensor_data': row['sensor_data'] or {},
                        'plc_outputs': row['plc_outputs'] or {}
                    })
                
                return historical_data
            
        except Exception as e:
            logger.error(f"Historical data retrieval error: {e}")
            return []

    def store_alarm(self, timestamp: datetime, plc_id: str, alarm_id: str, 
                    severity: str, message: str):
        """Store an alarm event in PostgreSQL"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO alarms (timestamp, plc_id, alarm_id, severity, message)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    timestamp,
                    plc_id,
                    alarm_id,
                    severity,
                    message
                ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Alarm storage error: {e}")

    def get_alarms(self, acknowledged: bool = None) -> List[Dict[str, Any]]:
        """Retrieve alarms from PostgreSQL, optionally filtering by acknowledgment status"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=extras.DictCursor) as cursor:
                if acknowledged is None:
                    cursor.execute('''
                        SELECT id, timestamp, plc_id, alarm_id, severity, message, acknowledged
                        FROM alarms
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''')
                else:
                    cursor.execute('''
                        SELECT id, timestamp, plc_id, alarm_id, severity, message, acknowledged
                        FROM alarms
                        WHERE acknowledged = %s
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''', (acknowledged,))
                
                rows = cursor.fetchall()
                conn.close()
                
                alarms = []
                for row in rows:
                    alarms.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'].isoformat(),
                        'plc_id': row['plc_id'],
                        'alarm_id': row['alarm_id'],
                        'severity': row['severity'],
                        'message': row['message'],
                        'acknowledged': row['acknowledged']
                    })
                
                return alarms
            
        except Exception as e:
            logger.error(f"Alarm retrieval error: {e}")
            return []   
        
    def acknowledge_alarm(self, alarm_id: int):
        """Acknowledge an alarm in PostgreSQL"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE alarms
                    SET acknowledged = TRUE
                    WHERE id = %s
                ''', (alarm_id,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Alarm acknowledgment error: {e}")

# Example usage:
# data_manager = DataManager()
# data_manager.store_simulation_data(datetime.now(), {...}, {...}, {...})               

# alarms = data_manager.get_alarms(acknowledged=False)
# data_manager.acknowledge_alarm(alarm_id=1)    
# historical_data = data_manager.get_historical_data(hours=2)
# Note: Ensure PostgreSQL server is running and accessible via the provided DATABASE_URL.
# If using Docker, ensure the container is running and ports are correctly mapped.
# If you encounter connection issues, verify the database server status and connection parameters.
# If PostgreSQL is running locally and you want to stop it:
# sudo systemctl status postgresql
# sudo systemctl stop postgresql
# optionally disable if you don't want it auto-starting
# sudo systemctl disable postgresql
