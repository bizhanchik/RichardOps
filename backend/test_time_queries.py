#!/usr/bin/env python3
"""
Test script for time-based NLP queries.
This tests the integration of time-based functions with the NLP query system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set production database URL
os.environ["SYNC_DATABASE_URL"] = "postgresql://monitoring_user:monitoring_pass@159.89.104.120:5432/monitoring"

from database import get_sync_db_session
from services.nlp_query_translator import QueryTranslator
from services.nlp_query_parser import ParsedQuery, QueryIntent, EntityType

def create_mock_parsed_query(query_text: str) -> ParsedQuery:
    """Create a mock ParsedQuery for testing."""
    return ParsedQuery(
        original_query=query_text,
        intent=QueryIntent.SEARCH_LOGS,
        entities=[],
        structured_params={},
        confidence=1.0
    )

def test_time_based_queries():
    """Test time-based query patterns."""
    print("Testing Time-Based Query Integration")
    print("=" * 50)
    
    try:
        # Get database session
        db_session = get_sync_db_session()
        translator = QueryTranslator()
        
        # Test queries for latest logs
        latest_queries = [
            "show latest logs",
            "get recent logs", 
            "display latest 50",
            "most recent logs"
        ]
        
        print("\n1. Testing Latest Logs Queries:")
        for i, query in enumerate(latest_queries, 1):
            print(f"\n   1.{i} Query: '{query}'")
            parsed_query = create_mock_parsed_query(query)
            result = translator._handle_search_logs(parsed_query, db_session)
            
            if result.get('intent') == 'search_logs' and not result.get('error'):
                print(f"        Success: True")
                print(f"        Query Type: {result.get('query_info', {}).get('query_type', 'N/A')}")
                print(f"        Count: {result.get('count', 'N/A')}")
                print(f"        Results: {len(result.get('results', []))}")
            else:
                print(f"        Success: False")
                print(f"        Error: {result.get('error', 'Unknown error')}")
        
        # Test queries for last hour
        hour_queries = [
            "logs from last hour",
            "show logs from past hour",
            "get logs from previous hour",
            "logs in the last hour"
        ]
        
        print("\n2. Testing Last Hour Queries:")
        for i, query in enumerate(hour_queries, 1):
            print(f"\n   2.{i} Query: '{query}'")
            parsed_query = create_mock_parsed_query(query)
            result = translator._handle_search_logs(parsed_query, db_session)
            
            if result.get('intent') == 'search_logs' and not result.get('error'):
                print(f"        Success: True")
                print(f"        Query Type: {result.get('query_info', {}).get('query_type', 'N/A')}")
                print(f"        Count: {result.get('count', 'N/A')}")
                print(f"        Results: {len(result.get('results', []))}")
                if 'time_filter' in result.get('query_info', {}):
                    time_filter = result['query_info']['time_filter']
                    print(f"        Duration: {time_filter.get('duration', 'N/A')}")
            else:
                print(f"        Success: False")
                print(f"        Error: {result.get('error', 'Unknown error')}")
        
        # Test edge cases
        print("\n3. Testing Edge Cases:")
        edge_queries = [
            "show all logs",  # Should use fetch_all_logs, not time-based
            "latest error logs",  # Should use latest logs
            "recent nginx logs"  # Should use latest logs
        ]
        
        for i, query in enumerate(edge_queries, 1):
            print(f"\n   3.{i} Query: '{query}'")
            parsed_query = create_mock_parsed_query(query)
            result = translator._handle_search_logs(parsed_query, db_session)
            
            if result.get('intent') == 'search_logs' and not result.get('error'):
                print(f"        Success: True")
                print(f"        Query Type: {result.get('query_info', {}).get('query_type', 'N/A')}")
                print(f"        Count: {result.get('count', 'N/A')}")
                print(f"        Results: {len(result.get('results', []))}")
            else:
                print(f"        Success: False")
                print(f"        Error: {result.get('error', 'Unknown error')}")
        
        db_session.close()
        print(f"\n✅ Time-based query integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_time_based_queries()