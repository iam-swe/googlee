const messagesArea = document.getElementById('messagesArea');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const suggestedPrompts = document.getElementById('suggestedPrompts');

let isTyping = false;
let messageCount = 1;

const SVG_STARS = `
    <svg class="icon-stars" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
`;

const SVG_DOWNLOAD = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
    </svg>
`;

function init() {
    sendButton.addEventListener('click', async () => {
        await Chat.send();
    });
    messageInput.addEventListener('input', Input.handleChange);
    messageInput.addEventListener('keydown', Input.handleKeyPress);

    const promptButtons = document.querySelectorAll('.prompt-button');
    promptButtons.forEach(button => {
        button.addEventListener('click', async () => {
            messageInput.value = button.getAttribute('data-prompt');
            Input.handleChange();
            await Chat.send();
        });
    });

    messageInput.addEventListener('input', Input.autoResize);

    const newChatButton = document.getElementById('newChatButton');
    if (newChatButton) {
        newChatButton.addEventListener('click', async () => {
            await UI.clearChat();
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

const Chat = {
    async send() {
        const message = messageInput.value.trim();
        if (!message || isTyping) return;

        UI.addUserMessage(message);

        messageInput.value = '';
        messageInput.style.height = 'auto';
        Input.handleChange();

        messageCount++;
        if (messageCount > 1 && suggestedPrompts) {
            suggestedPrompts.style.display = 'none';
        }

        UI.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();

            UI.hideTypingIndicator();

            if (data.status === 'success') {
                UI.addAssistantMessage(data.response);

                if (data.images && data.images.length > 0) {
                    UI.addImageMessage(data.images);
                }
            } else {
                UI.addAssistantMessage(data.response || 'We\'re experiencing technical difficulties at the moment. Please try again in a few moments.');
                console.error('Error from backend:', data);
            }
        } catch (error) {
            UI.hideTypingIndicator();

            UI.addAssistantMessage('Sorry, I\'m having trouble connecting. Please check your connection and try again.');
            console.error('Network error:', error);
        }

        UI.scrollToBottom();
    }
};

const Input = {
    handleChange() {
        const hasText = messageInput.value.trim().length > 0;
        sendButton.disabled = !hasText || isTyping;
    },

    async handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled) {
                await Chat.send();
            }
        }
    },

    autoResize() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }
};

const UI = {
    addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${Utils.escapeHtml(text)}</p>
            </div>
        `;
        messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
    },

    addAssistantMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${SVG_STARS}
            </div>
            <div class="message-content">
                <p>${Utils.formatMessage(text)}</p>
            </div>
        `;
        messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
    },

    addImageMessage(images) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';

        let imagesHtml = '';
        images.forEach(({ name, versions, latest }) => {
            const latestVersion = versions[versions.length - 1];
            const fileName = `${name.replace(/\s+/g, '_')}_v${latestVersion.version}.png`;

            imagesHtml += `
                <div class="image-container" style="margin-top: 1rem;">
                    <p style="font-weight: 600; margin-bottom: 0.5rem; color: #3d2e23;">${Utils.escapeHtml(name)}</p>
                    <div class="image-wrapper">
                        <img src="${latest}" alt="${Utils.escapeHtml(name)}" />
                        <a href="${latest}" download="${fileName}" class="download-button" title="Download image">
                            ${SVG_DOWNLOAD}
                        </a>
                    </div>
                    ${versions.length > 1 ? `
                        <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #6b5444;">
                            Version ${latestVersion.version} of ${versions.length}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${SVG_STARS}
            </div>
            <div class="message-content">
                ${imagesHtml}
            </div>
        `;
        messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
    },

    showTypingIndicator() {
        isTyping = true;
        Input.handleChange();

        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                ${SVG_STARS}
            </div>
            <div class="typing-content">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesArea.appendChild(typingDiv);
        this.scrollToBottom();
    },

    hideTypingIndicator() {
        isTyping = false;
        Input.handleChange();

        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    },

    scrollToBottom() {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    },

    async clearChat() {
        messagesArea.innerHTML = '';

        this.addAssistantMessage('Hi! I\'m here to help you promote your brand. Tell me about your business, and I\'ll suggest strategies to boost your visibility and reach.');

        if (suggestedPrompts) {
            suggestedPrompts.style.display = 'block';
        }

        messageCount = 1;

        try {
            await fetch('/api/new-session', { method: 'POST' });
        } catch (error) {
            console.error('Error creating new session:', error);
        }
    }
};

const Utils = {
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatMessage(text) {
        text = this.escapeHtml(text);
        text = text.replace(/\n/g, '<br>');

        const urlRegex = /(https?:\/\/\S+)/g;
        text = text.replace(urlRegex, (match, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
        });

        return text;
    }
};
