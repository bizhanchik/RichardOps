"""
Fast Log Classification Service

This module provides ultra-fast log classification using:
1. TF-IDF + Logistic Regression (primary)
2. LRU caching for repeated patterns
3. Rule-based fallback
4. Batch processing support

Designed for high-throughput log processing with minimal latency.
"""

import re
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from cachetools import LRUCache
import joblib
import os

# Import configuration
try:
    from config.log_classifier_config import get_classifier_config, ClassifierBackend
except ImportError:
    # Fallback if config module is not available
    class ClassifierBackend:
        ML_TFIDF = "ml_tfidf"
        RULE_BASED = "rule_based"
        HYBRID = "hybrid"
        DISABLED = "disabled"
    
    class DummyConfig:
        def __init__(self):
            self.backend = ClassifierBackend.ML_TFIDF
            self.cache_size = 10000
            self.confidence_threshold = 0.3
            self.max_features = 1000
            self.enable_fallback = True
            self.fallback_confidence = 0.8
            self.debug_mode = False
        
        def is_ml_enabled(self): return True
        def is_rule_based_enabled(self): return False
        def should_use_fallback(self): return True
    
    def get_classifier_config():
        return DummyConfig()

logger = logging.getLogger(__name__)


class FastLogClassifier:
    """Ultra-fast log classifier using ML and caching"""
    
    def __init__(self, cache_size: Optional[int] = None):
        # Load configuration
        self.config = get_classifier_config()
        
        # Initialize cache
        cache_size = cache_size or self.config.cache_size
        self.cache = LRUCache(maxsize=cache_size)
        
        # Initialize model based on configuration
        self.model = None
        self.is_trained = False
        
        if self.config.is_ml_enabled():
            self._initialize_model()
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.ml_predictions = 0
        self.rule_fallbacks = 0
    
    def _initialize_model(self):
        """Initialize the ML model with pre-trained patterns"""
        try:
            # Try to load pre-trained model
            model_path = os.path.join(os.path.dirname(__file__), 'log_classifier_model.joblib')
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                self.is_trained = True
                logger.info("Loaded pre-trained log classification model")
            else:
                # Create and train model with synthetic data
                self._create_and_train_model()
        except Exception as e:
            logger.warning(f"Failed to initialize ML model: {e}. Using rule-based fallback.")
            self.model = None
            self.is_trained = False
    
    def _create_and_train_model(self):
        """Create and train model with synthetic log data"""
        # Training data with common log patterns
        training_data = [
            # ERROR patterns
            ("ERROR: Database connection failed", "ERROR"),
            ("FATAL: Application crashed with exception", "ERROR"),
            ("Exception in thread main java.lang.NullPointerException", "ERROR"),
            ("ERROR 500: Internal server error", "ERROR"),
            ("CRITICAL: System out of memory", "ERROR"),
            ("ERROR: Failed to authenticate user", "ERROR"),
            ("SEVERE: Unable to connect to database", "ERROR"),
            ("ERROR: File not found /var/log/app.log", "ERROR"),
            ("FATAL ERROR: Segmentation fault", "ERROR"),
            ("ERROR: Connection timeout after 30 seconds", "ERROR"),
            
            # WARNING patterns
            ("WARNING: High memory usage detected", "WARN"),
            ("WARN: Deprecated API endpoint used", "WARN"),
            ("WARNING: SSL certificate expires in 7 days", "WARN"),
            ("CAUTION: Unusual login pattern detected", "WARN"),
            ("WARNING: Disk space low on /var partition", "WARN"),
            ("WARN: Rate limit exceeded for user", "WARN"),
            ("WARNING: Configuration file not found, using defaults", "WARN"),
            ("ALERT: Suspicious activity detected", "WARN"),
            ("WARNING: Cache miss ratio high", "WARN"),
            ("WARN: Connection pool exhausted", "WARN"),
            
            # INFO patterns
            ("INFO: Application started successfully", "INFO"),
            ("INFO: User logged in successfully", "INFO"),
            ("INFO: Processing request for /api/users", "INFO"),
            ("INFO: Database migration completed", "INFO"),
            ("INFO: Cache cleared successfully", "INFO"),
            ("INFO: Configuration loaded from config.yml", "INFO"),
            ("INFO: Backup completed successfully", "INFO"),
            ("INFO: Health check passed", "INFO"),
            ("INFO: Session created for user", "INFO"),
            ("INFO: Request processed in 150ms", "INFO"),
            
            # DEBUG patterns
            ("DEBUG: Entering function calculateTotal", "DEBUG"),
            ("DEBUG: Variable value: count=42", "DEBUG"),
            ("TRACE: SQL query executed in 5ms", "DEBUG"),
            ("DEBUG: Cache hit for key user:123", "DEBUG"),
            ("DEBUG: Validating input parameters", "DEBUG"),
            ("TRACE: Method execution completed", "DEBUG"),
            ("DEBUG: Connection established to localhost:5432", "DEBUG"),
            ("DEBUG: Parsing JSON response", "DEBUG"),
            ("TRACE: Function returned successfully", "DEBUG"),
            ("DEBUG: Loading configuration from environment", "DEBUG"),
        ]
        
        # Extract features and labels
        texts = [item[0] for item in training_data]
        labels = [item[1] for item in training_data]
        
        # Create pipeline with TF-IDF and Logistic Regression
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=self.config.max_features,
                ngram_range=(1, 2),
                stop_words='english',
                lowercase=True,
                strip_accents='ascii'
            )),
            ('classifier', LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced'
            ))
        ])
        
        # Train the model
        self.model.fit(texts, labels)
        self.is_trained = True
        
        # Save the model
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'log_classifier_model.joblib')
            joblib.dump(self.model, model_path)
            logger.info("Trained and saved log classification model")
        except Exception as e:
            logger.warning(f"Failed to save model: {e}")
    
    def _get_cache_key(self, message: str) -> str:
        """Generate cache key for message"""
        # Use hash of normalized message for cache key
        normalized = re.sub(r'\d+', 'NUM', message.lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _rule_based_classify(self, message: str) -> Optional[str]:
        """Fallback rule-based classification"""
        if not message:
            return None
        
        message_upper = message.upper()
        
        # Error patterns (highest priority)
        error_patterns = ['ERROR', 'FATAL', 'CRITICAL', 'SEVERE', 'EXCEPTION', 'FAILED', 'CRASH']
        if any(pattern in message_upper for pattern in error_patterns):
            return "ERROR"
        
        # Warning patterns
        warn_patterns = ['WARNING', 'WARN', 'CAUTION', 'ALERT', 'DEPRECATED']
        if any(pattern in message_upper for pattern in warn_patterns):
            return "WARN"
        
        # Debug patterns
        debug_patterns = ['DEBUG', 'TRACE', 'VERBOSE']
        if any(pattern in message_upper for pattern in debug_patterns):
            return "DEBUG"
        
        # Default to INFO
        return "INFO"
    
    def classify_single(self, message: str) -> Tuple[str, float]:
        """
        Classify a single log message
        
        Args:
            message: Log message text
            
        Returns:
            Tuple of (log_level, confidence)
        """
        if not message or not message.strip():
            return "INFO", 0.5
        
        # Handle disabled backend
        if self.config.backend == ClassifierBackend.DISABLED:
            return "INFO", 1.0
        
        # Check cache first
        cache_key = self._get_cache_key(message)
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        
        self.cache_misses += 1
        
        # Choose classification method based on backend
        if self.config.backend == ClassifierBackend.RULE_BASED:
            # Pure rule-based
            self.rule_fallbacks += 1
            rule_result = self._rule_based_classify(message)
            result = (rule_result, self.config.fallback_confidence)
        
        elif self.config.backend == ClassifierBackend.ML_TFIDF:
            # Pure ML
            result = self._ml_classify_single(message)
            
        elif self.config.backend == ClassifierBackend.HYBRID:
            # Try ML first, fallback to rules
            result = self._ml_classify_single(message)
            
            # Use rule-based if ML confidence is too low
            if result[1] < self.config.confidence_threshold and self.config.should_use_fallback():
                self.rule_fallbacks += 1
                rule_result = self._rule_based_classify(message)
                result = (rule_result, self.config.fallback_confidence)
        
        else:
            # Default to ML
            result = self._ml_classify_single(message)
        
        # Cache the result
        self.cache[cache_key] = result
        return result
    
    def _ml_classify_single(self, message: str) -> Tuple[str, float]:
        """Perform ML classification on a single message"""
        if self.is_trained and self.model:
            try:
                # Get prediction and probability
                prediction = self.model.predict([message])[0]
                probabilities = self.model.predict_proba([message])[0]
                confidence = float(np.max(probabilities))
                
                self.ml_predictions += 1
                return (prediction, confidence)
                
            except Exception as e:
                if self.config.debug_mode:
                    logger.debug(f"ML classification failed: {e}")
        
        # Fallback to rule-based if ML fails
        self.rule_fallbacks += 1
        rule_result = self._rule_based_classify(message)
        return (rule_result, self.config.fallback_confidence)
    
    def classify_batch(self, messages: List[str]) -> List[Tuple[str, float]]:
        """
        Classify multiple log messages efficiently
        
        Args:
            messages: List of log message texts
            
        Returns:
            List of (log_level, confidence) tuples
        """
        results = []
        uncached_messages = []
        uncached_indices = []
        
        # Check cache for all messages
        for i, message in enumerate(messages):
            if not message or not message.strip():
                results.append(("INFO", 0.5))
                continue
                
            cache_key = self._get_cache_key(message)
            if cache_key in self.cache:
                self.cache_hits += 1
                results.append(self.cache[cache_key])
            else:
                self.cache_misses += 1
                results.append(None)  # Placeholder
                uncached_messages.append(message)
                uncached_indices.append(i)
        
        # Process uncached messages in batch
        if uncached_messages and self.is_trained and self.model:
            try:
                predictions = self.model.predict(uncached_messages)
                probabilities = self.model.predict_proba(uncached_messages)
                
                for j, (pred, probs) in enumerate(zip(predictions, probabilities)):
                    confidence = float(np.max(probs))
                    result = (pred, confidence)
                    
                    # Update results and cache
                    idx = uncached_indices[j]
                    results[idx] = result
                    cache_key = self._get_cache_key(uncached_messages[j])
                    self.cache[cache_key] = result
                
                self.ml_predictions += len(uncached_messages)
                
            except Exception as e:
                logger.debug(f"Batch ML classification failed: {e}")
                # Fallback to rule-based for uncached messages
                for j, message in enumerate(uncached_messages):
                    rule_result = self._rule_based_classify(message)
                    result = (rule_result, 0.8)
                    
                    idx = uncached_indices[j]
                    results[idx] = result
                    cache_key = self._get_cache_key(message)
                    self.cache[cache_key] = result
                
                self.rule_fallbacks += len(uncached_messages)
        
        elif uncached_messages:
            # Use rule-based for all uncached messages
            for j, message in enumerate(uncached_messages):
                rule_result = self._rule_based_classify(message)
                result = (rule_result, 0.8)
                
                idx = uncached_indices[j]
                results[idx] = result
                cache_key = self._get_cache_key(message)
                self.cache[cache_key] = result
            
            self.rule_fallbacks += len(uncached_messages)
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "ml_predictions": self.ml_predictions,
            "rule_fallbacks": self.rule_fallbacks,
            "cache_size": len(self.cache),
            "model_trained": self.is_trained
        }
    
    def clear_cache(self):
        """Clear the classification cache"""
        self.cache.clear()
        logger.info("Classification cache cleared")
    
    def warm_cache(self, common_patterns: List[str]):
        """Pre-warm cache with common log patterns"""
        logger.info(f"Warming cache with {len(common_patterns)} patterns")
        for pattern in common_patterns:
            self.classify_single(pattern)


# Global classifier instance
_log_classifier: Optional[FastLogClassifier] = None


def get_log_classifier() -> FastLogClassifier:
    """Get the global log classifier instance"""
    global _log_classifier
    if _log_classifier is None:
        _log_classifier = FastLogClassifier()
        
        # Warm up with common patterns
        common_patterns = [
            "INFO: Application started",
            "ERROR: Database connection failed",
            "WARNING: High memory usage",
            "DEBUG: Processing request",
            "FATAL: System crash",
            "WARN: Configuration missing"
        ]
        _log_classifier.warm_cache(common_patterns)
    
    return _log_classifier


def classify_log_message(message: str) -> Tuple[str, float]:
    """
    Classify a single log message
    
    Args:
        message: Log message text
        
    Returns:
        Tuple of (log_level, confidence)
    """
    classifier = get_log_classifier()
    return classifier.classify_single(message)


def classify_log_messages(messages: List[str]) -> List[Tuple[str, float]]:
    """
    Classify multiple log messages efficiently
    
    Args:
        messages: List of log message texts
        
    Returns:
        List of (log_level, confidence) tuples
    """
    classifier = get_log_classifier()
    return classifier.classify_batch(messages)