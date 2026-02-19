from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sys
import os
import json

# Add the api directory to the path so we can import the agent controller
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(current_dir, '..', 'api')
sys.path.insert(0, api_dir)

# Store original working directory
original_cwd = os.getcwd()

# Initialize Flask with absolute paths
web_app_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(web_app_dir, 'templates'),
            static_folder=os.path.join(web_app_dir, 'static'))
app.secret_key = 'coffee_shop_secret_key_change_in_production'
CORS(app)

# Feature flags: control which backend is used for the chatbot.
# - USE_RUNPOD_AGENT: use original RunPod-based AgentController
# - USE_GEMINI_AGENT: use local Gemini-based GeminiAgentController
# If both are false, chatbot will be unavailable.
USE_RUNPOD_AGENT = os.getenv("USE_RUNPOD_AGENT", "false").lower() == "true"
USE_GEMINI_AGENT = os.getenv("USE_GEMINI_AGENT", "true").lower() == "true"

# Initialize AgentController (RunPod or Gemini)
agent_controller = None

if USE_RUNPOD_AGENT:
    try:
        os.chdir(api_dir)
        from agent_controller import AgentController
        agent_controller = AgentController()
        print("Using full AgentController with RunPod")
    except Exception as e:
        print(f"AgentController initialization failed: {e}")
        print("Please check your RunPod configuration and environment variables")
        agent_controller = None
    finally:
        os.chdir(original_cwd)
elif USE_GEMINI_AGENT:
    try:
        os.chdir(api_dir)
        from gemini_agent_controller import GeminiAgentController
        agent_controller = GeminiAgentController()
        print("Using GeminiAgentController (Gemini API)")
    except Exception as e:
        print(f"GeminiAgentController initialization failed: {e}")
        print("Please check your GEMINI_API_KEY and Gemini configuration")
        agent_controller = None
    finally:
        os.chdir(original_cwd)
else:
    print("No chatbot backend enabled (USE_RUNPOD_AGENT=false, USE_GEMINI_AGENT=false).")

# Initialize cart in session
@app.before_request
def init_cart():
    # Always ensure cart is a clean dict
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        session['cart'] = {}
    elif 'cart' not in session:
        session['cart'] = {}

# Routes
@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/home')
def home():
    """Home page with products"""
    return render_template('home.html')

@app.route('/chat')
def chat():
    """Chat room page"""
    return render_template('chat.html')

@app.route('/order')
def order():
    """Order/Cart page"""
    return render_template('order.html')

@app.route('/details')
def details():
    """Product details page"""
    return render_template('details.html')

@app.route('/thankyou')
def thankyou():
    """Thank you page"""
    return render_template('thankyou.html')

# API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products from Firebase or return sample data"""
    try:
        # Try to import and use Firebase if available
        firebase_url = os.getenv('FIREBASE_DATABASE_URL', '')
        firebase_cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', '')
        
        if firebase_url and firebase_cred_path:
            from firebase_admin import credentials, initialize_app, db
            
            # Initialize Firebase if not already done
            if not hasattr(app, 'firebase_initialized'):
                try:
                    cred = credentials.Certificate(firebase_cred_path)
                    initialize_app(cred, {'databaseURL': firebase_url})
                    app.firebase_initialized = True
                except Exception as e:
                    print(f"Firebase initialization failed: {e}")
                    return jsonify({
                        'products': get_sample_products(),
                        'success': True,
                        'note': 'Using sample products - Firebase initialization failed'
                    })
            
            # Fetch products from Firebase
            products_ref = db.reference('products')
            products_data = products_ref.get()
            
            products = []
            if products_data:
                for key, value in products_data.items():
                    products.append({**value, 'id': key})
            
            if products:
                return jsonify({
                    'products': products,
                    'success': True
                })
    except ImportError:
        # Firebase not installed, use sample data
        pass
    except Exception as e:
        print(f"Error fetching from Firebase: {e}")
    
    # Fallback: return sample products
    return jsonify({
        'products': get_sample_products(),
        'success': True,
        'note': 'Using sample products - Configure Firebase for real data'
    })

