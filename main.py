#!/usr/bin/env python3
"""
Main execution script for ARGO ETL Pipeline with Normalized Schema
"""
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.pipeline import ArgoETLPipeline

def main():
    """Main execution function"""
    try:
        # Initialize pipeline with new normalized schema
        pipeline = ArgoETLPipeline()
        
        # Run the pipeline with a small batch for testing
        results = pipeline.run_pipeline(max_files=3)
        
        # Get database statistics (now includes measurements!)
        db_stats = pipeline.get_database_stats()
        
        # Print results
        print("\n" + "="*50)
        print("ARGO ETL PIPELINE RESULTS (NORMALIZED SCHEMA)")
        print("="*50)
        print(f"Success: {'✓' if results['success'] else '✗'}")
        print(f"Files Downloaded: {results['files_downloaded']}")
        print(f"Files Parsed: {results['files_parsed']}")
        print(f"Profiles Stored: {results.get('profiles_stored', 0)}")
        print(f"Measurements Stored: {results.get('measurements_stored', 0)}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"\nDatabase Statistics:")
        print(f"Total Floats: {db_stats['total_floats']}")
        print(f"Total Profiles: {db_stats['total_profiles']}")
        print(f"Total Measurements: {db_stats.get('total_measurements', 0)}")
        
        if results['errors']:
            print(f"\nErrors: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        # Demonstrate new analytical capabilities
        print(f"\n🔬 RUNNING ANALYTICAL DEMO...")
        pipeline.demonstrate_analytical_capabilities()
        
        return 0 if results['success'] else 1
        
    except Exception as e:
        print(f"Application error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
