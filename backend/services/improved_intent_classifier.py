"""
Improved Intent Classification System using Sentence Transformers.

This module provides a more accurate intent classification system that uses
semantic similarity instead of simple keyword matching.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os
from sklearn.metrics.pairwise import cosine_similarity

# Define QueryIntent enum locally to avoid circular import
from enum import Enum

class QueryIntent(Enum):
    """Types of query intents the system can handle."""
    SEARCH_LOGS = "search_logs"
    GENERATE_REPORT = "generate_report"
    INVESTIGATE = "investigate"
    SHOW_ALERTS = "show_alerts"
    ANALYZE_TRENDS = "analyze_trends"
    ANALYTICS_SUMMARY = "analytics_summary"
    ANALYTICS_ANOMALIES = "analytics_anomalies"
    ANALYTICS_PERFORMANCE = "analytics_performance"
    ANALYTICS_METRICS = "analytics_metrics"
    UNKNOWN = "unknown"


@dataclass
class IntentExample:
    """Example query for training intent classification."""
    text: str
    intent: QueryIntent
    confidence: float = 1.0


class ImprovedIntentClassifier:
    """
    Advanced intent classifier using sentence transformers and semantic similarity.
    
    This classifier uses pre-computed embeddings of example queries to classify
    new queries based on semantic similarity rather than keyword matching.
    """
    
    def __init__(self):
        """Initialize the improved intent classifier."""
        self.intent_examples = self._build_intent_examples()
        self.example_embeddings = None
        self.embedding_model = None
        self._initialize_embeddings()
    
    def _build_intent_examples(self) -> List[IntentExample]:
        """Build comprehensive examples for each intent type."""
        examples = [
            # SEARCH_LOGS examples
            IntentExample("show me the latest logs", QueryIntent.SEARCH_LOGS),
            IntentExample("get container logs for nginx", QueryIntent.SEARCH_LOGS),
            IntentExample("find error logs from yesterday", QueryIntent.SEARCH_LOGS),
            IntentExample("display recent log entries", QueryIntent.SEARCH_LOGS),
            IntentExample("fetch logs containing 'database connection'", QueryIntent.SEARCH_LOGS),
            IntentExample("show all logs from the api container", QueryIntent.SEARCH_LOGS),
            IntentExample("get debug logs for the last hour", QueryIntent.SEARCH_LOGS),
            IntentExample("list application logs", QueryIntent.SEARCH_LOGS),
            IntentExample("retrieve system logs", QueryIntent.SEARCH_LOGS),
            IntentExample("show me what happened in the logs", QueryIntent.SEARCH_LOGS),
            
            # GENERATE_REPORT examples
            IntentExample("generate a security report", QueryIntent.GENERATE_REPORT),
            IntentExample("create a summary of today's events", QueryIntent.GENERATE_REPORT),
            IntentExample("build a performance report", QueryIntent.GENERATE_REPORT),
            IntentExample("produce an incident summary", QueryIntent.GENERATE_REPORT),
            IntentExample("make a daily digest", QueryIntent.GENERATE_REPORT),
            IntentExample("compile system statistics", QueryIntent.GENERATE_REPORT),
            IntentExample("export usage analytics", QueryIntent.GENERATE_REPORT),
            IntentExample("create a monthly overview", QueryIntent.GENERATE_REPORT),
            IntentExample("generate metrics dashboard", QueryIntent.GENERATE_REPORT),
            IntentExample("build error rate analysis", QueryIntent.GENERATE_REPORT),
            
            # INVESTIGATE examples
            IntentExample("investigate this IP address: 192.168.1.100", QueryIntent.INVESTIGATE),
            IntentExample("what caused the system failure?", QueryIntent.INVESTIGATE),
            IntentExample("analyze suspicious activity", QueryIntent.INVESTIGATE),
            IntentExample("trace the root cause of errors", QueryIntent.INVESTIGATE),
            IntentExample("examine container crashes", QueryIntent.INVESTIGATE),
            IntentExample("debug the authentication issues", QueryIntent.INVESTIGATE),
            IntentExample("why is the API responding slowly?", QueryIntent.INVESTIGATE),
            IntentExample("investigate security breach", QueryIntent.INVESTIGATE),
            IntentExample("find out what happened to user sessions", QueryIntent.INVESTIGATE),
            IntentExample("troubleshoot database connectivity", QueryIntent.INVESTIGATE),
            
            # SHOW_ALERTS examples
            IntentExample("show me current alerts", QueryIntent.SHOW_ALERTS),
            IntentExample("display critical notifications", QueryIntent.SHOW_ALERTS),
            IntentExample("get urgent warnings", QueryIntent.SHOW_ALERTS),
            IntentExample("list active incidents", QueryIntent.SHOW_ALERTS),
            IntentExample("show security alerts", QueryIntent.SHOW_ALERTS),
            IntentExample("display system alarms", QueryIntent.SHOW_ALERTS),
            IntentExample("get high priority issues", QueryIntent.SHOW_ALERTS),
            IntentExample("show me what's broken", QueryIntent.SHOW_ALERTS),
            IntentExample("list failed services", QueryIntent.SHOW_ALERTS),
            IntentExample("display error notifications", QueryIntent.SHOW_ALERTS),
            
            # ANALYZE_TRENDS examples
            IntentExample("analyze traffic trends over time", QueryIntent.ANALYZE_TRENDS),
            IntentExample("show performance patterns", QueryIntent.ANALYZE_TRENDS),
            IntentExample("compare this week vs last week", QueryIntent.ANALYZE_TRENDS),
            IntentExample("track error rate changes", QueryIntent.ANALYZE_TRENDS),
            IntentExample("analyze user behavior trends", QueryIntent.ANALYZE_TRENDS),
            IntentExample("show historical metrics", QueryIntent.ANALYZE_TRENDS),
            IntentExample("compare system performance", QueryIntent.ANALYZE_TRENDS),
            IntentExample("track resource usage over time", QueryIntent.ANALYZE_TRENDS),
            IntentExample("analyze growth patterns", QueryIntent.ANALYZE_TRENDS),
            IntentExample("show usage statistics trends", QueryIntent.ANALYZE_TRENDS),
            
            # ANALYTICS_SUMMARY examples
            IntentExample("give me a system summary", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("show me an overview of the system", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("generate a summary report", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("what's the current system status summary", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("provide a comprehensive overview", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("show me the daily summary", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("give me a quick system overview", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("summarize system activity", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("show me the weekly summary", QueryIntent.ANALYTICS_SUMMARY),
            IntentExample("provide system analytics summary", QueryIntent.ANALYTICS_SUMMARY),
            
            # ANALYTICS_ANOMALIES examples
            IntentExample("detect anomalies in the system", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("show me any unusual activity", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("find anomalies in the data", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("are there any anomalies detected", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("show me suspicious patterns", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("detect unusual behavior", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("find outliers in the metrics", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("show me abnormal activity", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("detect system anomalies", QueryIntent.ANALYTICS_ANOMALIES),
            IntentExample("find irregular patterns", QueryIntent.ANALYTICS_ANOMALIES),
            
            # ANALYTICS_PERFORMANCE examples
            IntentExample("show me performance metrics", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("how is the system performing", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("generate a performance report", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("show me system performance data", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("analyze system performance", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("what's the performance status", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("show me performance analytics", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("display performance statistics", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("get performance insights", QueryIntent.ANALYTICS_PERFORMANCE),
            IntentExample("show me resource utilization", QueryIntent.ANALYTICS_PERFORMANCE),
            
            # ANALYTICS_METRICS examples
            IntentExample("show me system metrics", QueryIntent.ANALYTICS_METRICS),
            IntentExample("display key metrics", QueryIntent.ANALYTICS_METRICS),
            IntentExample("get metric data", QueryIntent.ANALYTICS_METRICS),
            IntentExample("show me the latest metrics", QueryIntent.ANALYTICS_METRICS),
            IntentExample("display analytics metrics", QueryIntent.ANALYTICS_METRICS),
            IntentExample("show me metric trends", QueryIntent.ANALYTICS_METRICS),
            IntentExample("get system measurements", QueryIntent.ANALYTICS_METRICS),
            IntentExample("show me operational metrics", QueryIntent.ANALYTICS_METRICS),
            IntentExample("display metric dashboard", QueryIntent.ANALYTICS_METRICS),
            IntentExample("show me metric analysis", QueryIntent.ANALYTICS_METRICS),
        ]
        
        return examples
    
    def _initialize_embeddings(self):
        """Initialize embeddings for example queries."""
        try:
            # Try to use sentence-transformers if available
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Compute embeddings for all examples
            example_texts = [example.text for example in self.intent_examples]
            self.example_embeddings = self.embedding_model.encode(example_texts)
            
        except ImportError:
            # Fallback to mock embeddings if sentence-transformers not available
            print("Warning: sentence-transformers not available, using mock embeddings")
            self.embedding_model = None
            self.example_embeddings = self._generate_mock_embeddings()
    
    def _generate_mock_embeddings(self) -> np.ndarray:
        """Generate mock embeddings for testing when sentence-transformers is not available."""
        # Create deterministic mock embeddings based on text hash
        embeddings = []
        for example in self.intent_examples:
            # Use hash of text to create deterministic embedding
            text_hash = hash(example.text)
            np.random.seed(abs(text_hash) % (2**32))
            embedding = np.random.normal(0, 1, 384)  # 384 dimensions like MiniLM
            embedding = embedding / np.linalg.norm(embedding)  # Normalize
            embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def classify_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """
        Classify the intent of a query using semantic similarity.
        
        Args:
            query: The input query string
            
        Returns:
            Tuple of (predicted_intent, confidence_score)
        """
        if self.embedding_model is not None:
            # Use real sentence transformer
            query_embedding = self.embedding_model.encode([query])
        else:
            # Use mock embedding
            text_hash = hash(query)
            np.random.seed(abs(text_hash) % (2**32))
            query_embedding = np.random.normal(0, 1, (1, 384))
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Compute similarities with all examples
        similarities = cosine_similarity(query_embedding, self.example_embeddings)[0]
        
        # Find the best matching example
        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]
        best_intent = self.intent_examples[best_match_idx].intent
        
        # Apply confidence threshold
        if best_similarity < 0.3:  # Low similarity threshold
            return QueryIntent.UNKNOWN, best_similarity
        
        # Calculate intent-level confidence by averaging top matches for each intent
        intent_scores = {}
        for intent in QueryIntent:
            if intent == QueryIntent.UNKNOWN:
                continue
            
            # Get similarities for this intent
            intent_similarities = [
                similarities[i] for i, example in enumerate(self.intent_examples)
                if example.intent == intent
            ]
            
            if intent_similarities:
                # Use the maximum similarity for this intent
                intent_scores[intent] = max(intent_similarities)
        
        if not intent_scores:
            return QueryIntent.UNKNOWN, 0.0
        
        # Return the intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        return best_intent, confidence
    
    def get_intent_examples(self, intent: QueryIntent) -> List[str]:
        """Get example queries for a specific intent."""
        return [
            example.text for example in self.intent_examples
            if example.intent == intent
        ]
    
    def add_training_example(self, text: str, intent: QueryIntent, confidence: float = 1.0):
        """Add a new training example and recompute embeddings."""
        new_example = IntentExample(text, intent, confidence)
        self.intent_examples.append(new_example)
        
        # Recompute embeddings
        self._initialize_embeddings()
    
    def evaluate_on_test_queries(self, test_queries: List[Tuple[str, QueryIntent]]) -> Dict[str, float]:
        """Evaluate the classifier on test queries."""
        correct = 0
        total = len(test_queries)
        
        intent_stats = {}
        for intent in QueryIntent:
            intent_stats[intent.value] = {"correct": 0, "total": 0, "precision": 0, "recall": 0}
        
        for query, true_intent in test_queries:
            predicted_intent, confidence = self.classify_intent(query)
            
            intent_stats[true_intent.value]["total"] += 1
            
            if predicted_intent == true_intent:
                correct += 1
                intent_stats[true_intent.value]["correct"] += 1
        
        # Calculate metrics
        accuracy = correct / total if total > 0 else 0
        
        for intent_name, stats in intent_stats.items():
            if stats["total"] > 0:
                stats["recall"] = stats["correct"] / stats["total"]
        
        return {
            "accuracy": accuracy,
            "total_queries": total,
            "correct_predictions": correct,
            "intent_breakdown": intent_stats
        }


# Global instance
_improved_classifier = None

def get_improved_classifier() -> ImprovedIntentClassifier:
    """Get the global improved intent classifier instance."""
    global _improved_classifier
    if _improved_classifier is None:
        _improved_classifier = ImprovedIntentClassifier()
    return _improved_classifier


def classify_query_intent(query: str) -> Tuple[QueryIntent, float]:
    """Classify query intent using the improved classifier."""
    classifier = get_improved_classifier()
    return classifier.classify_intent(query)


if __name__ == "__main__":
    # Test the classifier
    classifier = ImprovedIntentClassifier()
    
    test_queries = [
        "show me recent logs",
        "generate a security report", 
        "what caused this error?",
        "display current alerts",
        "analyze performance trends"
    ]
    
    print("Testing Improved Intent Classifier:")
    print("=" * 50)
    
    for query in test_queries:
        intent, confidence = classifier.classify_intent(query)
        print(f"Query: '{query}'")
        print(f"Intent: {intent.value}, Confidence: {confidence:.3f}")
        print("-" * 30)