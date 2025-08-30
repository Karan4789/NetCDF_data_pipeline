"""
Updated ETL Pipeline for ARGO NetCDF data with normalized database schema
"""
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add paths
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
config_path = os.path.join(project_root, 'config')
src_path = os.path.join(project_root, 'src')
sys.path.extend([project_root, config_path, src_path])

from downloaders.ftp_downloader import FTPDownloader
from parsers.netcdf_parser import NetCDFParser
from database.database import DatabaseManager
from utils.utils import setup_logging
from config import Config

# Setup logging
logger = setup_logging()

class ArgoETLPipeline:
    """Updated ETL Pipeline for ARGO NetCDF data with normalized schema"""
    
    def __init__(self):
        self.ftp_downloader = FTPDownloader()
        self.netcdf_parser = NetCDFParser()
        self.db_manager = DatabaseManager()
        
    def run_pipeline(self, max_files: int = None) -> Dict[str, Any]:
        """
        Run the complete ETL pipeline with normalized data storage
        
        Args:
            max_files: Maximum number of files to process
            
        Returns:
            Dictionary containing pipeline execution results
        """
        if max_files is None:
            max_files = Config.MAX_FILES
            
        results = {
            'start_time': datetime.utcnow(),
            'files_downloaded': 0,
            'files_parsed': 0,
            'profiles_stored': 0,
            'measurements_stored': 0,
            'errors': [],
            'success': False
        }
        
        try:
            logger.info("Starting ARGO ETL Pipeline with normalized schema")
            
            # Step 1: Setup database
            logger.info("Setting up database...")
            self.db_manager.setup_database()
            
            # Step 2: Fetch files from FTP
            logger.info(f"Downloading up to {max_files} files from FTP...")
            downloaded_files = self.ftp_downloader.fetch_files(max_files)
            results['files_downloaded'] = len(downloaded_files)
            
            if not downloaded_files:
                raise Exception("No files were downloaded from FTP server")
            
            # Step 3: Parse NetCDF files
            logger.info("Parsing NetCDF files...")
            parsed_data_list = self.netcdf_parser.parse_multiple_files(downloaded_files)
            results['files_parsed'] = len(parsed_data_list)
            
            if not parsed_data_list:
                raise Exception("No files were successfully parsed")
            
            # Step 4: Store in database with normalized schema
            logger.info("Storing data in normalized database schema...")
            if self.db_manager.store_data(parsed_data_list):
                results['profiles_stored'] = len(parsed_data_list)
                # Calculate total measurements stored
                total_measurements = sum(data.get('num_measurements', 0) for data in parsed_data_list)
                results['measurements_stored'] = total_measurements
                results['success'] = True
            else:
                results['errors'].append("Failed to store data in database")
            
            # Step 5: Cleanup temporary files
            logger.info("Cleaning up temporary files...")
            self.ftp_downloader.cleanup_files(downloaded_files)
            
            # Step 6: Run example analytical query to demonstrate new capabilities
            logger.info("Running example analytical query...")
            analytical_results = self.db_manager.run_analytical_query_example()
            if analytical_results:
                logger.info("Analytical query results:")
                for result in analytical_results:
                    logger.info(f"  {result['depth_range']}: {result['measurement_count']} measurements, "
                               f"avg temp: {result['avg_temperature']:.2f}°C, "
                               f"avg salinity: {result['avg_salinity']:.2f}")
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            results['errors'].append(str(e))
        
        results['end_time'] = datetime.utcnow()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        # Log final results
        self._log_results(results)
        
        return results
    
    def _log_results(self, results: Dict[str, Any]):
        """Log pipeline execution results"""
        logger.info(f"Pipeline completed. Success: {results['success']}")
        logger.info(f"Files downloaded: {results['files_downloaded']}")
        logger.info(f"Files parsed: {results['files_parsed']}")
        logger.info(f"Profiles stored: {results['profiles_stored']}")
        logger.info(f"Measurements stored: {results['measurements_stored']}")
        logger.info(f"Duration: {results['duration']:.2f} seconds")
        
        if results['errors']:
            logger.warning(f"Errors encountered: {results['errors']}")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics including measurements"""
        return self.db_manager.get_database_stats()
    
    def run_data_quality_check(self) -> Dict[str, Any]:
        """
        Run data quality checks that are now possible with normalized schema
        
        Returns:
            Dictionary containing data quality metrics
        """
        logger.info("Running data quality checks...")
        
        try:
            with self.db_manager.get_session() as session:
                from database.models import ArgoMeasurement, ArgoProfile, ArgoFloat
                from sqlalchemy import func
                
                # Quality metrics
                metrics = {}
                
                # 1. Measurements with missing values
                total_measurements = session.query(ArgoMeasurement).count()
                missing_pressure = session.query(ArgoMeasurement).filter(
                    ArgoMeasurement.pressure.is_(None)
                ).count()
                missing_temperature = session.query(ArgoMeasurement).filter(
                    ArgoMeasurement.temperature.is_(None)
                ).count()
                missing_salinity = session.query(ArgoMeasurement).filter(
                    ArgoMeasurement.salinity.is_(None)
                ).count()
                
                metrics['total_measurements'] = total_measurements
                metrics['missing_data'] = {
                    'pressure': missing_pressure,
                    'temperature': missing_temperature,
                    'salinity': missing_salinity
                }
                
                # 2. Temperature range analysis
                temp_stats = session.query(
                    func.min(ArgoMeasurement.temperature),
                    func.max(ArgoMeasurement.temperature),
                    func.avg(ArgoMeasurement.temperature)
                ).filter(ArgoMeasurement.temperature.isnot(None)).first()
                
                if temp_stats:
                    metrics['temperature_stats'] = {
                        'min': float(temp_stats[0]),
                        'max': float(temp_stats[1]),
                        'avg': float(temp_stats[2])
                    }
                
                # 3. Pressure range analysis
                pressure_stats = session.query(
                    func.min(ArgoMeasurement.pressure),
                    func.max(ArgoMeasurement.pressure),
                    func.avg(ArgoMeasurement.pressure)
                ).filter(ArgoMeasurement.pressure.isnot(None)).first()
                
                if pressure_stats:
                    metrics['pressure_stats'] = {
                        'min': float(pressure_stats[0]),
                        'max': float(pressure_stats[1]),
                        'avg': float(pressure_stats[2])
                    }
                
                # 4. Profiles with most measurements
                profile_measurement_counts = session.query(
                    ArgoProfile.id,
                    ArgoProfile.cycle_number,
                    ArgoFloat.platform_number,
                    func.count(ArgoMeasurement.id).label('measurement_count')
                ).join(ArgoMeasurement).join(ArgoFloat).group_by(
                    ArgoProfile.id, ArgoProfile.cycle_number, ArgoFloat.platform_number
                ).order_by(func.count(ArgoMeasurement.id).desc()).limit(5).all()
                
                metrics['top_profiles_by_measurements'] = [
                    {
                        'platform_number': row.platform_number,
                        'cycle_number': row.cycle_number,
                        'measurement_count': row.measurement_count
                    }
                    for row in profile_measurement_counts
                ]
                
                logger.info("Data quality check completed successfully")
                return metrics
                
        except Exception as e:
            logger.error(f"Error running data quality check: {str(e)}")
            return {}
    
    def demonstrate_analytical_capabilities(self):
        """
        Demonstrate the analytical capabilities now available with normalized schema
        """
        logger.info("Demonstrating analytical capabilities of normalized schema...")
        
        print("\n" + "="*60)
        print("ANALYTICAL CAPABILITIES DEMONSTRATION")
        print("="*60)
        
        # Get database stats
        stats = self.get_database_stats()
        print(f"\nDATABASE STATISTICS:")
        print(f"  Total Floats: {stats.get('total_floats', 0)}")
        print(f"  Total Profiles: {stats.get('total_profiles', 0)}")
        print(f"  Total Measurements: {stats.get('total_measurements', 0)}")
        
        # Run quality check
        quality_metrics = self.run_data_quality_check()
        if quality_metrics:
            print(f"\nDATA QUALITY METRICS:")
            if 'missing_data' in quality_metrics:
                missing = quality_metrics['missing_data']
                print(f"  Missing Pressure Values: {missing['pressure']}")
                print(f"  Missing Temperature Values: {missing['temperature']}")
                print(f"  Missing Salinity Values: {missing['salinity']}")
            
            if 'temperature_stats' in quality_metrics:
                temp = quality_metrics['temperature_stats']
                print(f"  Temperature Range: {temp['min']:.2f}°C to {temp['max']:.2f}°C (avg: {temp['avg']:.2f}°C)")
            
            if 'pressure_stats' in quality_metrics:
                pres = quality_metrics['pressure_stats']
                print(f"  Pressure Range: {pres['min']:.2f} to {pres['max']:.2f} (avg: {pres['avg']:.2f})")
        
        # Run analytical query
        analytical_results = self.db_manager.run_analytical_query_example()
        if analytical_results:
            print(f"\nDEPTH-BASED ANALYSIS:")
            for result in analytical_results:
                print(f"  {result['depth_range']}: {result['measurement_count']} measurements")
                if result['avg_temperature']:
                    print(f"    Avg Temperature: {result['avg_temperature']:.2f}°C")
                if result['avg_salinity']:
                    print(f"    Avg Salinity: {result['avg_salinity']:.2f}")
        
        print("\n" + "="*60)
        print("These analytics were NOT possible with the old schema!")
        print("="*60)
