// Cart management functions

// Add item to cart
async function addToCart(itemName, quantity = 1) {
    try {
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item: itemName,
                quantity: quantity
            })
        });
        
        const data = await response.json();
        if (data.success) {
            await updateCartBadge();
            return data.cart;
        }
        return null;
    } catch (error) {
        console.error('Error adding to cart:', error);
        return null;
    }
}

// Update cart quantity
async function updateCartQuantity(itemName, delta) {
    try {
        const response = await fetch('/api/cart', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item: itemName,
                delta: delta
            })
        });
        
        const data = await response.json();
        if (data.success) {
            await updateCartBadge();
            return data.cart;
        }
        return null;
    } catch (error) {
        console.error('Error updating cart:', error);
        return null;
    }
}

// Get cart
async function getCart() {
    try {
        const response = await fetch('/api/cart');
        const data = await response.json();
        if (data.success) {
            return data.cart;
        }
        return {};
    } catch (error) {
        console.error('Error getting cart:', error);
        return {};
    }
}

// Empty cart
async function emptyCart() {
    try {
        const response = await fetch('/api/cart', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            await updateCartBadge();
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error emptying cart:', error);
        return false;
    }
}











































