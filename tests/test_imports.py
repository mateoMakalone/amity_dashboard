print("Testing imports...")

try:
    print("1. Testing config import...")
    from app.config import SECTIONS, ALL_METRICS, TIME_INTERVALS
    print(f"   SECTIONS keys: {list(SECTIONS.keys())}")
    print(f"   ALL_METRICS keys: {list(ALL_METRICS.keys())[:3]}")
    print(f"   TIME_INTERVALS: {TIME_INTERVALS}")
    print("   ✓ Config imported successfully")
except Exception as e:
    print(f"   ✗ Config import failed: {e}")

try:
    print("2. Testing metrics import...")
    from app.metrics import MetricsService
    print("   ✓ Metrics imported successfully")
except Exception as e:
    print(f"   ✗ Metrics import failed: {e}")

try:
    print("3. Testing routes import...")
    from app.routes import dashboard_bp
    print("   ✓ Routes imported successfully")
except Exception as e:
    print(f"   ✗ Routes import failed: {e}")

try:
    print("4. Testing app creation...")
    from app import create_app
    app = create_app()
    print("   ✓ App created successfully")
    
    print("5. Testing routes registration...")
    routes = list(app.url_map.iter_rules())
    print(f"   Registered routes: {len(routes)}")
    for route in routes:
        print(f"     {route.rule} -> {route.endpoint}")
    
except Exception as e:
    print(f"   ✗ App creation failed: {e}")

print("Import test completed.") 