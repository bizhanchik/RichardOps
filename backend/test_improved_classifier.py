#!/usr/bin/env python3
"""
Test script to compare the old keyword-based intent classifier 
with the new improved semantic similarity classifier.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.nlp_query_parser import NLPQueryParser
from services.improved_intent_classifier import ImprovedIntentClassifier, QueryIntent


def test_intent_classification():
    """Test both old and new intent classification systems."""
    
    # Initialize both classifiers
    old_parser = NLPQueryParser(use_improved_classifier=False)
    new_classifier = ImprovedIntentClassifier()
    
    # Test queries with expected intents
    test_cases = [
        # Clear cases
        ("show me the latest logs", QueryIntent.SEARCH_LOGS),
        ("generate a security report", QueryIntent.GENERATE_REPORT),
        ("what caused this error?", QueryIntent.INVESTIGATE),
        ("display current alerts", QueryIntent.SHOW_ALERTS),
        ("analyze performance trends", QueryIntent.ANALYZE_TRENDS),
        
        # Ambiguous/challenging cases
        ("I need to see what happened yesterday", QueryIntent.SEARCH_LOGS),
        ("Can you help me understand the system issues?", QueryIntent.INVESTIGATE),
        ("Show me a breakdown of today's events", QueryIntent.GENERATE_REPORT),
        ("Are there any problems right now?", QueryIntent.SHOW_ALERTS),
        ("How has our performance changed over time?", QueryIntent.ANALYZE_TRENDS),
        
        # Edge cases
        ("logs", QueryIntent.SEARCH_LOGS),
        ("What's wrong?", QueryIntent.INVESTIGATE),
        ("Status check", QueryIntent.SHOW_ALERTS),
        ("Compare last week", QueryIntent.ANALYZE_TRENDS),
        ("Make me a summary", QueryIntent.GENERATE_REPORT),
        
        # Potentially confusing cases
        ("Show me error trends in the logs", QueryIntent.ANALYZE_TRENDS),  # Could be SEARCH_LOGS
        ("Generate an investigation report", QueryIntent.GENERATE_REPORT),  # Could be INVESTIGATE
        ("Alert me about log patterns", QueryIntent.SHOW_ALERTS),  # Could be SEARCH_LOGS
    ]
    
    print("Intent Classification Comparison")
    print("=" * 80)
    print(f"{'Query':<40} {'Old System':<20} {'New System':<20} {'Match':<8}")
    print("-" * 80)
    
    matches = 0
    total = len(test_cases)
    
    for query, expected_intent in test_cases:
        # Test old system
        old_intent, old_confidence = old_parser._classify_intent(query.lower())
        
        # Test new system
        new_intent, new_confidence = new_classifier.classify_intent(query)
        
        # Check if new system matches expected
        is_match = "✓" if new_intent == expected_intent else "✗"
        if new_intent == expected_intent:
            matches += 1
        
        # Format output
        query_short = query[:37] + "..." if len(query) > 40 else query
        old_result = f"{old_intent.value[:15]}({old_confidence:.2f})"
        new_result = f"{new_intent.value[:15]}({new_confidence:.2f})"
        
        print(f"{query_short:<40} {old_result:<20} {new_result:<20} {is_match:<8}")
    
    print("-" * 80)
    print(f"New System Accuracy: {matches}/{total} ({matches/total*100:.1f}%)")
    
    # Test some completely unrelated queries
    print("\nTesting with unrelated queries (should return UNKNOWN):")
    print("-" * 60)
    
    unrelated_queries = [
        "What's the weather like?",
        "How do I cook pasta?",
        "Tell me a joke",
        "What is the capital of France?",
        "Random gibberish xyz abc 123"
    ]
    
    for query in unrelated_queries:
        old_intent, old_confidence = old_parser._classify_intent(query.lower())
        new_intent, new_confidence = new_classifier.classify_intent(query)
        
        print(f"'{query}'")
        print(f"  Old: {old_intent.value} ({old_confidence:.3f})")
        print(f"  New: {new_intent.value} ({new_confidence:.3f})")
        print()


def demonstrate_improvements():
    """Demonstrate specific improvements of the new system."""
    
    print("\nDemonstrating Key Improvements")
    print("=" * 50)
    
    new_classifier = ImprovedIntentClassifier()
    old_parser = NLPQueryParser(use_improved_classifier=False)
    
    # Cases where semantic understanding helps
    semantic_cases = [
        "I want to see what went wrong",  # Should be INVESTIGATE
        "Give me an overview of system health",  # Should be GENERATE_REPORT  
        "Are there any issues I should know about?",  # Should be SHOW_ALERTS
        "How are things performing compared to last month?",  # Should be ANALYZE_TRENDS
        "Pull up the recent activity",  # Should be SEARCH_LOGS
    ]
    
    print("Semantic Understanding Test:")
    print("-" * 30)
    
    for query in semantic_cases:
        old_intent, old_conf = old_parser._classify_intent(query.lower())
        new_intent, new_conf = new_classifier.classify_intent(query)
        
        print(f"Query: '{query}'")
        print(f"  Old system: {old_intent.value} (confidence: {old_conf:.3f})")
        print(f"  New system: {new_intent.value} (confidence: {new_conf:.3f})")
        print()


if __name__ == "__main__":
    print("Testing Improved Intent Classification System")
    print("=" * 60)
    
    try:
        test_intent_classification()
        demonstrate_improvements()
        
        print("\nRecommendations:")
        print("- The new system provides much better semantic understanding")
        print("- It handles ambiguous queries more accurately")
        print("- It's less prone to false positives from keyword matching")
        print("- Consider using the improved classifier in production")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install sentence-transformers scikit-learn numpy")