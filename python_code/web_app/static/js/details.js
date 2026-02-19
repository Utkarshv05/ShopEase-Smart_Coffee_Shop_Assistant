// Product details page functionality

// Load product details from URL parameters
function loadProductDetails() {
    const params = new URLSearchParams(window.location.search);
    
    const name = params.get('name');
    const imageUrl = params.get('image_url');
    const category = params.get('category');
    const price = params.get('price');
    const rating = params.get('rating');
    const description = params.get('description');
    
    if (!name) {
        window.location.href = '/home';
        return;
    }
    
    // Set product image
    const imageContainer = document.getElementById('productImageContainer');
    if (imageContainer) {
        imageContainer.innerHTML = `
            <img src="${imageUrl}" alt="${name}" class="product-image-large"
                 onerror="this.src='https://via.placeholder.com/400x300?text=No+Image'">
        `;
    }
    
    // Set product info
    const productName = document.getElementById('productName');
    if (productName) productName.textContent = name;
    
    const productCategory = document.getElementById('productCategory');
    if (productCategory) productCategory.textContent = category;
    
    const productRating = document.getElementById('productRating');
    if (productRating) {
        const ratingValue = parseFloat(rating) || 0;
        const fullStars = Math.floor(ratingValue);
        const hasHalfStar = ratingValue % 1 >= 0.5;
        
        let starsHTML = '';
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<span class="star">★</span>';
        }
        if (hasHalfStar) {
            starsHTML += '<span class="star">☆</span>';
        }
        for (let i = fullStars + (hasHalfStar ? 1 : 0); i < 5; i++) {
            starsHTML += '<span class="star" style="color: #d1d5db;">★</span>';
        }
        productRating.innerHTML = starsHTML;
    }
    
    const productDescription = document.getElementById('productDescription');
    if (productDescription) productDescription.textContent = description;
    
    const productPrice = document.getElementById('productPrice');
    if (productPrice) productPrice.textContent = formatPrice(price);
}

// Handle size selection
function initSizeSelection() {
    const sizeOptions = document.querySelectorAll('.size-option');
    sizeOptions.forEach(option => {
        option.addEventListener('click', () => {
            sizeOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
        });
    });
}

// Handle buy now
async function handleBuyNow() {
    const params = new URLSearchParams(window.location.search);
    const name = params.get('name');
    
    if (name) {
        await addToCart(name, 1);
        showToast(`${name} added to cart`);
        // Go back to home
        setTimeout(() => {
            window.location.href = '/home';
        }, 500);
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadProductDetails();
    initSizeSelection();
    
    const buyNowButton = document.getElementById('buyNowButton');
    if (buyNowButton) {
        buyNowButton.addEventListener('click', handleBuyNow);
    }
});











































