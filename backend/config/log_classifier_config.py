"""
Log Classifier Configuration

This module provides configuration options for the log classification system,
allowing users to choose between different backends and tune performance settings.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum


class ClassifierBackend(Enum):
    """Available classifier backends"""
    ML_TFIDF = "ml_tfidf"  # TF-IDF + Logistic Regression (default)
    RULE_BASED = "rule_based"  # Simple rule-based classification
    HYBRID = "hybrid"  # ML with rule-based fallback
    DISABLED = "disabled"  # No classification (returns INFO)


class LogClassifierConfig:
    """Configuration for log classification system"""
    
    def __init__(self):
        # Backend selection
        self.backend = self._get_backend_from_env()
        
        # Performance settings
        self.cache_size = int(os.getenv("LOG_CLASSIFIER_CACHE_SIZE", "10000"))
        self.batch_size = int(os.getenv("LOG_CLASSIFIER_BATCH_SIZE", "1000"))
        self.confidence_threshold = float(os.getenv("LOG_CLASSIFIER_CONFIDENCE_THRESHOLD", "0.3"))
        
        # ML Model settings
        self.model_path = os.getenv("LOG_CLASSIFIER_MODEL_PATH", "")
        self.auto_retrain = os.getenv("LOG_CLASSIFIER_AUTO_RETRAIN", "false").lower() == "true"
        self.max_features = int(os.getenv("LOG_CLASSIFIER_MAX_FEATURES", "1000"))
        
        # Fallback settings
        self.enable_fallback = os.getenv("LOG_CLASSIFIER_ENABLE_FALLBACK", "true").lower() == "true"
        self.fallback_confidence = float(os.getenv("LOG_CLASSIFIER_FALLBACK_CONFIDENCE", "0.8"))
        
        # Performance monitoring
        self.enable_metrics = os.getenv("LOG_CLASSIFIER_ENABLE_METRICS", "true").lower() == "true"
        self.metrics_interval = int(os.getenv("LOG_CLASSIFIER_METRICS_INTERVAL", "1000"))
        
        # Debug settings
        self.debug_mode = os.getenv("LOG_CLASSIFIER_DEBUG", "false").lower() == "true"
        self.log_misclassifications = os.getenv("LOG_CLASSIFIER_LOG_MISCLASSIFICATIONS", "false").lower() == "true"
    
    def _get_backend_from_env(self) -> ClassifierBackend:
        """Get backend from environment variable"""
        backend_str = os.getenv("LOG_CLASSIFIER_BACKEND", "ml_tfidf").lower()
        
        try:
            return ClassifierBackend(backend_str)
        except ValueError:
            # Invalid backend, default to ML TF-IDF
            return ClassifierBackend.ML_TFIDF
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "backend": self.backend.value,
            "cache_size": self.cache_size,
            "batch_size": self.batch_size,
            "confidence_threshold": self.confidence_threshold,
            "model_path": self.model_path,
            "auto_retrain": self.auto_retrain,
            "max_features": self.max_features,
            "enable_fallback": self.enable_fallback,
            "fallback_confidence": self.fallback_confidence,
            "enable_metrics": self.enable_metrics,
            "metrics_interval": self.metrics_interval,
            "debug_mode": self.debug_mode,
            "log_misclassifications": self.log_misclassifications
        }
    
    def is_ml_enabled(self) -> bool:
        """Check if ML classification is enabled"""
        return self.backend in [ClassifierBackend.ML_TFIDF, ClassifierBackend.HYBRID]
    
    def is_rule_based_enabled(self) -> bool:
        """Check if rule-based classification is enabled"""
        return self.backend in [ClassifierBackend.RULE_BASED, ClassifierBackend.HYBRID]
    
    def should_use_fallback(self) -> bool:
        """Check if fallback should be used"""
        return self.enable_fallback and self.backend == ClassifierBackend.HYBRID


# Global configuration instance
_config: Optional[LogClassifierConfig] = None


def get_classifier_config() -> LogClassifierConfig:
    """Get the global classifier configuration"""
    global _config
    if _config is None:
        _config = LogClassifierConfig()
    return _config


def reload_config():
    """Reload configuration from environment"""
    global _config
    _config = LogClassifierConfig()


# Configuration presets for different use cases
PERFORMANCE_PRESET = {
    "LOG_CLASSIFIER_BACKEND": "hybrid",
    "LOG_CLASSIFIER_CACHE_SIZE": "50000",
    "LOG_CLASSIFIER_BATCH_SIZE": "5000",
    "LOG_CLASSIFIER_CONFIDENCE_THRESHOLD": "0.2",
    "LOG_CLASSIFIER_ENABLE_FALLBACK": "true",
    "LOG_CLASSIFIER_ENABLE_METRICS": "false"
}

ACCURACY_PRESET = {
    "LOG_CLASSIFIER_BACKEND": "ml_tfidf",
    "LOG_CLASSIFIER_CACHE_SIZE": "10000",
    "LOG_CLASSIFIER_BATCH_SIZE": "1000",
    "LOG_CLASSIFIER_CONFIDENCE_THRESHOLD": "0.5",
    "LOG_CLASSIFIER_MAX_FEATURES": "2000",
    "LOG_CLASSIFIER_ENABLE_FALLBACK": "true",
    "LOG_CLASSIFIER_ENABLE_METRICS": "true"
}

MINIMAL_PRESET = {
    "LOG_CLASSIFIER_BACKEND": "rule_based",
    "LOG_CLASSIFIER_CACHE_SIZE": "1000",
    "LOG_CLASSIFIER_ENABLE_METRICS": "false",
    "LOG_CLASSIFIER_ENABLE_FALLBACK": "false"
}


def apply_preset(preset_name: str):
    """Apply a configuration preset"""
    presets = {
        "performance": PERFORMANCE_PRESET,
        "accuracy": ACCURACY_PRESET,
        "minimal": MINIMAL_PRESET
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
    
    preset = presets[preset_name]
    for key, value in preset.items():
        os.environ[key] = value
    
    # Reload configuration
    reload_config()


def get_config_summary() -> str:
    """Get a human-readable configuration summary"""
    config = get_classifier_config()
    
    summary = f"""
Log Classifier Configuration:
============================
Backend: {config.backend.value}
Cache Size: {config.cache_size:,}
Batch Size: {config.batch_size:,}
Confidence Threshold: {config.confidence_threshold}
ML Features: {config.max_features:,}
Fallback Enabled: {config.enable_fallback}
Metrics Enabled: {config.enable_metrics}
Debug Mode: {config.debug_mode}
"""
    
    return summary.strip()