"""Test the 4 scenarios described in instructions.md."""
import time
import requests

BASE = "http://127.0.0.1:5000"
WAIT = 30  # seconds between tests to avoid rate limiting

def test(name, message):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    r = requests.post(f"{BASE}/api/chat", json={"message": message}, stream=True, timeout=180)
    print(f"Status: {r.status_code}")
    for line in r.iter_lines(decode_unicode=True):
        if line:
            print(line)
    print()

# Clear chat
requests.post(f"{BASE}/api/clear")
time.sleep(2)

test("Test 1: Normal Chat", "你好，今天天气怎么样？")
print(f"Waiting {WAIT}s...")
time.sleep(WAIT)

# Clear for fresh context
requests.post(f"{BASE}/api/clear")
time.sleep(2)

test("Test 2: Suggest Intervention", "最近遭受了小团体排挤，很焦虑")
print(f"Waiting {WAIT}s...")
time.sleep(WAIT)

requests.post(f"{BASE}/api/clear")
time.sleep(2)

test("Test 3: Force Intervention", "出现严重焦虑，感觉生命没有意义")
print(f"Waiting {WAIT}s...")
time.sleep(WAIT)

requests.post(f"{BASE}/api/clear")
time.sleep(2)

test("Test 4: Health Advice", "手划伤了")

print("\n\nAll tests completed.")
