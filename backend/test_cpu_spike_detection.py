#!/usr/bin/env python3
"""
Test script to verify CPU spike detection in the integrated anomaly detection system.
This simulates the data flow from the Go client to the backend anomaly detection.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.anomaly_detection import AnomalyDetectionService

async def test_cpu_spike_detection():
    """Test CPU spike detection with simulated data"""
    print("🧪 Testing CPU Spike Detection Integration")
    print("=" * 50)
    
    # Create anomaly detection service
    service = AnomalyDetectionService()
    
    # Test 1: Normal CPU usage (should not trigger)
    print("\n📊 Test 1: Normal CPU Usage")
    normal_metrics = {
        'cpu_usage': 25.5,
        'memory_usage': 45.2,
        'disk_usage': 60.1,
        'tcp_connections': 150,
        'timestamp': datetime.now(timezone.utc)
    }
    
    try:
        anomalies = await service.detect_metric_spikes(normal_metrics)
        print(f"✅ Normal metrics processed: {len(anomalies)} anomalies detected")
        for anomaly in anomalies:
            print(f"   - {anomaly.type}: {anomaly.description}")
    except Exception as e:
        print(f"❌ Error processing normal metrics: {e}")
    
    # Test 2: CPU spike (should trigger)
    print("\n🚨 Test 2: CPU Spike Detection")
    spike_metrics = {
        'cpu_usage': 95.8,  # High CPU usage
        'memory_usage': 45.2,
        'disk_usage': 60.1,
        'tcp_connections': 150,
        'timestamp': datetime.now(timezone.utc)
    }
    
    try:
        anomalies = await service.detect_metric_spikes(spike_metrics)
        print(f"✅ Spike metrics processed: {len(anomalies)} anomalies detected")
        
        cpu_spike_found = False
        for anomaly in anomalies:
            print(f"   - {anomaly.type}: {anomaly.description} (Severity: {anomaly.severity})")
            if anomaly.type == "cpu_spike":
                cpu_spike_found = True
                print(f"     🎯 CPU spike detected! Confidence: {anomaly.confidence:.2%}")
                print(f"     📊 Details: {anomaly.details}")
        
        if not cpu_spike_found:
            print("⚠️  Warning: CPU spike not detected - check thresholds")
        
    except Exception as e:
        print(f"❌ Error processing spike metrics: {e}")
    
    # Test 3: Multiple spikes
    print("\n🔥 Test 3: Multiple Metric Spikes")
    multi_spike_metrics = {
        'cpu_usage': 92.3,
        'memory_usage': 88.7,  # High memory too
        'disk_usage': 95.1,    # High disk usage
        'tcp_connections': 850, # High connections
        'timestamp': datetime.now(timezone.utc)
    }
    
    try:
        anomalies = await service.detect_metric_spikes(multi_spike_metrics)
        print(f"✅ Multi-spike metrics processed: {len(anomalies)} anomalies detected")
        
        spike_types = []
        for anomaly in anomalies:
            print(f"   - {anomaly.type}: {anomaly.description} (Severity: {anomaly.severity})")
            spike_types.append(anomaly.type)
        
        expected_spikes = ["cpu_spike", "memory_spike", "disk_spike", "tcp_spike"]
        for expected in expected_spikes:
            if expected in spike_types:
                print(f"     ✅ {expected} detected")
            else:
                print(f"     ⚠️  {expected} not detected")
                
    except Exception as e:
        print(f"❌ Error processing multi-spike metrics: {e}")
    
    # Test 4: Check thresholds
    print("\n⚙️  Test 4: Anomaly Detection Thresholds")
    thresholds = service.thresholds
    print(f"   CPU spike threshold: {thresholds.cpu_spike_threshold}%")
    print(f"   Memory spike threshold: {thresholds.memory_spike_threshold}%")
    print(f"   Disk spike threshold: {thresholds.disk_spike_threshold}%")
    print(f"   IP request threshold: {thresholds.ip_request_threshold} requests/hour")
    print(f"   Error rate threshold: {thresholds.error_rate_threshold}%")
    
    print("\n🎉 CPU Spike Detection Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_cpu_spike_detection())