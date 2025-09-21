#!/usr/bin/env python3
"""
Direct test of NLP query processing without database dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.nlp_query_system import NLPQuerySystem
from services.improved_intent_classifier import reset_improved_classifier
from services.nlp_query_parser import reset_nlp_parser

def test_nlp_query():
    """Test NLP query processing directly."""
    
    # Reset global instances to pick up updated training examples
    reset_improved_classifier()
    reset_nlp_parser()
    
    # Initialize NLP system
    nlp_system = NLPQuerySystem()
    
    # Test query - specifically for SEARCH_LOGS intent
    query = "show me recent logs"
    
    print(f"Testing query: {query}")
    print("-" * 50)
    
    try:
        # Process the query (this will work without database for intent classification)
        result = nlp_system.process_query(query)
        
        print(f"Intent: {result.get('intent', 'unknown')}")
        print(f"Confidence: {result.get('confidence', 0.0):.3f}")
        print(f"Processing time: {result.get('processing_time_ms', 0)}ms")
        print(f"Entities: {result.get('entities', [])}")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        
    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nlp_query()