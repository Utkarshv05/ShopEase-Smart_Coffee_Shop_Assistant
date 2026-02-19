// Chat page functionality

// ============================================
// HARDCODED CHAT SIMULATION FOR SCREENSHOTS
// ============================================
// Set to true to show hardcoded messages for screenshots
// Set to false to use real chat functionality
const USE_HARDCODED_CHAT = false;
// ============================================

let messages = [];

// Hardcoded chat messages - Allergy-focused conversation
const HARDCODED_MESSAGES = [
    {
        role: 'bot',
        content: "Hello! Welcome to ShopEase Coffee Shop. Before we start, do you have any food allergies or dietary restrictions I should be aware of? This helps me suggest the perfect products for you!"
    },
    {
        role: 'user',
        content: "Yes, I'm lactose intolerant. I can't have dairy products."
    },
    {
        role: 'bot',
        content: "Thank you for letting me know! I'll make sure to suggest only dairy-free options. We have several great alternatives:\n\n• Oat Milk Latte (₹415) - Made with creamy oat milk\n• Almond Milk Cappuccino (₹415) - Rich and frothy\n• Black Coffee (₹250) - Classic and dairy-free\n• Vegan Chocolate Croissant (₹330) - Made with plant-based ingredients\n\nWhich one would you like to try?"
    },
    {
        role: 'user',
        content: "The Oat Milk Latte sounds perfect! Can I also get a vegan chocolate croissant?"
    },
    {
        role: 'bot',
        content: "Excellent choices! I've added 1 Oat Milk Latte and 1 Vegan Chocolate Croissant to your cart. Both are completely dairy-free and safe for you. Your total is ₹745. Is there anything else you'd like?"
    },
    {
        role: 'user',
        content: "That's perfect, thank you for being so helpful with my dietary needs!"
    },
    {
        role: 'bot',
        content: "You're very welcome! Your health and safety are our priority. Your order is ready in your cart. Enjoy your dairy-free treats! ☕"
    }
];

// Initialize hardcoded chat messages
function initHardcodedChat() {
    if (!USE_HARDCODED_CHAT) return;
    
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Clear any existing messages
    chatMessages.innerHTML = '';
    
    // Add hardcoded messages with slight delay for natural appearance
    HARDCODED_MESSAGES.forEach((msg, index) => {
        setTimeout(() => {
            addMessageToChat(msg.role, msg.content);
            messages.push(msg);
        }, index * 300); // 300ms delay between messages
    });
    
    // Update cart badge to show items (2 items: Oat Milk Latte + Vegan Chocolate Croissant)
    setTimeout(() => {
        const badge = document.getElementById('chatCartBadge');
        if (badge) {
            badge.textContent = '2';
            badge.style.display = 'block';
        }
    }, HARDCODED_MESSAGES.length * 300);
}

// Ensure cart functions are available (loaded from cart.js and utils.js in base.html)
// These functions should be available globally:
// - addToCart(itemName, quantity)
// - emptyCart()
// - updateCartBadge()
// - showToast(message)

// Initialize chat
function initChat() {
    const chatForm = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    if (chatForm) {
        chatForm.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSendMessage();
            }
        });
    }
    
    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }
}