def get_sample_products():
    """Load all products from products.jsonl file"""
    import json
    
    products = []
    # Get the products directory path
    products_file = os.path.join(current_dir, '..', 'products', 'products.jsonl')
    images_dir = os.path.join(current_dir, '..', 'products', 'images')
    
    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, start=1):
                if line.strip():
                    product = json.loads(line.strip())
                    image_filename = product.get('image_path', '')
                    
                    # Try to serve images from local static folder or use placeholder
                    # If images are hosted elsewhere, update this logic
                    if image_filename:
                        # Check if we can serve from Flask static files
                        image_path = os.path.join(images_dir, image_filename)
                        if os.path.exists(image_path):
                            # Serve from Flask static route (we'll add this route)
                            image_url = f'/static/products/images/{image_filename}'
                        else:
                            # Use placeholder if image not found locally
                            image_url = f'https://via.placeholder.com/400x300?text={product.get("name", "Product").replace(" ", "+")}'
                    else:
                        image_url = f'https://via.placeholder.com/400x300?text={product.get("name", "Product").replace(" ", "+")}'
                    
                    products.append({
                        'id': str(idx),
                        'name': product.get('name', ''),
                        'category': product.get('category', ''),
                        'price': float(product.get('price', 0)),
                        'rating': float(product.get('rating', 0)),
                        'description': product.get('description', ''),
                        'image_url': image_url,
                        'image_path': image_filename
                    })
    except FileNotFoundError:
        print(f"Products file not found at {products_file}")
        return []
    except Exception as e:
        print(f"Error loading products: {e}")
        return []
    
    return products

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat messages"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({
                'error': 'No messages provided'
            }), 400
        
        # Use AgentController with RunPod
        if agent_controller:
            try:
                # Format input for agent controller
                input_data = {
                    "input": {
                        "messages": messages
                    }
                }
                
                # Get response from agent controller
                response = agent_controller.get_response(input_data)
                
                # Extract the assistant's message
                assistant_message = {
                    "role": response.get("role", "assistant"),
                    "content": response.get("content", "I'm sorry, I couldn't process that request."),
                    "memory": response.get("memory", {})
                }
                
                # Debug: Log the response to see if order is included
                if assistant_message.get("memory", {}).get("order"):
                    print(f"AgentController returning order: {assistant_message.get('memory').get('order')}")
                
                return jsonify({
                    'message': assistant_message,
                    'success': True
                })
            except Exception as e:
                print(f"AgentController error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'message': {
                        "role": "assistant",
                        "content": f"I'm sorry, there was an error processing your request: {str(e)}",
                        "memory": {}
                    },
                    'success': False,
                    'error': str(e)
                }), 500
        else:
            return jsonify({
                'message': {
                    "role": "assistant",
                    "content": "I'm sorry, the chatbot service is currently unavailable. Please check the server configuration.",
                    "memory": {}
                },
                'success': False,
                'error': 'AgentController not initialized'
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/cart', methods=['GET', 'POST', 'PUT', 'DELETE'])
def cart_api():
    """Cart management API"""
    if request.method == 'GET':
        return jsonify({
            'cart': session.get('cart', {}),
            'success': True
        })
    
    elif request.method == 'POST':
        data = request.json
        item_name = data.get('item')
        quantity = data.get('quantity', 1)
        
        cart = session.get('cart', {})
        # Ensure cart is a dict
        if not isinstance(cart, dict):
            cart = {}
        cart[item_name] = cart.get(item_name, 0) + quantity
        session['cart'] = cart
        
        return jsonify({
            'cart': cart,
            'success': True
        })
    
    elif request.method == 'PUT':
        data = request.json
        item_name = data.get('item')
        delta = data.get('delta', 0)
        
        cart = session.get('cart', {})
        # Ensure cart is a dict
        if not isinstance(cart, dict):
            cart = {}
        cart[item_name] = max((cart.get(item_name, 0) + delta), 0)
        if cart[item_name] == 0:
            del cart[item_name]
        session['cart'] = cart
        
        return jsonify({
            'cart': cart,
            'success': True
        })
    
    elif request.method == 'DELETE':
        session['cart'] = {}
        return jsonify({
            'cart': {},
            'success': True
        })

@app.route('/api/cart/reset', methods=['POST'])
def reset_cart():
    """Reset cart to empty - useful for debugging"""
    session['cart'] = {}
    return jsonify({
        'cart': {},
        'success': True,
        'message': 'Cart reset successfully'
    })

@app.route('/static/products/images/<filename>')
def serve_product_image(filename):
    """Serve product images from the products/images directory"""
    from flask import send_from_directory
    images_dir = os.path.join(current_dir, '..', 'products', 'images')
    return send_from_directory(images_dir, filename)


@app.route('/avatars/<filename>')
def serve_avatar(filename):
    """Serve avatar images from python_code/avatarimages directory"""
    from flask import send_from_directory
    avatars_dir = os.path.join(current_dir, '..', 'avatarimages')
    return send_from_directory(avatars_dir, filename)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Coffee Shop Web App API'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
