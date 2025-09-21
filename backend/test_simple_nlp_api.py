#!/usr/bin/env python3
"""
Test script for the Simple NLP API endpoints

This script tests the updated NLP API endpoints that now use
direct message mapping instead of intent classification.
"""

import requests
import json
import time
from typing import Dict, Any


def test_nlp_endpoint(base_url: str = "http://localhost:8000") -> None:
    """Test the NLP API endpoints."""
    
    print("Testing Simple NLP API Endpoints")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "show me recent logs",
        "get latest logs", 
        "show alerts",
        "system summary",
        "error logs from last hour",
        "container logs for web-server",
        "invalid query that should fail"
    ]
    
    # Test /api/nlp/query endpoint
    print("\n1. Testing /api/nlp/query endpoint:")
    print("-" * 40)
    
    for query in test_queries:
        try:
            response = requests.post(
                f"{base_url}/api/nlp/query",
                json={"query": query},
                timeout=10
            )
            
            print(f"\nQuery: '{query}'")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success', False)}")
                
                if data.get('success'):
                    result = data.get('result', {})
                    print(f"Function Used: {result.get('function_used', 'none')}")
                    print(f"Processing Time: {data.get('processing_time_ms', 0):.2f}ms")
                    
                    if result.get('error'):
                        print(f"Function Error: {result['error']}")
                    else:
                        print(f"Results Count: {result.get('count', 0)}")
                else:
                    print(f"API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"HTTP Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
    
    # Test /api/nlp/suggestions endpoint
    print("\n\n2. Testing /api/nlp/suggestions endpoint:")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/nlp/suggestions", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success'):
                suggestions = data.get('suggestions', [])
                print(f"Suggestions Count: {len(suggestions)}")
                print("Sample Suggestions:")
                for suggestion in suggestions[:5]:
                    print(f"  - {suggestion}")
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    # Test /api/nlp/status endpoint
    print("\n\n3. Testing /api/nlp/status endpoint:")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/nlp/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success'):
                status = data.get('status', {})
                print(f"System Status: {status.get('status', 'unknown')}")
                print(f"Database Connected: {status.get('database_connected', False)}")
                print(f"Available Functions: {status.get('available_functions', 0)}")
                print(f"Cache Size: {status.get('cache_size', 0)}")
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    # Test /api/nlp/examples endpoint
    print("\n\n4. Testing /api/nlp/examples endpoint:")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/nlp/examples", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success'):
                examples = data.get('examples', {})
                print(f"Example Categories: {len(examples)}")
                for category, queries in examples.items():
                    print(f"  {category}: {len(queries)} examples")
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("API Testing Complete!")


if __name__ == "__main__":
    # Test with default localhost
    test_nlp_endpoint()
    
    print("\nNote: Database connection errors are expected if PostgreSQL is not running.")
    print("The important thing is that message mapping works correctly!")