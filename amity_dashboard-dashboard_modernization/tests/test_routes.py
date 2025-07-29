from app import create_app

app = create_app()

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} -> {rule.endpoint}")

print("\nTesting endpoints...")

with app.test_client() as client:
    # Test main page
    response = client.get('/')
    print(f"GET / -> {response.status_code}")
    
    # Test dashboard_data
    response = client.get('/dashboard_data')
    print(f"GET /dashboard_data -> {response.status_code}")
    
    # Test api/sections
    response = client.get('/api/sections')
    print(f"GET /api/sections -> {response.status_code}")
    if response.status_code == 200:
        print(f"  Response: {response.get_json()}")
    
    # Test api/test
    response = client.get('/api/test')
    print(f"GET /api/test -> {response.status_code}")
    if response.status_code == 200:
        print(f"  Response: {response.get_json()}") 