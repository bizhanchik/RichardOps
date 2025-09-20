#!/usr/bin/env python3
"""
Test script to verify NLP endpoints are properly connected to the FastAPI app.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_nlp_endpoints():
    """Test that NLP endpoints are properly connected to the FastAPI app."""
    try:
        # Import the main app
        from main import app
        
        # Get all routes from the app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if route.methods else [],
                    'name': getattr(route, 'name', 'unnamed')
                })
        
        # Filter NLP routes
        nlp_routes = [route for route in routes if '/nlp' in route['path']]
        
        print("=== NLP Endpoints Test Results ===")
        print(f"Total routes found: {len(routes)}")
        print(f"NLP routes found: {len(nlp_routes)}")
        print()
        
        if nlp_routes:
            print("NLP Endpoints successfully connected:")
            for route in nlp_routes:
                methods_str = ', '.join(route['methods']) if route['methods'] else 'N/A'
                print(f"  - {route['path']} [{methods_str}]")
        else:
            print("❌ No NLP endpoints found!")
            return False
        
        # Check for specific expected endpoints
        expected_endpoints = [
            '/nlp/test',
            '/nlp/process', 
            '/api/nlp/query',
            '/api/nlp/suggestions',
            '/api/nlp/status',
            '/api/nlp/examples',
            '/api/nlp/test',
            '/api/nlp/health'
        ]
        
        found_endpoints = [route['path'] for route in nlp_routes]
        missing_endpoints = [ep for ep in expected_endpoints if ep not in found_endpoints]
        
        print()
        if missing_endpoints:
            print("⚠️  Missing expected endpoints:")
            for ep in missing_endpoints:
                print(f"  - {ep}")
        else:
            print("✅ All expected NLP endpoints are connected!")
        
        return len(missing_endpoints) == 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False

if __name__ == "__main__":
    success = test_nlp_endpoints()
    sys.exit(0 if success else 1)