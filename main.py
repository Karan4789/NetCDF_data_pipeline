#!/usr/bin/env python3
"""
ARGO ETL Pipeline with Pathway Poll Integration
"""

import sys
import os
import pathway as pw
from datetime import datetime, timezone
import time

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.pipeline import ArgoETLPipeline

class ETLResultSchema(pw.Schema):
    timestamp: str
    success: bool
    files_downloaded: int
    files_parsed: int
    records_stored: int
    duration: float
    errors: str
    total_floats: int
    total_profiles: int

class PollSubject(pw.io.python.ConnectorSubject):
    def run(self):
        while True:
            result = run_etl_once()[0]
            self.next(**result)
            time.sleep(30)  # Poll every 30 seconds

def run_etl_once():
    """Run the ETL pipeline once and return a dict."""
    try:
        pipeline = ArgoETLPipeline()
        results = pipeline.run_pipeline()
        db_stats = pipeline.get_database_stats()
        return [{
            "timestamp": datetime.utcnow().isoformat(),
            "success": results["success"],
            "files_downloaded": results["files_downloaded"],
            "files_parsed": results["files_parsed"],
            "records_stored": results["records_stored"],
            "duration": results["duration"],
            "errors": "; ".join(results["errors"]) if results["errors"] else "",
            "total_floats": db_stats.get("total_floats", 0),
            "total_profiles": db_stats.get("total_profiles", 0)
        }]
    except Exception as e:
        return [{
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "files_downloaded": 0,
            "files_parsed": 0,
            "records_stored": 0,
            "duration": 0.0,
            "errors": str(e),
            "total_floats": 0,
            "total_profiles": 0
        }]

def main():
    poll_subject = PollSubject()
    poll_table = pw.io.python.read(poll_subject, schema=ETLResultSchema)

    def on_change(key, row, time, is_addition):
        print("ETL Run ->", row)

    pw.io.subscribe(poll_table, on_change)
    pw.run()

if __name__ == "__main__":
    main()
