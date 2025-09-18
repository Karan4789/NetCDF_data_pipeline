import logging
from typing import Dict, Any, List

from downloaders.ftp_downloader import FTPDownloader
from parsers.netcdf_parser import NetCDFParser
from database.database import DatabaseManager
from utils.utils import setup_logging
from config import Config
from datetime import datetime

logger = setup_logging()

class ArgoETLPipeline:
    """ETL pipeline using a simpler Pathway version, feeding parsed rows via rows input"""
    
    def __init__(self):
        self.ftp_downloader = FTPDownloader()
        self.netcdf_parser = NetCDFParser()
        self.db_manager = DatabaseManager()
    
    def run_pipeline(self, max_files: int = None) -> Dict[str, Any]:
        

        if max_files is None:
            max_files = int(Config.MAX_FILES)

        results = {
            "start_time": datetime.utcnow(),
            "files_downloaded": 0,
            "files_parsed": 0,
            "records_stored": 0,
            "errors": [],
            "success": False,
        }

        try:
            logger.info("Starting ARGO ETL Pipeline (adapted mode)")

            # Step 1: Download files
            logger.info(f"Downloading up to {max_files} files from FTP...")
            downloaded_files = self.ftp_downloader.fetch_files(max_files)
            results["files_downloaded"] = len(downloaded_files)

            if not downloaded_files:
                raise Exception("No files downloaded")

            # Step 2: Parse NetCDF files
            logger.info("Parsing NetCDF files...")
            parsed_data_list = self.netcdf_parser.parse_multiple_files(downloaded_files)
            results["files_parsed"] = len(parsed_data_list)
            
            if not parsed_data_list:
                raise Exception("No files were successfully parsed")

            # Step 3: Store in database
            logger.info("Storing data in database...")
            if self.db_manager.store_data(parsed_data_list):
                results["records_stored"] = len(parsed_data_list)
                results["success"] = True
            else:
                results["errors"].append("Failed to store data in database")
            # Step 5: Cleanup temporary files
            logger.info("Cleaning up temporary files...")
            self.ftp_downloader.cleanup_files(downloaded_files)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["errors"].append(str(e))

        results["end_time"] = datetime.utcnow()
        results["duration"] = (
            results["end_time"] - results["start_time"]
        ).total_seconds()

        # Log summary
        self._log_results(results)
        
        return results
        
    def _log_results(self, results):
        """Log the pipeline results"""
        logger.info(f"Pipeline results: {results}")
        logger.info(f"Success: {results['success']}")
        logger.info(f"Files downloaded: {results['files_downloaded']}")
        logger.info(f"Files parsed: {results['files_parsed']}")
        logger.info(f"Records stored: {results['records_stored']}")
        logger.info(f"Duration: {results['duration']:.2f} sec")
        if results["errors"]:
            logger.warning(f"Errors: {results['errors']}")
    
    def get_database_stats(self):
        """Get database statistics"""
        stats = self.db_manager.get_database_stats()
        return {
            "total_floats": stats.get("floats", 0),
            "total_profiles": stats.get("profiles", 0)
        }
