#!/usr/bin/env python3
"""
Main execution script for ARGO ETL Pipeline
"""
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.pipeline import ArgoETLPipeline

def main():
    """Main execution function"""
    try:
        # Initialize pipeline
        pipeline = ArgoETLPipeline()
        
        # Run the pipeline
        results = pipeline.run_pipeline()
        
        # Get database statistics
        db_stats = pipeline.get_database_stats()
        
        # Print results
        print("\n" + "="*50)
        print("ARGO ETL PIPELINE RESULTS")
        print("="*50)
        print(f"Success: {'✓' if results['success'] else '✗'}")
        print(f"Files Downloaded: {results['files_downloaded']}")
        print(f"Files Parsed: {results['files_parsed']}")
        print(f"Records Stored: {results['records_stored']}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"\nDatabase Statistics:")
        print(f"Total Floats: {db_stats['total_floats']}")
        print(f"Total Profiles: {db_stats['total_profiles']}")
        
        if results['errors']:
            print(f"\nErrors: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        return 0 if results['success'] else 1
        
    except Exception as e:
        print(f"Application error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
