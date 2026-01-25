/**
 * Chat functionality for Brand Boost AI chatbot
 */

// DOM elements
const messagesArea = document.getElementById('messagesArea');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const suggestedPrompts = document.getElementById('suggestedPrompts');

// State
let isTyping = false;
let messageCount = 1; // Start at 1 because we have the initial greeting message

/**
 * Initialize the chatbot
 */
function init() {
    // Event listeners
    sendButton.addEventListener('click', handleSend);
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyPress);

    // Suggested prompt buttons
    const promptButtons = document.querySelectorAll('.prompt-button');
    promptButtons.forEach(button => {
        button.addEventListener('click', () => {
            const prompt = button.getAttribute('data-prompt');
            messageInput.value = prompt;
            handleInputChange();
            handleSend();
        });
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', autoResizeTextarea);
}

/**
 * Handle input change to enable/disable send button
 */
function handleInputChange() {
    const hasText = messageInput.value.trim().length > 0;
    sendButton.disabled = !hasText || isTyping;
}

/**
 * Handle key press (Enter to send, Shift+Enter for new line)
 */
function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendButton.disabled) {
            handleSend();
        }
    }
}

/**
 * Auto-resize textarea based on content
 */
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

/**
 * Handle send message
 */
async function handleSend() {
    const message = messageInput.value.trim();
    if (!message || isTyping) return;

    // Add user message to chat
    addUserMessage(message);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    handleInputChange();

    // Increment message count and hide suggested prompts after first user message
    messageCount++;
    if (messageCount > 1 && suggestedPrompts) {
        suggestedPrompts.style.display = 'none';
    }

    // Show typing indicator
    showTypingIndicator();

    try {
        // Send message to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();

        // Hide typing indicator
        hideTypingIndicator();

        if (data.status === 'success') {
            // Add assistant message to chat
            addAssistantMessage(data.response);

            // Add images if present
            if (data.images && data.images.length > 0) {
                addImageMessage(data.images);
            }
        } else {
            // Show error message from backend
            addAssistantMessage(data.response || 'We\'re experiencing technical difficulties at the moment. Please try again in a few moments.');
            console.error('Error from backend:', data);
        }
    } catch (error) {
        // Hide typing indicator
        hideTypingIndicator();

        // Show error message
        addAssistantMessage('Sorry, I\'m having trouble connecting. Please check your connection and try again.');
        console.error('Network error:', error);
    }

    // Scroll to bottom
    scrollToBottom();
}

/**
 * Add user message to chat
 */
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    messagesArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add assistant message to chat
 */
function addAssistantMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <svg class="icon-stars" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
        </div>
        <div class="message-content">
            <p>${formatMessage(text)}</p>
        </div>
    `;
    messagesArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add image message to chat
 */
function addImageMessage(images) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';

    let imagesHtml = '';
    images.forEach(image => {
        const fileName = `${image.name.replace(/\s+/g, '_')}_v${image.versions[image.versions.length - 1].version}.png`;
        imagesHtml += `
            <div class="image-container" style="margin-top: 1rem;">
                <p style="font-weight: 600; margin-bottom: 0.5rem; color: #3d2e23;">${escapeHtml(image.name)}</p>
                <div class="image-wrapper">
                    <img src="${image.latest}" alt="${escapeHtml(image.name)}" />
                    <a href="${image.latest}" download="${fileName}" class="download-button" title="Download image">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    </a>
                </div>
                ${image.versions.length > 1 ? `
                    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #6b5444;">
                        Version ${image.versions[image.versions.length - 1].version} of ${image.versions.length}
                    </div>
                ` : ''}
            </div>
        `;
    });

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <svg class="icon-stars" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
        </div>
        <div class="message-content">
            ${imagesHtml}
        </div>
    `;
    messagesArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    isTyping = true;
    handleInputChange();

    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <svg class="icon-stars" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
        </div>
        <div class="typing-content">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    messagesArea.appendChild(typingDiv);
    scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    isTyping = false;
    handleInputChange();

    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

/**
 * Scroll to bottom of messages area
 */
function scrollToBottom() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format message text (preserve line breaks, convert URLs to links)
 */
function formatMessage(text) {
    // Escape HTML first
    text = escapeHtml(text);

    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');

    // Convert URLs to clickable links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    text = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

    return text;
}

/**
 * Load conversation history (optional)
 */
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            // Clear existing messages except the greeting
            messagesArea.innerHTML = '';

            // Re-add greeting
            addAssistantMessage('Hi! I\'m here to help you promote your brand. Tell me about your business, and I\'ll suggest strategies to boost your visibility and reach.');

            // Add history messages
            data.history.forEach(msg => {
                if (msg.role === 'user') {
                    addUserMessage(msg.content);
                } else {
                    addAssistantMessage(msg.content);
                }
            });

            // Hide suggested prompts if there are messages
            if (data.history.length > 0 && suggestedPrompts) {
                suggestedPrompts.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

/**
 * Clear conversation history
 */
async function clearHistory() {
    try {
        await fetch('/api/clear', { method: 'POST' });

        // Reset UI
        messagesArea.innerHTML = '';
        addAssistantMessage('Hi! I\'m here to help you promote your brand. Tell me about your business, and I\'ll suggest strategies to boost your visibility and reach.');

        if (suggestedPrompts) {
            suggestedPrompts.style.display = 'block';
        }

        messageCount = 1;
    } catch (error) {
        console.error('Error clearing history:', error);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Optionally load history on page load
// loadHistory();
