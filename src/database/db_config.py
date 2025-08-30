"""
Alternative database configuration for handling special characters in passwords
"""
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Handle database configuration with special characters"""
    
    @staticmethod
    def build_database_url():
        """Build database URL with proper encoding"""
        # Get components separately
        username = os.getenv('DB_USERNAME', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        host = os.getenv('DB_HOST', 'db.ovpnqlkqkobmcmarados.supabase.co')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_DATABASE', 'postgres')
        
        # URL encode the password to handle special characters
        encoded_password = urllib.parse.quote_plus(password)
        
        # Build the URL
        database_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
        
        return database_url
    
    @staticmethod
    def get_database_url():
        """Get database URL, trying environment variable first, then building from components"""
        # Try direct URL first
        direct_url = os.getenv('DATABASE_URL')
        if direct_url and '@' in direct_url and direct_url.count('@') == 1:
            return direct_url
        
        # Build from components if direct URL has issues
        return DatabaseConfig.build_database_url()
