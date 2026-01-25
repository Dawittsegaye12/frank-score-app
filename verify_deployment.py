"""
Quick script to verify Render deployment is working correctly.
Run this locally to test your deployed app.
"""
import requests
import sys

# Get base URL from command line or use default
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://your-app.onrender.com"

print(f"Testing deployment at: {BASE_URL}\n")

# Test 1: Health check
print("1. Testing health endpoint...")
try:
    resp = requests.get(f"{BASE_URL}/health", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ Health check passed: {data}")
    else:
        print(f"   ❌ Health check failed: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Health check error: {e}")

# Test 2: Home page (should redirect to login)
print("\n2. Testing home page...")
try:
    resp = requests.get(f"{BASE_URL}/", timeout=10, allow_redirects=False)
    if resp.status_code in [200, 302]:
        print(f"   ✅ Home page accessible: {resp.status_code}")
    else:
        print(f"   ❌ Home page failed: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Home page error: {e}")

# Test 3: Admin dashboard
print("\n3. Testing admin dashboard...")
try:
    resp = requests.get(f"{BASE_URL}/admin", timeout=10)
    if resp.status_code == 200:
        print(f"   ✅ Admin dashboard accessible")
    elif resp.status_code == 403:
        print(f"   ⚠️  Admin dashboard blocked (ADMIN_MODE=false)")
    else:
        print(f"   ❌ Admin dashboard failed: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Admin dashboard error: {e}")

# Test 4: Questions API
print("\n4. Testing questions API...")
try:
    resp = requests.get(f"{BASE_URL}/api/questions", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ Questions API working: {len(data)} questions available")
    else:
        print(f"   ❌ Questions API failed: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Questions API error: {e}")

# Test 5: Static files
print("\n5. Testing static files...")
try:
    resp = requests.get(f"{BASE_URL}/static/app.css", timeout=10)
    if resp.status_code == 200:
        print(f"   ✅ Static files accessible")
    else:
        print(f"   ⚠️  Static files not found (may be normal)")
except Exception as e:
    print(f"   ⚠️  Static files check: {e}")

print("\n" + "="*50)
print("Deployment verification complete!")
print("="*50)
print("\nNext steps:")
print("1. Test signup/login flow")
print("2. Complete a full assessment")
print("3. Check admin dashboard metrics")
print("4. Verify model predictions are working")

