import requests
import json

try:
    r = requests.get('http://localhost:5000/dashboard_data')
    data = r.json()
    
    print("=== Prominent metrics ===")
    for k, v in data['prominent'].items():
        if 'avg' in k:
            print(f"  {k}: {v}")
    
    print("\n=== All prominent keys ===")
    for k in data['prominent'].keys():
        print(f"  {k}")
        
    print(f"\n=== Total prominent metrics: {len(data['prominent'])} ===")
    
except Exception as e:
    print(f"Error: {e}") 