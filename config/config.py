"""
Configuration settings for ARGO ETL Pipeline
"""
import os
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL with proper handling of special characters"""
    # Try direct DATABASE_URL first
    direct_url = os.getenv('DATABASE_URL')
    if direct_url:
        return direct_url
    
    # Fallback: build from components
    username = os.getenv('DB_USERNAME', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    host = os.getenv('DB_HOST', 'db.ovpnqlkqkobmcmarados.supabase.co')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_DATABASE', 'postgres')
    
    # URL encode the password to handle special characters
    encoded_password = urllib.parse.quote_plus(password)
    
    # Build the URL
    return f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"

class Config:
    """Configuration class for ARGO ETL Pipeline"""
    
    # Supabase settings
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Database settings (Supabase PostgreSQL)
    DATABASE_URL = get_database_url()
    
    # FTP settings
    FTP_HOST = os.getenv('FTP_HOST', 'ftp.ifremer.fr')
    FTP_PATH = os.getenv('FTP_PATH', '/ifremer/argo/dac/incois/')
    
    # Pipeline settings
    MAX_FILES = int(os.getenv('MAX_FILES', '5'))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'argo_etl.log'
    
    # Temporary directory settings
    TEMP_DIR_PREFIX = 'argo_data_'
