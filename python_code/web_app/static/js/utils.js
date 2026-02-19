// Utility functions

// Format price in Indian format
function formatPrice(price) {
    const num = parseFloat(price);
    // Format with Indian number system (lakhs, crores) for large numbers
    if (num >= 10000000) {
        return (num / 10000000).toFixed(2) + 'Cr';
    } else if (num >= 100000) {
        return (num / 100000).toFixed(2) + 'L';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    // For prices under 1000, show full number
    return Math.round(num).toLocaleString('en-IN');
}

// Update cart badge
async function updateCartBadge() {
    try {
        const response = await fetch('/api/cart');
        const data = await response.json();
        if (data.success) {
            const cart = data.cart;
            const totalItems = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
            const badge = document.getElementById('cartBadge');
            if (badge) {
                badge.textContent = totalItems;
                badge.style.display = totalItems > 0 ? 'block' : 'none';
            }
        }
    } catch (error) {
        console.error('Error updating cart badge:', error);
    }
}

// Show toast notification
function showToast(message, duration = 2000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background-color: #333;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 10000;
        animation: fadeInOut ${duration}ms;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 300ms';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, duration);
}

// Add CSS for toast animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateX(-50%) translateY(20px); }
        10% { opacity: 1; transform: translateX(-50%) translateY(0); }
        90% { opacity: 1; transform: translateX(-50%) translateY(0); }
        100% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize cart badge on page load
document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();
});



