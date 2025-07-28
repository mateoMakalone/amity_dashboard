print("Simple Flask test...")

try:
    from flask import Flask
    
    # Create a simple test app
    app = Flask(__name__)
    
    @app.route('/test')
    def test():
        return 'Test works!'
    
    print("Simple Flask app created")
    
    with app.test_client() as client:
        response = client.get('/test')
        print(f"Test route status: {response.status_code}")
        print(f"Test route response: {response.data.decode()}")
    
except Exception as e:
    print(f"Error: {e}")

print("Simple test completed.") 