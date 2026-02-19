// Home page functionality

let products = [];
let categories = ['All'];
let selectedCategory = 'All';

// Fetch products
async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        if (data.success) {
            products = data.products;
            
            // Extract unique categories
            const uniqueCategories = ['All', ...new Set(products.map(p => p.category))];
            categories = uniqueCategories;
            
            renderCategories();
            renderProducts();
        }
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

// Render categories
function renderCategories() {
    const categoriesList = document.getElementById('categoriesList');
    if (!categoriesList) return;
    
    categoriesList.innerHTML = categories.map(category => {
        const isActive = category === selectedCategory;
        return `
            <button class="category-button ${isActive ? 'active' : ''}" 
                    onclick="selectCategory('${category}')">
                ${category}
            </button>
        `;
    }).join('');
}

// Select category
function selectCategory(category) {
    selectedCategory = category;
    renderCategories();
    renderProducts(); // This is now async but we don't need to await it
}

// Render products
async function renderProducts() {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;
    
    // Get current cart to show quantities
    const cart = await getCart();
    
    const filteredProducts = selectedCategory === 'All' 
        ? products 
        : products.filter(p => p.category === selectedCategory);
    
    // Store current scroll position to prevent jumping
    const scrollTop = productsGrid.scrollTop;
    
    const isInitialLoad = !productsGrid.hasAttribute('data-rendered');
    if (isInitialLoad) {
        productsGrid.setAttribute('data-rendered', 'true');
    }
    
    productsGrid.innerHTML = filteredProducts.map((product, index) => {
        const quantity = cart[product.name] || 0;
        const initialClass = isInitialLoad ? 'initial-load' : '';
        return `
        <div class="product-card ${initialClass}" 
             data-product-name="${product.name}"
             onclick="goToDetails('${product.name}', '${product.image_url}', '${product.category}', '${product.price}', '${product.rating}', '${product.description.replace(/'/g, "\\'")}')">
            <div class="product-image-wrapper">
                <img src="${product.image_url}" alt="${product.name}" class="product-image" 
                     onerror="this.src='https://via.placeholder.com/200x128?text=No+Image'">
            </div>
            <h3 class="product-name">${product.name}</h3>
            <p class="product-category">${product.category}</p>
            <div class="product-footer">
                <span class="product-price">₹${formatPrice(product.price)}</span>
                <div class="product-quantity-controls" onclick="event.stopPropagation();">
                    ${quantity > 0 ? `
                        <button class="quantity-control-btn minus-btn" onclick="updateProductQuantity('${product.name}', -1)">−</button>
                        <span class="quantity-display">${quantity}</span>
                        <button class="quantity-control-btn plus-btn" onclick="updateProductQuantity('${product.name}', 1)">+</button>
                    ` : `
                        <button class="add-to-cart-btn" onclick="updateProductQuantity('${product.name}', 1)">Add</button>
                    `}
                </div>
            </div>
        </div>
    `;
    }).join('');
    
    // Restore scroll position
    productsGrid.scrollTop = scrollTop;
}

// Go to product details
function goToDetails(name, imageUrl, category, price, rating, description) {
    const params = new URLSearchParams({
        name: name,
        image_url: imageUrl,
        category: category,
        price: price,
        rating: rating,
        description: description
    });
    window.location.href = `/details?${params.toString()}`;
}

// Update product quantity (add or subtract)
async function updateProductQuantity(productName, delta) {
    if (delta > 0) {
        await addToCart(productName, delta);
        showToast(`${productName} added to cart`);
    } else {
        await updateCartQuantity(productName, delta);
        const cart = await getCart();
        const quantity = cart[productName] || 0;
        if (quantity === 0) {
            showToast(`${productName} removed from cart`);
        }
    }
    
    // Update only the specific product card instead of re-rendering all
    await updateSingleProductCard(productName);
    
    // Update cart badge
    await updateCartBadge();
}

// Update a single product card without re-rendering all
async function updateSingleProductCard(productName) {
    const productCard = document.querySelector(`.product-card[data-product-name="${productName}"]`);
    if (!productCard) {
        // If card not found, do a full render (might be filtered out)
        await renderProducts();
        return;
    }
    
    const cart = await getCart();
    const quantity = cart[productName] || 0;
    const controlsContainer = productCard.querySelector('.product-quantity-controls');
    
    if (!controlsContainer) return;
    
    // Update the controls without re-rendering the whole card
    if (quantity > 0) {
        controlsContainer.innerHTML = `
            <button class="quantity-control-btn minus-btn" onclick="updateProductQuantity('${productName}', -1)">−</button>
            <span class="quantity-display">${quantity}</span>
            <button class="quantity-control-btn plus-btn" onclick="updateProductQuantity('${productName}', 1)">+</button>
        `;
    } else {
        controlsContainer.innerHTML = `
            <button class="add-to-cart-btn" onclick="updateProductQuantity('${productName}', 1)">Add</button>
        `;
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    await fetchProducts();
    await updateCartBadge();
});



