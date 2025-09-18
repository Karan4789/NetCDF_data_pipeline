"""
FTP operations for downloading ARGO NetCDF files
"""
import os
import ftplib
import tempfile
import logging
import sys
import json
from typing import List, Dict, Tuple

# Add config to path
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
sys.path.append(config_path)

from config import Config

logger = logging.getLogger(__name__)

class FTPDownloader:
    """Handles FTP operations for downloading ARGO NetCDF files"""
    
    def __init__(self, ftp_host: str = None, ftp_path: str = None):
        self.ftp_host = ftp_host or Config.FTP_HOST
        self.ftp_path = ftp_path or Config.FTP_PATH
        self.cursor_file = os.path.join(os.path.dirname(__file__), '..', '..', 'ftp_cursor.json')
        
    def _load_cursor(self) -> Dict:
        """Load the cursor that tracks processing progress"""
        if os.path.exists(self.cursor_file):
            try:
                with open(self.cursor_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading cursor file: {str(e)}. Starting fresh.")
                
        return {
            "float_index": 0,
            "last_float": "",
            "last_file": "",
            "dirs_processed": 0,
            "files_processed": 0
        }
        
    def _save_cursor(self, cursor: Dict):
        """Save the processing cursor"""
        try:
            with open(self.cursor_file, 'w') as f:
                json.dump(cursor, f)
        except Exception as e:
            logger.error(f"Error saving cursor file: {str(e)}")
            
    def fetch_files(self, max_files: int = None) -> List[str]:
        """
        Connect to FTP server and download NetCDF files
        
        Args:
            max_files: Maximum number of files to download for testing
            
        Returns:
            List of local file paths to downloaded NetCDF files
        """
        if max_files is None:
            max_files = Config.MAX_FILES
            
        downloaded_files = []
        temp_dir = tempfile.mkdtemp(prefix=Config.TEMP_DIR_PREFIX)
        
        # Load cursor to continue from where we left off
        cursor = self._load_cursor()
        float_index = cursor["float_index"]
        
        try:
            logger.info(f"Connecting to FTP server: {self.ftp_host}")
            with ftplib.FTP(self.ftp_host) as ftp:
                ftp.login()  # Anonymous login
                ftp.cwd(self.ftp_path)
                
                # Get list of float directories
                float_dirs = []
                ftp.retrlines('NLST', float_dirs.append)
                logger.info(f"Found {len(float_dirs)} float directories")
                
                if float_index >= len(float_dirs):
                    logger.info("All float directories processed, resetting to start")
                    float_index = 0
                
                files_downloaded = 0
                processed_float_count = 0
                
                # Start from the last processed float directory
                for i in range(float_index, min(float_index + 3, len(float_dirs))):
                    float_dir = float_dirs[i]
                    if files_downloaded >= max_files:
                        break
                        
                    try:
                        ftp.cwd(f"{self.ftp_path}{float_dir}/profiles")
                        nc_files = []
                        ftp.retrlines('NLST', nc_files.append)
                        
                        # If this is the last float we processed, find where we left off
                        start_idx = 0
                        if float_dir == cursor["last_float"]:
                            try:
                                last_file_idx = nc_files.index(cursor["last_file"])
                                start_idx = last_file_idx + 1
                            except ValueError:
                                # Last file not found, start from beginning
                                start_idx = 0
                        
                        # Download .nc files from this directory, starting from where we left off
                        for nc_file in nc_files[start_idx:]:
                            if files_downloaded >= max_files:
                                break
                            if nc_file.endswith('.nc'):
                                local_path = os.path.join(temp_dir, f"{float_dir}_{nc_file}")
                                
                                with open(local_path, 'wb') as local_file:
                                    ftp.retrbinary(f'RETR {nc_file}', local_file.write)
                                
                                downloaded_files.append(local_path)
                                files_downloaded += 1
                                cursor["last_float"] = float_dir
                                cursor["last_file"] = nc_file
                                logger.info(f"Downloaded: {nc_file} ({files_downloaded}/{max_files})")
                                
                        processed_float_count += 1
                        
                    except ftplib.error_perm as e:
                        logger.warning(f"Permission error accessing {float_dir}: {str(e)}")
                        processed_float_count += 1
                        continue
                    except Exception as e:
                        logger.error(f"Error processing {float_dir}: {str(e)}")
                        processed_float_count += 1
                        continue
                
                # Update cursor for next run
                cursor["float_index"] = (float_index + processed_float_count) % len(float_dirs)
                cursor["dirs_processed"] += processed_float_count
                cursor["files_processed"] += files_downloaded
                self._save_cursor(cursor)
                        
        except Exception as e:
            logger.error(f"Error connecting to FTP server: {str(e)}")
            raise
            
        logger.info(f"Successfully downloaded {len(downloaded_files)} files to {temp_dir}")
        return downloaded_files
    
    def cleanup_files(self, file_paths: List[str]):
        """Clean up downloaded files"""
        for file_path in file_paths:
            try:
                os.remove(file_path)
                logger.debug(f"Removed temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove file {file_path}: {str(e)}")
