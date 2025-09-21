#!/usr/bin/env python3
"""
Test script to check if there's data in the database tables.
"""

from database import get_sync_db_session
from db_models import ContainerLogsModel, DockerEventsModel, AlertsModel, MetricsModel

def check_database_data():
    """Check if there's data in the main database tables."""
    db_session = get_sync_db_session()
    
    try:
        # Check each table for data
        tables_to_check = [
            ("container_logs", ContainerLogsModel),
            ("docker_events", DockerEventsModel),
            ("alerts", AlertsModel),
            ("metrics", MetricsModel)
        ]
        
        print("Checking database tables for data...")
        print("=" * 50)
        
        total_records = 0
        for table_name, model in tables_to_check:
            try:
                count = db_session.query(model).count()
                print(f"{table_name}: {count} records")
                total_records += count
                
                # Show a sample record if available
                if count > 0:
                    sample = db_session.query(model).first()
                    print(f"  Sample record: {sample.id if hasattr(sample, 'id') else 'N/A'}")
                    if hasattr(sample, 'timestamp'):
                        print(f"  Latest timestamp: {sample.timestamp}")
                    print()
                    
            except Exception as e:
                print(f"{table_name}: ERROR - {str(e)}")
        
        print("=" * 50)
        print(f"Total records across all tables: {total_records}")
        
        if total_records == 0:
            print("\n⚠️  WARNING: No data found in any tables!")
            print("This explains why search queries return 0 results.")
        else:
            print(f"\n✅ Found {total_records} total records in database.")
            
    except Exception as e:
        print(f"Database connection error: {str(e)}")
    finally:
        db_session.close()

if __name__ == "__main__":
    check_database_data()