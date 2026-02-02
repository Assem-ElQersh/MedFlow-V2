#!/usr/bin/env python3
"""
Test script to verify MedGemma Colab connection
Usage: python test_medgemma_connection.py <ngrok_url>
Example: python test_medgemma_connection.py https://xxxx.ngrok-free.app
"""

import sys
import requests
import json

def test_connection(remote_url):
    """Test connection to MedGemma Colab service"""
    
    print("=" * 60)
    print("MedGemma Connection Test")
    print("=" * 60)
    print(f"\nRemote URL: {remote_url}\n")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{remote_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Connected successfully!")
            print(f"   Model: {data.get('model', 'Unknown')}")
            print(f"   Device: {data.get('device', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
        else:
            print(f"   ✗ Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ✗ Connection timeout - Is Colab running?")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ✗ Connection error - Check URL and network")
        print(f"   Error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    # Test 2: Simple text prediction
    print("\n2. Testing text prediction...")
    test_prompt = "What are the common symptoms of pneumonia?"
    try:
        response = requests.post(
            f"{remote_url}/predict_text",
            json={
                "text": test_prompt,
                "max_new_tokens": 200
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Text prediction working!")
            print(f"   Response preview: {data.get('response', '')[:100]}...")
        else:
            print(f"   ✗ Status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ✗ Request timeout (model might be loading, try again)")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! MedGemma service is ready.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add this URL to your .env file:")
    print(f"   MEDGEMMA_REMOTE_URL={remote_url}")
    print("2. Restart MedFlow services:")
    print("   docker compose restart backend celery-worker")
    print("3. Start using MedFlow with real AI analysis!")
    print()
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_medgemma_connection.py <ngrok_url>")
        print("Example: python test_medgemma_connection.py https://xxxx.ngrok-free.app")
        sys.exit(1)
    
    remote_url = sys.argv[1].rstrip('/')  # Remove trailing slash if present
    
    if not remote_url.startswith('http'):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    success = test_connection(remote_url)
    sys.exit(0 if success else 1)
