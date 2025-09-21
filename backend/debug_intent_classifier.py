#!/usr/bin/env python3
"""
Debug script for intent classifier
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.improved_intent_classifier import ImprovedIntentClassifier, QueryIntent

def test_intent_classifier():
    """Test the intent classifier with detailed debugging."""
    print("🔍 Testing Intent Classifier")
    print("=" * 50)
    
    # Initialize classifier
    print("Initializing classifier...")
    classifier = ImprovedIntentClassifier()
    
    # Check if embeddings were initialized
    print(f"Embedding model: {type(classifier.embedding_model)}")
    print(f"Example embeddings shape: {classifier.example_embeddings.shape if classifier.example_embeddings is not None else 'None'}")
    print(f"Number of intent examples: {len(classifier.intent_examples)}")
    
    # Show some examples
    print("\nFirst 10 training examples:")
    for i, example in enumerate(classifier.intent_examples[:10]):
        print(f"  {i+1}. '{example.text}' -> {example.intent}")
    
    # Test the specific query
    test_query = "Show recent error logs and stack traces"
    print(f"\nTesting query: '{test_query}'")
    print("-" * 50)
    
    # Get classification result
    intent, confidence = classifier.classify_intent(test_query)
    
    print(f"Intent: {intent}")
    print(f"Confidence: {confidence:.3f}")
    
    # Check if the query matches any training examples exactly
    print("\nChecking for exact matches in training examples:")
    for example in classifier.intent_examples:
        if test_query.lower() in example.text.lower() or example.text.lower() in test_query.lower():
            print(f"  Similar: '{example.text}' -> {example.intent}")
    
    # Test a few more queries
    test_queries = [
        "show me recent logs",
        "display error logs",
        "get stack traces",
        "show recent error logs and stack traces"
    ]
    
    print(f"\nTesting multiple queries:")
    print("-" * 50)
    for query in test_queries:
        intent, confidence = classifier.classify_intent(query)
        print(f"'{query}' -> {intent} (confidence: {confidence:.3f})")

if __name__ == "__main__":
    test_intent_classifier()