"""
Intent Classifier Factory

This module provides a factory pattern to easily switch between
the old keyword-based classifier and the new improved semantic classifier.
"""

from typing import Tuple, Optional
from enum import Enum


class ClassifierType(Enum):
    """Available classifier types."""
    KEYWORD_BASED = "keyword"
    SEMANTIC_SIMILARITY = "semantic"
    AUTO = "auto"  # Automatically choose the best available


class IntentClassifierFactory:
    """Factory for creating intent classifiers."""
    
    @staticmethod
    def create_classifier(classifier_type: ClassifierType = ClassifierType.SEMANTIC_SIMILARITY):
        """
        Create an intent classifier of the specified type.
        
        Args:
            classifier_type: The type of classifier to create
            
        Returns:
            A classifier instance with a classify_intent method
        """
        if classifier_type == ClassifierType.SEMANTIC_SIMILARITY:
            return IntentClassifierFactory._create_semantic_classifier()
        elif classifier_type == ClassifierType.KEYWORD_BASED:
            return IntentClassifierFactory._create_keyword_classifier()
        elif classifier_type == ClassifierType.AUTO:
            # Try semantic first, fall back to keyword
            try:
                return IntentClassifierFactory._create_semantic_classifier()
            except Exception:
                return IntentClassifierFactory._create_keyword_classifier()
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")
    
    @staticmethod
    def _create_semantic_classifier():
        """Create the improved semantic similarity classifier."""
        try:
            from services.improved_intent_classifier import get_improved_classifier
            return get_improved_classifier()
        except ImportError as e:
            raise ImportError(
                "Semantic classifier requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            ) from e
    
    @staticmethod
    def _create_keyword_classifier():
        """Create a wrapper for the old keyword-based classifier."""
        from services.nlp_query_parser import NLPQueryParser
        
        class KeywordClassifierWrapper:
            """Wrapper to make the old classifier compatible with the new interface."""
            
            def __init__(self):
                self.parser = NLPQueryParser(use_improved_classifier=False)
            
            def classify_intent(self, query: str) -> Tuple:
                """Classify intent using keyword-based approach."""
                return self.parser._classify_intent(query.lower())
        
        return KeywordClassifierWrapper()


def get_best_classifier():
    """Get the best available intent classifier."""
    return IntentClassifierFactory.create_classifier(ClassifierType.AUTO)


def classify_intent(query: str, classifier_type: ClassifierType = ClassifierType.AUTO) -> Tuple:
    """
    Classify a query's intent using the specified classifier type.
    
    Args:
        query: The query to classify
        classifier_type: The type of classifier to use
        
    Returns:
        Tuple of (intent, confidence)
    """
    classifier = IntentClassifierFactory.create_classifier(classifier_type)
    return classifier.classify_intent(query)


if __name__ == "__main__":
    # Demo usage
    test_queries = [
        "show me recent logs",
        "generate a security report",
        "what caused this error?",
        "display current alerts",
        "analyze performance trends"
    ]
    
    print("Intent Classification Factory Demo")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Try both classifiers
        try:
            semantic_intent, semantic_conf = classify_intent(query, ClassifierType.SEMANTIC_SIMILARITY)
            print(f"  Semantic: {semantic_intent.value} ({semantic_conf:.3f})")
        except Exception as e:
            print(f"  Semantic: Error - {e}")
        
        try:
            keyword_intent, keyword_conf = classify_intent(query, ClassifierType.KEYWORD_BASED)
            print(f"  Keyword:  {keyword_intent.value} ({keyword_conf:.3f})")
        except Exception as e:
            print(f"  Keyword:  Error - {e}")
        
        # Auto selection
        auto_intent, auto_conf = classify_intent(query, ClassifierType.AUTO)
        print(f"  Auto:     {auto_intent.value} ({auto_conf:.3f})")