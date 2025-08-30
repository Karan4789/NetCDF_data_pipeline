"""
Updated Database operations for ARGO ETL Pipeline with normalized schema
"""
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add config to path
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
sys.path.append(config_path)

from .models import Base, ArgoFloat, ArgoProfile, ArgoMeasurement
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles database operations for ARGO data with normalized schema"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def setup_database(self):
        """Create database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def store_data(self, parsed_data_list: List[Dict[str, Any]]) -> bool:
        """
        Store parsed data in database using normalized schema
        
        Args:
            parsed_data_list: List of dictionaries containing parsed NetCDF data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                floats_processed = set()
                profiles_created = 0
                measurements_created = 0
                
                for data in parsed_data_list:
                    platform_number = data['platform_number']
                    
                    # Get or create float record
                    argo_float = session.query(ArgoFloat).filter(
                        ArgoFloat.platform_number == platform_number
                    ).first()
                    
                    if not argo_float:
                        argo_float = ArgoFloat(
                            platform_number=platform_number,
                            first_location_lat=data['latitude'],
                            first_location_lon=data['longitude'],
                            first_measurement_time=data['measurement_time'],
                            total_cycles=1
                        )
                        session.add(argo_float)
                        session.flush()  # Get the ID
                        floats_processed.add(platform_number)
                        logger.info(f"Created new float record: {platform_number}")
                    else:
                        # Update total cycles if needed
                        current_cycle = data['cycle_number']
                        if current_cycle > argo_float.total_cycles:
                            argo_float.total_cycles = current_cycle
                            argo_float.updated_at = datetime.utcnow()
                    
                    # Check if profile already exists
                    existing_profile = session.query(ArgoProfile).filter(
                        ArgoProfile.float_id == argo_float.id,
                        ArgoProfile.cycle_number == data['cycle_number']
                    ).first()
                    
                    if not existing_profile:
                        # Create profile record (metadata only)
                        profile = ArgoProfile(
                            float_id=argo_float.id,
                            cycle_number=data['cycle_number'],
                            latitude=data['latitude'],
                            longitude=data['longitude'],
                            measurement_time=data['measurement_time'],
                            num_measurements=data['num_measurements']
                        )
                        
                        session.add(profile)
                        session.flush()  # Get the profile ID
                        profiles_created += 1
                        
                        # Create individual measurements
                        measurements_in_profile = self._create_measurements(
                            session, 
                            profile.id, 
                            data['pressure'], 
                            data['temperature'], 
                            data['salinity']
                        )
                        measurements_created += measurements_in_profile
                        
                    else:
                        logger.info(f"Profile already exists for platform {platform_number}, cycle {data['cycle_number']}")
                
                session.commit()
                logger.info(f"Successfully stored {len(floats_processed)} floats, {profiles_created} profiles, and {measurements_created} measurements")
                return True
                
        except Exception as e:
            logger.error(f"Error storing data in database: {str(e)}")
            if 'session' in locals():
                session.rollback()
            return False
    
    def _create_measurements(self, session: Session, profile_id: str, 
                           pressure_list: List[float], 
                           temperature_list: List[float], 
                           salinity_list: List[float]) -> int:
        """
        Create individual measurement records for a profile
        
        Args:
            session: Database session
            profile_id: ID of the profile
            pressure_list: List of pressure values
            temperature_list: List of temperature values
            salinity_list: List of salinity values
            
        Returns:
            Number of measurements created
        """
        # Find the maximum length among all measurement arrays
        max_length = max(
            len(pressure_list) if pressure_list else 0,
            len(temperature_list) if temperature_list else 0,
            len(salinity_list) if salinity_list else 0
        )
        
        measurements_created = 0
        
        for i in range(max_length):
            # Get values at index i, or None if the list is shorter
            pressure = pressure_list[i] if i < len(pressure_list) else None
            temperature = temperature_list[i] if i < len(temperature_list) else None
            salinity = salinity_list[i] if i < len(salinity_list) else None
            
            # Only create measurement if at least one value is not None
            if pressure is not None or temperature is not None or salinity is not None:
                measurement = ArgoMeasurement(
                    profile_id=profile_id,
                    measurement_order=i,
                    pressure=pressure,
                    temperature=temperature,
                    salinity=salinity
                )
                session.add(measurement)
                measurements_created += 1
        
        return measurements_created
    
    def get_float_count(self) -> int:
        """Get total number of floats in database"""
        try:
            with self.get_session() as session:
                return session.query(ArgoFloat).count()
        except Exception as e:
            logger.error(f"Error getting float count: {str(e)}")
            return 0
    
    def get_profile_count(self) -> int:
        """Get total number of profiles in database"""
        try:
            with self.get_session() as session:
                return session.query(ArgoProfile).count()
        except Exception as e:
            logger.error(f"Error getting profile count: {str(e)}")
            return 0
    
    def get_measurement_count(self) -> int:
        """Get total number of individual measurements in database"""
        try:
            with self.get_session() as session:
                return session.query(ArgoMeasurement).count()
        except Exception as e:
            logger.error(f"Error getting measurement count: {str(e)}")
            return 0
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get comprehensive database statistics"""
        return {
            'total_floats': self.get_float_count(),
            'total_profiles': self.get_profile_count(),
            'total_measurements': self.get_measurement_count()
        }
    
    def get_profile_with_measurements(self, profile_id: str) -> Dict[str, Any]:
        """
        Get a complete profile with all its measurements
        Useful for testing and verification
        
        Args:
            profile_id: ID of the profile to retrieve
            
        Returns:
            Dictionary containing profile data and measurements
        """
        try:
            with self.get_session() as session:
                profile = session.query(ArgoProfile).filter(
                    ArgoProfile.id == profile_id
                ).first()
                
                if not profile:
                    return {}
                
                measurements = session.query(ArgoMeasurement).filter(
                    ArgoMeasurement.profile_id == profile_id
                ).order_by(ArgoMeasurement.measurement_order).all()
                
                return {
                    'profile': {
                        'id': str(profile.id),
                        'float_platform': profile.float.platform_number,
                        'cycle_number': profile.cycle_number,
                        'latitude': profile.latitude,
                        'longitude': profile.longitude,
                        'measurement_time': profile.measurement_time,
                        'num_measurements': profile.num_measurements
                    },
                    'measurements': [
                        {
                            'order': m.measurement_order,
                            'pressure': m.pressure,
                            'temperature': m.temperature,
                            'salinity': m.salinity
                        }
                        for m in measurements
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting profile with measurements: {str(e)}")
            return {}
    
    def run_analytical_query_example(self) -> List[Dict[str, Any]]:
        """
        Example analytical query that wouldn't be possible with the old schema
        
        Returns:
            List of results showing the power of the normalized schema
        """
        try:
            with self.get_session() as session:
                # Example: Get average temperature by pressure ranges across all profiles
                from sqlalchemy import func, case
                
                depth_case = case(
                    (ArgoMeasurement.pressure < 100, '0-100m'),
                    (ArgoMeasurement.pressure < 500, '100-500m'), 
                    (ArgoMeasurement.pressure < 1000, '500-1000m'),
                    else_='1000m+'
                ).label('depth_range')
                
                query = session.query(
                    depth_case,
                    func.count(ArgoMeasurement.id).label('measurement_count'),
                    func.avg(ArgoMeasurement.temperature).label('avg_temperature'),
                    func.avg(ArgoMeasurement.salinity).label('avg_salinity')
                ).filter(
                    ArgoMeasurement.temperature.isnot(None),
                    ArgoMeasurement.pressure.isnot(None)
                ).group_by(depth_case)
                
                results = []
                for row in query.all():
                    results.append({
                        'depth_range': row.depth_range,
                        'measurement_count': row.measurement_count,
                        'avg_temperature': float(row.avg_temperature) if row.avg_temperature else None,
                        'avg_salinity': float(row.avg_salinity) if row.avg_salinity else None
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error running analytical query: {str(e)}")
            return []
