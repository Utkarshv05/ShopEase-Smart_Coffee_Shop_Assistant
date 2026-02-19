# Coffee Shop Web App - ShopEase

A complete web application replica of the React Native coffee shop app, featuring product browsing, shopping cart, and AI-powered chatbot.

## Features

- 🏠 **Landing Page** - Beautiful welcome screen with "Get Started" button
- 🛍️ **Home Page** - Product browsing with:
  - Search area with location
  - Promotional banner
  - Category filters
  - Product grid with images, prices, and add to cart
- 💬 **Chat Bot** - AI-powered customer service chatbot that can:
  - Answer questions about the coffee shop
  - Take orders through conversation
  - Provide product recommendations
  - Automatically add items to cart from orders
- 🛒 **Shopping Cart** - Full cart management with:
  - Quantity adjustments
  - Total price calculation
  - Order placement
- 📱 **Product Details** - Detailed product pages with:
  - Large product images
  - Ratings and descriptions
  - Size selection
  - Buy now functionality
- ✅ **Thank You Page** - Order confirmation

## Setup

1. **Install dependencies:**
   ```bash
   cd python_code/web_app
   pip install -r requirements.txt
   ```

2. **Set up environment variables (Optional):**
   
   **Option A: Use Google Gemini (Recommended for simple setup)**
   Create a `.env` file in the `python_code/web_app/` directory with:
   - `GEMINI_API_KEY` - Your Google Gemini API key (get from https://makersuite.google.com/app/apikey)
   - `GEMINI_MODEL` - (Optional) Model to use, defaults to "gemini-1.5-flash"
     - Available models: "gemini-1.5-flash" (fast), "gemini-1.5-pro" (more capable), "gemini-pro" (older)
   
   **Option B: Use RunPod (if you have it configured)**
   Create a `.env` file in the `python_code/api/` directory with:
   - `RUNPOD_TOKEN` - Your RunPod API token
   - `RUNPOD_CHATBOT_URL` - Your RunPod chatbot endpoint URL
   - `RUNPOD_EMBEDDING_URL` - Your RunPod embedding endpoint URL
   - `MODEL_NAME` - The model name to use
   - `FIREBASE_DATABASE_URL` - (Optional) Firebase Realtime Database URL for products
   - Other required environment variables for Pinecone, etc.
   
   **Option C: No API keys (Rule-based chatbot)**
   If you don't set up any API keys, the app will use a simple rule-based chatbot that can handle basic queries about the menu, orders, and recommendations.

3. **Run the web app:**
   ```bash
   python app.py
   ```

4. **Access the app:**
   Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
web_app/
├── app.py              # Flask application with all routes
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── templates/
│   ├── base.html      # Base template
│   ├── index.html    # Landing page
│   ├── home.html     # Home page with products
│   ├── chat.html     # Chat bot page
│   ├── order.html    # Shopping cart page
│   ├── details.html  # Product details page
│   └── thankyou.html # Thank you page
└── static/
    ├── css/
    │   └── style.css # Complete styling matching mobile app
    └── js/
        ├── utils.js  # Utility functions
        ├── cart.js   # Cart management
        ├── home.js   # Home page functionality
        ├── chat.js   # Chat functionality
        ├── order.js  # Order page functionality
        └── details.js # Product details functionality
```

## API Endpoints

### Pages
- `GET /` - Landing page
- `GET /home` - Home page with products
- `GET /chat` - Chat bot page
- `GET /order` - Shopping cart page
- `GET /details` - Product details page
- `GET /thankyou` - Thank you page

### API
- `GET /api/products` - Get all products (from Firebase or sample data)
- `POST /api/chat` - Send chat messages to the AI chatbot
- `GET /api/cart` - Get current cart
- `POST /api/cart` - Add item to cart
- `PUT /api/cart` - Update cart quantity
- `DELETE /api/cart` - Empty cart
- `GET /api/health` - Health check endpoint

## Features Matching Mobile App

✅ Landing page with "Get Started" button  
✅ Search area with location and filter button  
✅ Promotional banner  
✅ Category filtering  
✅ Product grid (2 columns on mobile, 3 on desktop)  
✅ Add to cart functionality  
✅ Shopping cart with quantity management  
✅ Product details page  
✅ Chat bot integration with RunPod  
✅ Cart badge in navigation  
✅ Bottom navigation bar  
✅ Order placement flow  
✅ Thank you page  

## Chatbot Configuration

The app supports three chatbot modes:

1. **Full Agent Controller (RunPod)** - Uses your complete agent system with GuardAgent, ClassificationAgent, etc. (requires RunPod setup) - **Currently commented out**
2. **Google Gemini Direct** - Uses Google Gemini API directly for intelligent responses (requires GEMINI_API_KEY) - **Currently active**
3. **Rule-Based Fallback** - Simple rule-based chatbot that works without any API keys

The app will automatically try each option in order and use the first one that works.

## Notes

- If Firebase is not configured, the app will load products from `products.jsonl` file
- The chatbot automatically falls back to simpler modes if RunPod is unavailable
- Cart is stored in Flask session (server-side)
- All styling matches the mobile app design with orange color (#C67C4E)
- Responsive design works on mobile and desktop
- Product images are served from the `products/images/` folder

