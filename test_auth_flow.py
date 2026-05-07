import urllib.request
import json
import sys

base_url = "https://attendance-system-pkccs.onrender.com"

# Step 1: Login
print("Step 1: Testing LOGIN...")
login_data = json.dumps({
    "email": "pkccsattendance88@gmail.com",
    "password": "PKCCSSAMS@88"
}).encode('utf-8')

req = urllib.request.Request(
    f"{base_url}/login",
    data=login_data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        response = resp.read().decode()
        print(f"✅ Status: {resp.status}")
        print(f"Response: {response}")
        
        # Extract token
        data = json.loads(response)
        token = data.get('token')
        print(f"\n✅ Token received: {token[:20]}...\n")
        
        # Step 2: Test /me with token
        print("Step 2: Testing /me endpoint with token...")
        req2 = urllib.request.Request(
            f"{base_url}/me",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            response2 = resp2.read().decode()
            print(f"✅ Status: {resp2.status}")
            print(f"Response: {response2}")
            
            # Step 3: Test /students with token
            print("\nStep 3: Testing /students endpoint with token...")
            req3 = urllib.request.Request(
                f"{base_url}/students",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            with urllib.request.urlopen(req3, timeout=15) as resp3:
                response3 = resp3.read().decode()
                print(f"✅ Status: {resp3.status}")
                data3 = json.loads(response3)
                print(f"✅ Students count: {len(data3)}")
                print(f"✅ SUCCESS! Token काम कर रहा है!\n")
                
except urllib.error.HTTPError as e:
    print(f"❌ Error {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"❌ Exception: {str(e)}")
