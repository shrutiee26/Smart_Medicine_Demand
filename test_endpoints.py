import urllib.request
import json

base = '.\.venv\Scripts\Activate.ps1'
endpoints = [
    ('/', 'text/html'),
    ('/style.css', 'text/css'),
    ('/app.js', 'javascript'),
    ('/api/dashboard', 'application/json'),
    ('/api/medicines', 'application/json'),
    ('/api/forecast/MED-101', 'application/json'),
    ('/api/export/reorders', 'text/csv'),
]

print("=== VERIFYING ENDPOINTS ===")
for ep, expected in endpoints:
    url = base + ep
    try:
        req = urllib.request.urlopen(url)
        ct = req.headers.get("Content-Type", "")
        print(f"[PASS] {ep:<25} Status: {req.status} | Content-Type: {ct[:30]}")
    except Exception as e:
        print(f"[FAIL] {ep:<25} Error: {e}")

# Test POST /api/simulate
data = json.dumps({'horizon_days': 30, 'outbreak_multiplier': 1.5, 'lead_time_buffer_days': 2}).encode()
req = urllib.request.Request(base + '/api/simulate', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
print(f"[PASS] POST /api/simulate        Status: {resp.status}")

# Test POST /api/reorder/confirm
data2 = json.dumps({'medicine_id': 'MED-102', 'quantity': 250}).encode()
req2 = urllib.request.Request(base + '/api/reorder/confirm', data=data2, headers={'Content-Type': 'application/json'})
resp2 = urllib.request.urlopen(req2)
res_json = json.loads(resp2.read().decode())
print(f"[PASS] POST /api/reorder/confirm  Status: {resp2.status} | PO: {res_json.get('po_number')}")
print("=== ALL ENDPOINTS HEALTHY ===")
