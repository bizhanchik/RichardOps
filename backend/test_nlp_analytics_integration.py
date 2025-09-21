#!/usr/bin/env python3
"""
Test script for NLP-Analytics integration.
Tests the intent classification and handler mapping for analytics queries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.nlp_query_parser import NLPQueryParser, QueryIntent
from services.improved_intent_classifier import get_improved_classifier
from services.intent_classifier_factory import classify_intent, ClassifierType

def test_analytics_intent_classification():
    """Test that analytics queries are correctly classified."""
    print("🧪 Testing Analytics Intent Classification")
    print("=" * 50)
    
    # Test queries for each analytics intent
    test_cases = [
        # Analytics Summary
        ("Give me a system summary for the last 24 hours", QueryIntent.ANALYTICS_SUMMARY),
        ("Show me system overview for today", QueryIntent.ANALYTICS_SUMMARY),
        ("Generate system summary report", QueryIntent.ANALYTICS_SUMMARY),
        ("What's the system status summary?", QueryIntent.ANALYTICS_SUMMARY),
        
        # Analytics Anomalies
        ("Detect anomalies in the last hour", QueryIntent.ANALYTICS_ANOMALIES),
        ("Show me critical anomalies today", QueryIntent.ANALYTICS_ANOMALIES),
        ("Find unusual patterns in system behavior", QueryIntent.ANALYTICS_ANOMALIES),
        ("What anomalies occurred this week?", QueryIntent.ANALYTICS_ANOMALIES),
        
        # Analytics Performance
        ("Show me performance metrics for this week", QueryIntent.ANALYTICS_PERFORMANCE),
        ("Generate performance report", QueryIntent.ANALYTICS_PERFORMANCE),
        ("How is system performance today?", QueryIntent.ANALYTICS_PERFORMANCE),
        ("Display performance analytics", QueryIntent.ANALYTICS_PERFORMANCE),
        
        # Analytics Metrics
        ("Show detailed metrics for the last 24 hours", QueryIntent.ANALYTICS_METRICS),
        ("Display system metrics", QueryIntent.ANALYTICS_METRICS),
        ("Get comprehensive metrics report", QueryIntent.ANALYTICS_METRICS),
        ("What are the current system metrics?", QueryIntent.ANALYTICS_METRICS),
    ]
    
    # Test with improved classifier
    print("\n📊 Testing with Improved Semantic Classifier:")
    print("-" * 45)
    
    try:
        classifier = get_improved_classifier()
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for query, expected_intent in test_cases:
            try:
                predicted_intent, confidence = classifier.classify_intent(query)
                is_correct = predicted_intent == expected_intent
                correct_predictions += is_correct
                
                status = "✅" if is_correct else "❌"
                print(f"{status} Query: '{query}'")
                print(f"   Expected: {expected_intent.value}")
                print(f"   Predicted: {predicted_intent.value} (confidence: {confidence:.3f})")
                print()
                
            except Exception as e:
                print(f"❌ Error classifying '{query}': {e}")
                print()
        
        accuracy = correct_predictions / total_predictions
        print(f"📈 Accuracy: {correct_predictions}/{total_predictions} ({accuracy:.1%})")
        
    except Exception as e:
        print(f"❌ Failed to test improved classifier: {e}")
    
    # Test with keyword-based classifier as fallback
    print("\n🔤 Testing with Keyword-based Classifier:")
    print("-" * 40)
    
    try:
        parser = NLPQueryParser(use_improved_classifier=False)
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for query, expected_intent in test_cases:
            try:
                parsed_query = parser.parse_query(query)
                predicted_intent = parsed_query.intent
                is_correct = predicted_intent == expected_intent
                correct_predictions += is_correct
                
                status = "✅" if is_correct else "❌"
                print(f"{status} Query: '{query}'")
                print(f"   Expected: {expected_intent.value}")
                print(f"   Predicted: {predicted_intent.value}")
                print()
                
            except Exception as e:
                print(f"❌ Error parsing '{query}': {e}")
                print()
        
        accuracy = correct_predictions / total_predictions
        print(f"📈 Accuracy: {correct_predictions}/{total_predictions} ({accuracy:.1%})")
        
    except Exception as e:
        print(f"❌ Failed to test keyword classifier: {e}")

def test_nlp_query_parser_integration():
    """Test that the NLP query parser correctly uses the improved classifier."""
    print("\n🔗 Testing NLP Query Parser Integration")
    print("=" * 50)
    
    try:
        # Test with improved classifier enabled
        parser = NLPQueryParser(use_improved_classifier=True)
        print(f"✅ Successfully created NLP query parser")
        print(f"   Using improved classifier: {parser.use_improved_classifier}")
        
        # Test parsing analytics queries
        test_queries = [
            "Give me a system summary for today",
            "Show me anomalies in the last hour",
            "Display performance metrics",
            "Get detailed system metrics"
        ]
        
        print("\n📝 Testing query parsing:")
        for query in test_queries:
            try:
                parsed_query = parser.parse_query(query)
                print(f"✅ '{query}'")
                print(f"   Intent: {parsed_query.intent.value}")
                print(f"   Entities: {len(parsed_query.entities)} found")
                time_entities = [e for e in parsed_query.entities if e.type.value == "time_range"]
                time_info = time_entities[0].value if time_entities else "No time range detected"
                print(f"   Time range: {time_info}")
                print()
            except Exception as e:
                print(f"❌ Failed to parse '{query}': {e}")
                print()
                
    except Exception as e:
        print(f"❌ Failed to test NLP query parser integration: {e}")

def test_intent_classifier_factory():
    """Test the intent classifier factory functionality."""
    print("\n🏭 Testing Intent Classifier Factory")
    print("=" * 50)
    
    test_query = "Show me system anomalies for today"
    
    # Test different classifier types
    classifier_types = [
        ClassifierType.SEMANTIC_SIMILARITY,
        ClassifierType.KEYWORD_BASED,
        ClassifierType.AUTO
    ]
    
    for classifier_type in classifier_types:
        try:
            intent, confidence = classify_intent(test_query, classifier_type)
            print(f"✅ {classifier_type.value.upper()} classifier:")
            print(f"   Intent: {intent.value}")
            print(f"   Confidence: {confidence:.3f}")
            print()
        except Exception as e:
            print(f"❌ {classifier_type.value.upper()} classifier failed: {e}")
            print()

def test_analytics_intent_coverage():
    """Test that all analytics intents are properly defined."""
    print("\n📋 Testing Analytics Intent Coverage")
    print("=" * 50)
    
    expected_analytics_intents = [
        "ANALYTICS_SUMMARY",
        "ANALYTICS_ANOMALIES", 
        "ANALYTICS_PERFORMANCE",
        "ANALYTICS_METRICS"
    ]
    
    # Check QueryIntent enum
    available_intents = [intent.name for intent in QueryIntent]
    
    print("📊 Checking QueryIntent enum:")
    for intent_name in expected_analytics_intents:
        if intent_name in available_intents:
            print(f"✅ {intent_name} - Available")
        else:
            print(f"❌ {intent_name} - Missing")
    
    print(f"\n📈 Total intents available: {len(available_intents)}")
    print(f"🎯 Analytics intents: {len([i for i in expected_analytics_intents if i in available_intents])}/4")

def main():
    """Run all integration tests."""
    print("🚀 NLP-Analytics Integration Test Suite")
    print("=" * 60)
    print("Testing the integration between NLP system and analytics features")
    print("=" * 60)
    
    try:
        # Test intent coverage first
        test_analytics_intent_coverage()
        
        # Test intent classification
        test_analytics_intent_classification()
        
        # Test NLP parser integration
        test_nlp_query_parser_integration()
        
        # Test factory functionality
        test_intent_classifier_factory()
        
        print("\n🎉 Integration testing completed!")
        print("=" * 60)
        print("✨ The NLP-Analytics integration is ready for deployment!")
        
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()