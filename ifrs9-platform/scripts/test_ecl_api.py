#!/usr/bin/env python3
"""Test ECL calculation API endpoint"""
import requests
import json
from datetime import date

# API base URL
BASE_URL = "http://localhost:8000"

def test_ecl_calculation():
    """Test ECL calculation for a sample instrument"""
    
    # Test instrument ID from imported data
    instrument_id = "1001160398003"
    
    # Prepare request
    url = f"{BASE_URL}/api/v1/ecl/calculate"
    payload = {
        "instrument_id": instrument_id,
        "reporting_date": date.today().isoformat()
    }
    
    print(f"Testing ECL calculation for instrument: {instrument_id}")
    print(f"Request URL: {url}")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print("-" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ECL Calculation Successful!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ ECL Calculation Failed!")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
        print("Start the API with: ./start_api.sh")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_instrument_exists():
    """Check if the instrument exists in the database"""
    instrument_id = "1001160398003"
    url = f"{BASE_URL}/api/v1/instruments/{instrument_id}"
    
    print(f"\nChecking if instrument exists: {instrument_id}")
    print(f"Request URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            instrument = response.json()
            print("✅ Instrument found!")
            print(f"Customer ID: {instrument.get('customer_id')}")
            print(f"Stage: {instrument.get('current_stage')}")
            print(f"Principal: {instrument.get('principal_amount')}")
            print(f"DPD: {instrument.get('days_past_due')}")
            return True
        else:
            print(f"❌ Instrument not found: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ECL API Test Script")
    print("=" * 60)
    
    # Test 1: Check if instrument exists
    if test_instrument_exists():
        print("\n")
        # Test 2: Calculate ECL
        test_ecl_calculation()
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)
