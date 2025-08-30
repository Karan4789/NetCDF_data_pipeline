"""
NetCDF file parser for ARGO data
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import netCDF4 as nc

logger = logging.getLogger(__name__)

class NetCDFParser:
    """Handles parsing of ARGO NetCDF files"""
    
    @staticmethod
    def clean_array(arr):
        """Clean array data by removing fill values and NaN"""
        if hasattr(arr, 'mask'):
            return arr.compressed().tolist()
        else:
            return arr[~np.isnan(arr)].tolist() if len(arr) > 0 else []
    
    @staticmethod
    def parse_file(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse NetCDF file and extract key metadata and measurements
        
        Args:
            file_path: Path to NetCDF file
            
        Returns:
            Dictionary containing extracted data or None if parsing fails
        """
        try:
            logger.info(f"Parsing NetCDF file: {os.path.basename(file_path)}")
            
            with nc.Dataset(file_path, 'r') as dataset:
                # Extract metadata
                platform_data = dataset.variables['PLATFORM_NUMBER'][0].data
                # Handle both string and byte array formats
                if hasattr(platform_data, 'tobytes'):
                    platform_number = platform_data.tobytes().decode('utf-8').strip()
                else:
                    platform_number = str(platform_data).strip()
                
                cycle_number = int(dataset.variables['CYCLE_NUMBER'][0].data)
                
                # Extract location and time
                latitude = float(dataset.variables['LATITUDE'][0].data)
                longitude = float(dataset.variables['LONGITUDE'][0].data)
                
                # Handle time conversion
                juld = dataset.variables['JULD'][0].data
                if not np.ma.is_masked(juld):
                    # JULD is days since 1950-01-01 00:00:00 UTC
                    reference_date = datetime(1950, 1, 1)
                    measurement_time = reference_date + pd.Timedelta(days=float(juld))
                else:
                    measurement_time = None
                
                # Extract measurements
                pressure = dataset.variables['PRES'][0].data
                temperature = dataset.variables['TEMP'][0].data
                salinity = dataset.variables['PSAL'][0].data
                
                # Clean data (remove fill values)
                pressure_clean = NetCDFParser.clean_array(pressure)
                temperature_clean = NetCDFParser.clean_array(temperature)
                salinity_clean = NetCDFParser.clean_array(salinity)
                
                parsed_data = {
                    'platform_number': platform_number,
                    'cycle_number': cycle_number,
                    'latitude': latitude if not np.ma.is_masked(latitude) else None,
                    'longitude': longitude if not np.ma.is_masked(longitude) else None,
                    'measurement_time': measurement_time,
                    'pressure': pressure_clean,
                    'temperature': temperature_clean,
                    'salinity': salinity_clean,
                    'num_measurements': len(pressure_clean)
                }
                
                logger.info(f"Successfully parsed data for platform {platform_number}, cycle {cycle_number}")
                return parsed_data
                
        except Exception as e:
            logger.error(f"Error parsing NetCDF file {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def parse_multiple_files(file_paths: list) -> list:
        """
        Parse multiple NetCDF files
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of parsed data dictionaries (excluding failed parses)
        """
        parsed_data_list = []
        
        for file_path in file_paths:
            parsed_data = NetCDFParser.parse_file(file_path)
            if parsed_data:
                parsed_data_list.append(parsed_data)
        
        logger.info(f"Successfully parsed {len(parsed_data_list)} out of {len(file_paths)} files")
        return parsed_data_list
