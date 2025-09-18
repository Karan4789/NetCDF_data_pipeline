"""
Database operations for ARGO ETL Pipeline
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

from .models import Base, ArgoFloat, ArgoProfile
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles database operations for ARGO data"""
    
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
        Store parsed data in database using SQLAlchemy
        
        Args:
            parsed_data_list: List of dictionaries containing parsed NetCDF data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                floats_processed = set()
                profiles_created = 0
                
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

                        profile = ArgoProfile(
                            float_id=argo_float.id,
                            cycle_number=data['cycle_number'],
                            latitude=data['latitude'],
                            longitude=data['longitude'],
                            measurement_time=data['measurement_time'],
                            pressure_values=str(data['pressure']),
                            temperature_values=str(data['temperature']),
                            salinity_values=str(data['salinity']),
                            num_measurements=data['num_measurements'],
                        )
                        
                        session.add(profile)
                        profiles_created += 1
                    else:
                        logger.info(f"Profile already exists for platform {platform_number}, cycle {data['cycle_number']}")
                
                session.commit()
                logger.info(f"Successfully stored {len(floats_processed)} floats and {profiles_created} profiles")
                return True
                
        except Exception as e:
            logger.error(f"Error storing data in database: {str(e)}")
            if 'session' in locals():
                session.rollback()
            return False
    
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
    
    def get_database_stats(self):
        """
        Return number of floats and profiles in the database.
        """
        with self.get_session() as session:
            from .models import ArgoFloat, ArgoProfile
            float_count = session.query(ArgoFloat).count()
            profile_count = session.query(ArgoProfile).count()
            return {
                "floats": float_count,
                "profiles": profile_count
            }
