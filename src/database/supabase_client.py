"""
Supabase client setup for additional operations (optional)
This module provides a Supabase client for any additional operations
beyond the standard PostgreSQL connection used by SQLAlchemy
"""
import os
import logging
import sys
from typing import Optional

# Add config to path
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
sys.path.append(config_path)

from config import Config

logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase client not available. Install with: pip install supabase")

class SupabaseClient:
    """Optional Supabase client for additional operations"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        
        if SUPABASE_AVAILABLE and Config.SUPABASE_URL and Config.SUPABASE_KEY:
            try:
                self.client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
        else:
            logger.info("Supabase client not initialized (missing URL/KEY or library)")
    
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        if not self.is_available():
            return False
        
        try:
            # Try a simple query to test connection
            response = self.client.table('argo_floats').select("count", count='exact').limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
            return False
