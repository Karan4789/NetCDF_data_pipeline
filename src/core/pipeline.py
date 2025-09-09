"""
Main ETL Pipeline for ARGO NetCDF data
"""
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add config to path
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
sys.path.append(config_path)

from downloaders.ftp_downloader import FTPDownloader
from parsers.netcdf_parser import NetCDFParser
from database.database import DatabaseManager
from utils.utils import setup_logging
from utils.embedding_service import EmbeddingService
from config import Config

# Setup logging
logger = setup_logging()

class ArgoETLPipeline:
    """Main ETL Pipeline for ARGO NetCDF data"""
    
    def __init__(self):
        self.ftp_downloader = FTPDownloader()
        self.netcdf_parser = NetCDFParser()
        self.db_manager = DatabaseManager()
        self.embedding_service = EmbeddingService()
        
    def run_pipeline(self, max_files: int = None) -> Dict[str, Any]:
        """
        Run the complete ETL pipeline
        
        Args:
            max_files: Maximum number of files to process
            
        Returns:
            Dictionary containing pipeline execution results
        """
        if max_files is None:
            max_files = int(Config.MAX_FILES)
            
        results = {
            'start_time': datetime.utcnow(),
            'files_downloaded': 0,
            'files_parsed': 0,
            'records_stored': 0,
            'embeddings_generated': 0,
            'errors': [],
            'success': False
        }
        
        try:
            logger.info("Starting ARGO ETL Pipeline")
            
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
            
            # Step 3.5: Generate embeddings if service is available
            if self.embedding_service.is_available():
                logger.info("Generating embeddings for parsed data...")
                embeddings_generated = 0
                for data in parsed_data_list:
                    embedding = self.embedding_service.generate_profile_embedding(data)
                    if embedding:
                        data['embedding'] = embedding
                        embeddings_generated += 1
                results['embeddings_generated'] = embeddings_generated
                logger.info(f"Generated {embeddings_generated} embeddings")
            else:
                logger.info("Embedding service not available, skipping embedding generation")
            
            # Step 4: Store in database
            logger.info("Storing data in database...")
            if self.db_manager.store_data(parsed_data_list):
                results['records_stored'] = len(parsed_data_list)
                results['success'] = True
            else:
                results['errors'].append("Failed to store data in database")
            
            # Step 5: Cleanup temporary files
            logger.info("Cleaning up temporary files...")
            self.ftp_downloader.cleanup_files(downloaded_files)
            
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
        logger.info(f"Records stored: {results['records_stored']}")
        logger.info(f"Embeddings generated: {results['embeddings_generated']}")
        logger.info(f"Duration: {results['duration']:.2f} seconds")
        
        if results['errors']:
            logger.warning(f"Errors encountered: {results['errors']}")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics"""
        return {
            'total_floats': self.db_manager.get_float_count(),
            'total_profiles': self.db_manager.get_profile_count()
        }
    
    def generate_embeddings_for_existing_profiles(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Generate embeddings for profiles that don't have them yet
        
        Args:
            batch_size: Number of profiles to process at once
            
        Returns:
            Dictionary with processing results
        """
        if not self.embedding_service.is_available():
            logger.warning("Embedding service not available")
            return {'success': False, 'message': 'Embedding service not available'}
        
        results = {
            'start_time': datetime.utcnow(),
            'profiles_processed': 0,
            'embeddings_generated': 0,
            'errors': [],
            'success': False
        }
        
        try:
            logger.info(f"Processing embeddings for existing profiles (batch size: {batch_size})...")
            
            profiles = self.db_manager.get_profiles_without_embeddings(batch_size)
            results['profiles_processed'] = len(profiles)
            
            embeddings_generated = 0
            for profile in profiles:
                try:
                    # Create profile data dictionary for embedding generation
                    profile_data = {
                        'platform_number': profile.float.platform_number if profile.float else 'Unknown',
                        'cycle_number': profile.cycle_number,
                        'latitude': profile.latitude,
                        'longitude': profile.longitude,
                        'measurement_time': profile.measurement_time,
                        'temperature': profile.temperature_values,
                        'salinity': profile.salinity_values,
                        'pressure': profile.pressure_values,
                        'num_measurements': profile.num_measurements
                    }
                    
                    embedding = self.embedding_service.generate_profile_embedding(profile_data)
                    if embedding:
                        if self.db_manager.update_profile_embedding(str(profile.id), embedding):
                            embeddings_generated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing profile {profile.id}: {str(e)}")
                    results['errors'].append(f"Profile {profile.id}: {str(e)}")
            
            results['embeddings_generated'] = embeddings_generated
            results['success'] = True
            
            logger.info(f"Generated embeddings for {embeddings_generated} out of {len(profiles)} profiles")
            
        except Exception as e:
            logger.error(f"Error in embedding generation process: {str(e)}")
            results['errors'].append(str(e))
        
        results['end_time'] = datetime.utcnow()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        return results
