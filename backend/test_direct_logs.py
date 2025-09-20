#!/usr/bin/env python3
"""
Direct test script for simple log fetching functions.
This bypasses the NLP system and directly calls the database functions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set production database URL
os.environ["SYNC_DATABASE_URL"] = "postgresql://monitoring_user:monitoring_pass@159.89.104.120:5432/monitoring"

from database import get_sync_db_session
from services.nlp_query_translator import QueryTranslator

def test_direct_log_functions():
    """Test the direct log fetching functions."""
    print("Testing direct log fetching functions...")
    
    # Get database session
    db_session = get_sync_db_session()
    
    try:
        # Initialize query translator
        translator = QueryTranslator()
        
        print("\n1. Testing fetch_all_logs()...")
        result = translator.fetch_all_logs(db_session, limit=10)
        print(f"   Result structure: {result}")
        if result.get('success'):
            print(f"   Success: True")
            if 'data' in result and 'total_count' in result['data']:
                print(f"   Count: {result['data']['total_count']}")
                print(f"   Logs returned: {len(result['data']['logs'])}")
            else:
                print(f"   Data structure: {result.get('data', 'No data key')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n2. Testing fetch_logs_by_message_pattern('ERROR')...")
        result = translator.fetch_logs_by_message_pattern(db_session, 'ERROR', limit=10)
        print(f"   Success: {result.get('success')}")
        if result.get('success') and 'data' in result:
            print(f"   Count: {result['data'].get('total_count', 'N/A')}")
            print(f"   Logs returned: {len(result['data'].get('logs', []))}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n3. Testing fetch_logs_by_message_pattern('INFO')...")
        result = translator.fetch_logs_by_message_pattern(db_session, 'INFO', limit=10)
        print(f"   Success: {result.get('success')}")
        if result.get('success') and 'data' in result:
            print(f"   Count: {result['data'].get('total_count', 'N/A')}")
            print(f"   Logs returned: {len(result['data'].get('logs', []))}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n4. Testing fetch_logs_by_container('webapp')...")
        result = translator.fetch_logs_by_container(db_session, 'webapp', limit=10)
        print(f"   Success: {result.get('success')}")
        if result.get('success') and 'data' in result:
            print(f"   Count: {result['data'].get('total_count', 'N/A')}")
            print(f"   Logs returned: {len(result['data'].get('logs', []))}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n5. Testing fetch_logs_by_container('nginx')...")
        result = translator.fetch_logs_by_container(db_session, 'nginx', limit=10)
        print(f"   Success: {result.get('success')}")
        if result.get('success') and 'data' in result:
            print(f"   Count: {result['data'].get('total_count', 'N/A')}")
            print(f"   Logs returned: {len(result['data'].get('logs', []))}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n6. Testing fetch_latest_logs() - Latest 50 logs...")
        result = translator.fetch_latest_logs(db_session, limit=50)
        print(f"   Success: {result.get('success')}")
        if result.get('success') and 'data' in result:
            print(f"   Count: {result['data'].get('total_count', 'N/A')}")
            print(f"   Logs returned: {len(result['data'].get('logs', []))}")
            print(f"   Limit: {result['data'].get('limit', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n7. Testing fetch_logs_last_hour() - Logs from past hour...")
        result = translator.fetch_logs_last_hour(db_session, limit=100)
        print(f"   Success: {result.get('success')}")
        if result.get('success') and 'data' in result:
            print(f"   Count: {result['data'].get('total_count', 'N/A')}")
            print(f"   Logs returned: {len(result['data'].get('logs', []))}")
            if 'time_filter' in result['data']:
                time_filter = result['data']['time_filter']
                print(f"   Time range: {time_filter.get('duration', 'N/A')}")
                print(f"   Start time: {time_filter.get('start_time', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Show sample log if available
        all_logs_result = translator.fetch_all_logs(db_session, limit=1)
        if all_logs_result.get('success') and all_logs_result.get('data', {}).get('logs'):
            sample_log = all_logs_result['data']['logs'][0]
            print(f"\n8. Sample log entry:")
            print(f"   Timestamp: {sample_log.get('timestamp', 'N/A')}")
            print(f"   Container: {sample_log.get('container', 'N/A')}")
            print(f"   Message: {sample_log.get('message', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_session.close()

if __name__ == "__main__":
    test_direct_log_functions()