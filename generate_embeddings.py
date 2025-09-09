#!/usr/bin/env python3
"""
Standalone script to generate embeddings for existing ARGO profiles
"""
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.pipeline import ArgoETLPipeline

def main():
    """Generate embeddings for existing profiles"""
    try:
        print("🔧 Initializing ARGO ETL Pipeline for embedding generation...")
        pipeline = ArgoETLPipeline()
        
        # Check if embedding service is available
        if not pipeline.embedding_service.is_available():
            print("❌ Embedding service not available. Please check:")
            print("   1. GENAI_API_KEY is set in config/.env")
            print("   2. google-generativeai is installed: pip install google-generativeai")
            return 1
        
        print("✅ Embedding service is available")
        
        # Get current database stats
        db_stats = pipeline.get_database_stats()
        print(f"📊 Current database: {db_stats['total_profiles']} profiles")
        
        # Generate embeddings for profiles that don't have them
        batch_size = 10  # Process 10 profiles at a time
        results = pipeline.generate_embeddings_for_existing_profiles(batch_size)
        
        # Print results
        print("\n" + "="*50)
        print("EMBEDDING GENERATION RESULTS")
        print("="*50)
        print(f"Success: {'✓' if results['success'] else '✗'}")
        print(f"Profiles Processed: {results['profiles_processed']}")
        print(f"Embeddings Generated: {results['embeddings_generated']}")
        print(f"Duration: {results['duration']:.2f} seconds")
        
        if results['errors']:
            print(f"\nErrors: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        return 0 if results['success'] else 1
        
    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
