import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def wait_for_server():
    print("Waiting for server to start...")
    for _ in range(10):
        try:
            resp = requests.get(f"{BASE_URL}/actuator/health")
            if resp.status_code == 200:
                print("Server is UP!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Server failed to start.")
    return False

def test_endpoints():
    print("\nTesting Endpoints:")
    
    # 1. Health
    try:
        resp = requests.get(f"{BASE_URL}/actuator/health")
        print(f"Health Check: {resp.status_code} - {resp.json()}")
        assert resp.status_code == 200
    except Exception as e:
        print(f"Health Check FAILED: {e}")
        return False

    # 2. Market Data (BTC-USDT)
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/market/BTC-USDT?limit=5")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Market Data (BTC-USDT): {len(data)} rows received")
            if len(data) > 0:
                 print(f"Sample: {data[0]}")
        else:
            print(f"Market Data FAILED: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Market Data FAILED: {e}")
        return False

    # 3. Metrics (BTC-USDT)
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/metrics/BTC-USDT?limit=5")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Metrics (BTC): {len(data)} rows received")
            if len(data) > 0:
                 print(f"Sample: {data[0]}")
        else:
            print(f"Metrics FAILED: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
         print(f"Metrics FAILED: {e}")
         return False
         
    return True

if __name__ == "__main__":
    if not wait_for_server():
        sys.exit(1)
    
    if not test_endpoints():
        sys.exit(1)
    
    print("\n✅ API Verification Passed")
