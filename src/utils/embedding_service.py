"""
Embedding service for ARGO profile data using Google Gemini
"""
import logging
import sys
import os
from typing import List, Optional, Dict, Any

# Add config to path
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
sys.path.append(config_path)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from config import Config

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Handles embedding generation for ARGO profile data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GENAI_API_KEY')
        self.embedding_model = "models/embedding-001"
        
        if not GENAI_AVAILABLE:
            logger.warning("Google GenerativeAI not available. Install with: pip install google-generativeai")
            return
            
        if not self.api_key:
            logger.warning("GENAI_API_KEY not found in environment variables")
            return
            
        try:
            genai.configure(api_key=self.api_key)
            logger.info("Google GenerativeAI configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Google GenerativeAI: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if embedding service is available"""
        return GENAI_AVAILABLE and self.api_key is not None
    
    def create_profile_summary(self, profile_data: Dict[str, Any]) -> str:
        """
        Create a text summary of the ARGO profile for embedding
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Text summary of the profile
        """
        try:
            summary = f"""
            ARGO float profile measurement:
            Location: Latitude {profile_data.get('latitude', 'N/A')}, Longitude {profile_data.get('longitude', 'N/A')}
            Time: {profile_data.get('measurement_time', 'N/A')}
            Measurements: {profile_data.get('num_measurements', 0)} data points
            Temperature profile: {profile_data.get('temperature', 'N/A')}
            Salinity profile: {profile_data.get('salinity', 'N/A')}
            Pressure range: {profile_data.get('pressure', 'N/A')}
            Platform: {profile_data.get('platform_number', 'N/A')}
            Cycle: {profile_data.get('cycle_number', 'N/A')}
            """
            return summary.strip()
        except Exception as e:
            logger.error(f"Error creating profile summary: {str(e)}")
            return ""
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for given text using Gemini
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of float values representing the embedding, or None if failed
        """
        if not self.is_available():
            logger.warning("Embedding service not available")
            return None
            
        try:
            response = genai.embed_content(
                model=self.embedding_model,
                content=text
            )
            embedding = response["embedding"]
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_profile_embedding(self, profile_data: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for ARGO profile data
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            summary = self.create_profile_summary(profile_data)
            if not summary:
                return None
                
            embedding = self.generate_embedding(summary)
            if embedding:
                logger.info(f"Generated embedding for platform {profile_data.get('platform_number')}, cycle {profile_data.get('cycle_number')}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating profile embedding: {str(e)}")
            return None
