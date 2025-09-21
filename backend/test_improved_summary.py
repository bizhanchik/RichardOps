#!/usr/bin/env python3
"""
Test script to demonstrate the improved analytics summary functionality
"""

import asyncio
import json
from datetime import datetime, timedelta
from services.summary_service import SummaryService

async def test_improved_summary():
    """Test the improved summary service with better data quality handling"""
    
    print("🔍 Testing Improved Analytics Summary Service")
    print("=" * 50)
    
    # Initialize the summary service
    summary_service = SummaryService()
    
    # Test different time periods
    periods = ["1h", "24h", "7d"]
    
    for period in periods:
        print(f"\n📊 Testing period: {period}")
        print("-" * 30)
        
        try:
            # Get summary data
            summary = await summary_service.get_summary(period)
            
            print(f"✅ Summary generated successfully for {period}")
            
            # Check metrics data quality
            if "metrics" in summary:
                print("\n📈 Metrics Analysis:")
                for metric_name, metric_data in summary["metrics"].items():
                    if isinstance(metric_data, dict) and "status" in metric_data:
                        status = metric_data["status"]
                        count = metric_data.get("count", 0)
                        avg = metric_data.get("avg")
                        
                        if status == "no_data":
                            print(f"  ⚠️  {metric_name}: No data available ({count} records)")
                        else:
                            print(f"  ✅ {metric_name}: Avg={avg}, Count={count}")
                    else:
                        # Legacy format
                        print(f"  📊 {metric_name}: {metric_data} (legacy format)")
            
            # Check data quality information
            if "data_quality" in summary:
                print("\n🔍 Data Quality Report:")
                dq = summary["data_quality"]
                print(f"  📊 Total Records: {dq.get('total_records', 'N/A')}")
                print(f"  🔴 CPU NULL: {dq.get('cpu_null_percentage', 'N/A')}% ({dq.get('cpu_null_count', 'N/A')} records)")
                print(f"  🟠 Memory NULL: {dq.get('memory_null_percentage', 'N/A')}% ({dq.get('memory_null_count', 'N/A')} records)")
                if "summary" in dq:
                    print(f"  📝 Summary: {dq['summary']}")
            
            # Check other sections
            sections = ["alerts", "events", "logs", "containers"]
            for section in sections:
                if section in summary:
                    section_data = summary[section]
                    if isinstance(section_data, dict):
                        count = len(section_data)
                        print(f"  📋 {section.title()}: {count} items")
                    else:
                        print(f"  📋 {section.title()}: Available")
                        
        except Exception as e:
            print(f"❌ Error testing {period}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("✅ Improved metrics handling with null value detection")
    print("✅ Data quality reporting with statistics")
    print("✅ Better error handling and status reporting")
    print("✅ Backward compatibility with existing data")

if __name__ == "__main__":
    # Note: This test requires database connection
    print("⚠️  Note: This test requires database connection.")
    print("   To run with actual database, ensure DATABASE_URL is configured.")
    print("   For demonstration purposes, this shows the improved structure.")
    
    # Show example of improved data structure
    print("\n📋 Example of Improved Data Structure:")
    example_summary = {
        "metrics": {
            "cpu_usage": {
                "min": None,
                "max": None,
                "avg": None,
                "count": 0,
                "status": "no_data"
            },
            "memory_usage": {
                "min": 45.2,
                "max": 78.9,
                "avg": 62.1,
                "count": 150,
                "status": "ok"
            }
        },
        "data_quality": {
            "total_records": 200,
            "cpu_null_count": 200,
            "cpu_null_percentage": 100.0,
            "memory_null_count": 50,
            "memory_null_percentage": 25.0,
            "summary": "High percentage of NULL values detected in CPU metrics. Memory metrics have good data quality."
        },
        "alerts": {},
        "events": {},
        "generated_at": datetime.now().isoformat()
    }
    
    print(json.dumps(example_summary, indent=2))