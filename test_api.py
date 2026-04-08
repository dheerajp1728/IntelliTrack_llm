#!/usr/bin/env python3
"""
Test script for the Agile Tracker API
Tests the /progress endpoint with sample data
"""

import requests
import socket
import sys
import json
from time import sleep

# Configuration
API_URL = "http://127.0.0.1:8004"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
LM_STUDIO_HOST = "127.0.0.1"
LM_STUDIO_PORT = 1234

def check_service(host, port, name):
    """Check if a service is running on host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def print_status(status, message):
    """Print colored status message"""
    if status:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    return status

def check_services():
    """Check if all required services are running"""
    print("\n" + "="*60)
    print("CHECKING REQUIRED SERVICES")
    print("="*60)
    
    all_ok = True
    
    # Check Qdrant
    if not check_service(QDRANT_HOST, QDRANT_PORT, f"Qdrant (localhost:{QDRANT_PORT})"):
        print_status(False, f"Qdrant is not running on {QDRANT_HOST}:{QDRANT_PORT}")
        print("   Start it with: docker run -p 6333:6333 qdrant/qdrant")
        all_ok = False
    else:
        print_status(True, f"Qdrant is running on {QDRANT_HOST}:{QDRANT_PORT}")
    
    # Check LM Studio
    if not check_service(LM_STUDIO_HOST, LM_STUDIO_PORT, f"LM Studio (127.0.0.1:{LM_STUDIO_PORT})"):
        print_status(False, f"LM Studio is not running on {LM_STUDIO_HOST}:{LM_STUDIO_PORT}")
        print("   Start LM Studio and load a model")
        all_ok = False
    else:
        print_status(True, f"LM Studio is running on {LM_STUDIO_HOST}:{LM_STUDIO_PORT}")
    
    # Check FastAPI server
    try:
        response = requests.get(f"{API_URL}/docs", timeout=2)
        print_status(True, f"FastAPI server is running on {API_URL}")
    except requests.exceptions.ConnectionError:
        print_status(False, f"FastAPI server is not running on {API_URL}")
        print("   Start it with: python -m uvicorn main:app --host 127.0.0.1 --port 8004")
        all_ok = False
    except Exception as e:
        print_status(False, f"Error checking FastAPI: {e}")
        all_ok = False
    
    return all_ok

def test_api():
    """Test the /progress API endpoint"""
    print("\n" + "="*60)
    print("TESTING API ENDPOINT")
    print("="*60)
    
    # Sample request
    payload = {
        "repo_url": "https://github.com/vignesh362/Search-Engine",
        "tasks": """Implement BM25 ranking algorithm
Build compressed inverted index with VarByte encoding
Add support for both OR and AND query modes
Create a Google-like web interface for search
Enable real-time system logs in the UI"""
    }
    
    print(f"\nSending POST request to {API_URL}/progress")
    print(f"Repository: {payload['repo_url']}")
    print(f"Number of tasks: {len(payload['tasks'].splitlines())}")
    
    try:
        response = requests.post(
            f"{API_URL}/progress",
            json=payload,
            timeout=300  # 5 minute timeout for processing
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_status(True, "API request successful (HTTP 200)")
            
            try:
                data = response.json()
                print_status(True, "Response is valid JSON")
                
                # Validate response structure
                if "results" in data:
                    print_status(True, f"Response contains 'results' field ({len(data['results'])} tasks)")
                else:
                    print_status(False, "Response missing 'results' field")
                    return False
                
                if "progress_percent" in data:
                    print_status(True, f"Response contains 'progress_percent' field (value: {data['progress_percent']}%)")
                else:
                    print_status(False, "Response missing 'progress_percent' field")
                    return False
                
                # Print sample results
                print("\nSample Results:")
                print("-" * 60)
                for i, result in enumerate(data["results"][:3], 1):
                    task = result.get("task", "N/A")[:50]
                    progress = result.get("progress", "N/A")[:50]
                    print(f"  Task {i}: {task}...")
                    print(f"  Status: {progress}...")
                    print()
                
                return True
            except json.JSONDecodeError as e:
                print_status(False, f"Failed to parse JSON response: {e}")
                print(f"Response text: {response.text[:500]}")
                return False
        else:
            print_status(False, f"API returned status code {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print_status(False, "Request timed out (took more than 5 minutes)")
        return False
    except requests.exceptions.ConnectionError as e:
        print_status(False, f"Connection error: {e}")
        return False
    except Exception as e:
        print_status(False, f"Unexpected error: {e}")
        return False

def main():
    """Main test routine"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  AGILE TRACKER API TEST SUITE".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    # Check services
    services_ok = check_services()
    
    if not services_ok:
        print("\n" + "="*60)
        print("❌ NOT ALL SERVICES ARE RUNNING")
        print("="*60)
        print("\nPlease start all required services and try again.")
        return 1
    
    # Test API
    print("\n")
    api_ok = test_api()
    
    # Final summary
    print("\n" + "="*60)
    if api_ok:
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe API is working correctly. You can now:")
        print("  1. Use curl to test the endpoint")
        print("  2. Integrate the API into your application")
        print("  3. Monitor logs with: tail -f server.log")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the errors above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
