#!/usr/bin/env python3
"""
Test script for analytics performance functionality.
Tests the fixed analytics_performance intent to ensure it returns meaningful data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.nlp_query_system import get_nlp_system
import json

def test_analytics_performance():
    """Test analytics performance queries."""
    print('Testing Analytics Performance Queries:')
    print('=' * 50)
    
    # Test analytics performance queries
    test_queries = [
        'Show me performance metrics for this week',
        'Generate performance report',
        'How is system performance today?',
        'Display performance analytics'
    ]

    nlp_system = get_nlp_system()

    for query in test_queries:
        print(f'\nQuery: "{query}"')
        try:
            result = nlp_system.process_query(query)
            print(f'Success: {result.get("success", False)}')
            print(f'Query Type: {result.get("query_type", "unknown")}')
            print(f'Message: {result.get("message", "No message")}')
            
            # Check if we have data
            data = result.get('data', {})
            if data:
                print(f'Data Status: {data.get("status", "unknown")}')
                if data.get('status') == 'success':
                    print('✅ Performance data returned successfully!')
                    # Show some details about the data
                    if 'performance_analysis' in data:
                        print('   - Performance analysis included')
                    if 'utilization_patterns' in data:
                        print('   - Utilization patterns included')
                    if 'recommendations' in data:
                        print('   - Recommendations included')
                elif data.get('status') == 'no_data':
                    print('⚠️  No performance data available (expected if no metrics in DB)')
                    print(f'   Message: {data.get("message", "No message")}')
                else:
                    print(f'❌ Unexpected status: {data.get("status")}')
                    if 'error' in data:
                        print(f'   Error: {data.get("error")}')
            else:
                print('❌ No data returned')
                
        except Exception as e:
            print(f'❌ Error: {str(e)}')
        
        print('-' * 30)

def test_analytics_summary():
    """Test analytics summary queries to compare."""
    print('\n\nTesting Analytics Summary Queries (for comparison):')
    print('=' * 60)
    
    test_queries = [
        'Give me a system summary for today',
        'Show me system overview'
    ]

    nlp_system = get_nlp_system()

    for query in test_queries:
        print(f'\nQuery: "{query}"')
        try:
            result = nlp_system.process_query(query)
            print(f'Success: {result.get("success", False)}')
            print(f'Query Type: {result.get("query_type", "unknown")}')
            print(f'Message: {result.get("message", "No message")}')
            
            # Check if we have data
            data = result.get('data', {})
            if data:
                print(f'Data Status: {data.get("status", "unknown")}')
                if data.get('status') == 'success':
                    print('✅ Summary data returned successfully!')
                elif data.get('status') == 'no_data':
                    print('⚠️  No summary data available')
                else:
                    print(f'❌ Unexpected status: {data.get("status")}')
            else:
                print('❌ No data returned')
                
        except Exception as e:
            print(f'❌ Error: {str(e)}')
        
        print('-' * 30)

if __name__ == "__main__":
    test_analytics_performance()
    test_analytics_summary()