// Order page functionality

let products = [];
let cart = {};

// Fetch products and cart
async function loadData() {
    await Promise.all([
        fetchProducts(),
        fetchCart()
    ]);
    renderOrderItems();
    updateTotal();
}

// Fetch products
async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        if (data.success) {
            products = data.products;
        }
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

// Fetch cart
async function fetchCart() {
    cart = await getCart();
}

// Render order items
function renderOrderItems() {
    const orderList = document.getElementById('orderList');
    if (!orderList) return;
    
    const cartItems = Object.entries(cart).filter(([name, qty]) => qty > 0);
    
    if (cartItems.length === 0) {
        orderList.innerHTML = `
            <div class="empty-cart">
                <h2>No items in your cart yet</h2>
                <p>Let's Go Get some Delicious Goodies</p>
            </div>
        `;
        return;
    }
    
    orderList.innerHTML = cartItems.map(([itemName, quantity]) => {
        const product = products.find(p => p.name === itemName);
        if (!product) return '';
        
        return `
            <div class="order-item">
                <img src="${product.image_url}" alt="${product.name}" class="order-item-image"
                     onerror="this.src='https://via.placeholder.com/64x64?text=No+Image'">
                <div class="order-item-info">
                    <h3 class="order-item-name">${product.name}</h3>
                    <p class="order-item-category">${product.category}</p>
                </div>
                <div class="order-item-controls">
                    <button class="quantity-button" onclick="updateQuantity('${itemName}', -1)">−</button>
                    <span class="quantity-display">${quantity}</span>
                    <button class="quantity-button" onclick="updateQuantity('${itemName}', 1)">+</button>
                </div>
            </div>
        `;
    }).join('');
}

// Update quantity
async function updateQuantity(itemName, delta) {
    await updateCartQuantity(itemName, delta);
    await fetchCart();
    renderOrderItems();
    updateTotal();
}

// Update total price
function updateTotal() {
    const totalPriceElement = document.getElementById('totalPrice');
    const orderButton = document.getElementById('orderButton');
    
    if (!totalPriceElement) return;
    
    let total = 0;
    for (const [itemName, quantity] of Object.entries(cart)) {
        const product = products.find(p => p.name === itemName);
        if (product) {
            total += product.price * quantity;
        }
    }
    
    // Add ₹10 service fee
    const finalTotal = total > 0 ? total + 10 : 0;
    totalPriceElement.textContent = formatPrice(finalTotal);
    
    if (orderButton) {
        orderButton.disabled = total === 0;
        orderButton.style.opacity = total === 0 ? '0.5' : '1';
    }
}

// Place order
async function placeOrder() {
    const total = parseFloat(document.getElementById('totalPrice').textContent);
    if (total === 0) return;
    
    await emptyCart();
    window.location.href = '/thankyou';
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    
    const orderButton = document.getElementById('orderButton');
    if (orderButton) {
        orderButton.addEventListener('click', placeOrder);
    }
});