// Handle send message
async function handleSendMessage() {
    // Skip real functionality if using hardcoded chat
    if (USE_HARDCODED_CHAT) {
        const input = document.getElementById('messageInput');
        input.value = '';
        // Just show a toast that it's in demo mode
        if (typeof showToast !== 'undefined') {
            showToast('Demo mode: Chat is simulated for screenshots');
        }
        return;
    }
    
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    messages.push({
        role: 'user',
        content: message
    });
    
    // Display user message
    addMessageToChat('user', message);
    
    // Clear input
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: messages
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.message) {
            // Add bot message
            messages.push({
                role: data.message.role,
                content: data.message.content,
                memory: data.message.memory
            });
            
            // Display bot message
            addMessageToChat('bot', data.message.content);
            
            // Handle cart updates from order memory (same as original React Native code)
            if (data.message.memory && data.message.memory.order) {
                try {
                    console.log('Updating cart with order:', data.message.memory.order);
                    
                    // Check if cart functions are available
                    if (typeof emptyCart === 'undefined' || typeof addToCart === 'undefined') {
                        console.error('Cart functions not available! Make sure cart.js is loaded.');
                        showToast('Cart functions not available. Please refresh the page.');
                        return;
                    }
                    
                    // Empty cart first (exactly like original code)
                    await emptyCart();
                    
                    // Add all items from order to cart (exactly like original)
                    for (const item of data.message.memory.order) {
                        console.log(`Adding to cart: ${item.quantity}x ${item.item}`);
                        await addToCart(item.item, item.quantity);
                    }
                    
                    // Update cart badge (both main and chat page)
                    if (typeof updateCartBadge !== 'undefined') {
                        await updateCartBadge();
                    }
                    await updateChatCartBadge();
                    
                    // Show notification
                    if (data.message.memory.order.length > 0) {
                        const itemsText = data.message.memory.order.map(i => `${i.quantity}x ${i.item}`).join(', ');
                        if (typeof showToast !== 'undefined') {
                            showToast(`Added to cart: ${itemsText}`);
                        }
                    }
                    
                    console.log('Cart updated successfully');
                } catch (error) {
                    console.error('Error updating cart:', error);
                    showToast('Error updating cart. Please try again.');
                }
            }
        } else {
            throw new Error(data.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.', true);
    } finally {
        hideTypingIndicator();
    }
}

// Add message to chat
const USER_AVATAR_SRC = '/avatars/pngtree-social-media-cute-girls-user-avatars-png-image_3584399.png';
const BOT_AVATAR_SRC = '/avatars/pngtree-cute-and-cute-kawaii-coffee-beverage-sticker-clipart-vector-png-image_12242413.png';

function createAvatarElement(role) {
    const avatar = document.createElement('div');
    avatar.className = `message-avatar ${role}`;

    const img = document.createElement('img');
    img.className = 'avatar-image';
    img.alt = role === 'user' ? 'User avatar' : 'Coffee bot avatar';
    img.src = role === 'user' ? USER_AVATAR_SRC : BOT_AVATAR_SRC;

    avatar.appendChild(img);
    return avatar;
}

function createMessageBubble(content, isError = false) {
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (isError) {
        contentDiv.style.backgroundColor = '#fee';
        contentDiv.style.borderColor = '#fcc';
        contentDiv.style.color = '#c33';
    }
    contentDiv.textContent = content;

    return contentDiv;
}

function addMessageToChat(role, content, isError = false) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = createAvatarElement(role);
    const bubble = createMessageBubble(content, isError);

    if (role === 'user') {
        messageDiv.appendChild(bubble);
        messageDiv.appendChild(avatar);
    } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'flex';
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}

// Hide typing indicator
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// Update cart badge on chat page
async function updateChatCartBadge() {
    const badge = document.getElementById('chatCartBadge');
    if (badge && typeof updateCartBadge !== 'undefined') {
        await updateCartBadge();
        // Also update the chat page badge
        try {
            const response = await fetch('/api/cart');
            const data = await response.json();
            if (data.success) {
                const cart = data.cart;
                const totalItems = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
                badge.textContent = totalItems;
                badge.style.display = totalItems > 0 ? 'block' : 'none';
            }
        } catch (error) {
            console.error('Error updating chat cart badge:', error);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    if (USE_HARDCODED_CHAT) {
        // Initialize hardcoded chat for screenshots
        initHardcodedChat();
        // Disable input in demo mode
        const input = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        if (input) {
            input.disabled = true;
            input.placeholder = 'Demo mode: Chat is simulated';
        }
        if (sendButton) {
            sendButton.disabled = true;
            sendButton.style.opacity = '0.5';
            sendButton.style.cursor = 'not-allowed';
        }
    } else {
        // Normal chat initialization
        initChat();
        updateChatCartBadge();
    }
});
