"""
FTP operations for downloading ARGO NetCDF files
"""
import os
import ftplib
import tempfile
import logging
import sys
from typing import List

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
        
        try:
            logger.info(f"Connecting to FTP server: {self.ftp_host}")
            with ftplib.FTP(self.ftp_host) as ftp:
                ftp.login()  # Anonymous login
                ftp.cwd(self.ftp_path)
                
                # Get list of float directories
                float_dirs = []
                ftp.retrlines('NLST', float_dirs.append)
                logger.info(f"Found {len(float_dirs)} float directories")
                
                files_downloaded = 0
                for float_dir in float_dirs[:3]:  # Limit to first 3 float directories
                    if files_downloaded >= max_files:
                        break
                        
                    try:
                        ftp.cwd(f"{self.ftp_path}{float_dir}/profiles")
                        nc_files = []
                        ftp.retrlines('NLST', nc_files.append)
                        
                        # Download .nc files from this directory
                        for nc_file in nc_files:
                            if files_downloaded >= max_files:
                                break
                            if nc_file.endswith('.nc'):
                                local_path = os.path.join(temp_dir, f"{float_dir}_{nc_file}")
                                
                                with open(local_path, 'wb') as local_file:
                                    ftp.retrbinary(f'RETR {nc_file}', local_file.write)
                                
                                downloaded_files.append(local_path)
                                files_downloaded += 1
                                logger.info(f"Downloaded: {nc_file} ({files_downloaded}/{max_files})")
                                
                    except ftplib.error_perm as e:
                        logger.warning(f"Permission error accessing {float_dir}: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing {float_dir}: {str(e)}")
                        continue
                        
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
