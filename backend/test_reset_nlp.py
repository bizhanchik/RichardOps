#!/usr/bin/env python3
"""
Test script to reset NLP cache and test the improved classifier.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.improved_intent_classifier import reset_improved_classifier, get_improved_classifier
from services.nlp_query_parser import reset_nlp_parser, parse_natural_query

def test_reset_and_classify():
    """Test resetting the NLP cache and classifying a query."""
    
    print("=== Testing NLP Cache Reset ===")
    
    # Reset the caches
    print("1. Resetting improved classifier cache...")
    reset_improved_classifier()
    
    print("2. Resetting NLP parser cache...")
    reset_nlp_parser()
    
    print("3. Testing query classification after reset...")
    
    # Test query
    test_query = "Show recent error logs and stack traces"
    
    # Test with improved classifier directly
    print(f"\n--- Direct Classifier Test ---")
    classifier = get_improved_classifier()
    intent, confidence = classifier.classify_intent(test_query)
    print(f"Query: {test_query}")
    print(f"Intent: {intent}")
    print(f"Confidence: {confidence:.3f}")
    
    # Test with full NLP parser
    print(f"\n--- Full NLP Parser Test ---")
    parsed_query = parse_natural_query(test_query)
    print(f"Query: {test_query}")
    print(f"Intent: {parsed_query.intent}")
    print(f"Confidence: {parsed_query.confidence:.3f}")
    print(f"Entities: {parsed_query.entities}")
    
    print("\n=== Reset and Classification Test Complete ===")

if __name__ == "__main__":
    test_reset_and_classify()