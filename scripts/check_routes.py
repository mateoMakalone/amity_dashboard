#!/usr/bin/env python3

print("Checking Flask routes...")

try:
    from app import create_app
    
    app = create_app()
    
    print(f"App created successfully")
    print(f"Registered routes:")
    
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")
    
    # Test specific routes
    with app.test_client() as client:
        print("\nTesting routes:")
        
        # Test main page
        response = client.get('/')
        print(f"  GET / -> {response.status_code}")
        
        # Test api/sections
        response = client.get('/api/sections')
        print(f"  GET /api/sections -> {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"    Response keys: {list(data.keys())}")
        
        # Test api/test
        response = client.get('/api/test')
        print(f"  GET /api/test -> {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"    Response: {data}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 