// Chat Assistant JavaScript
// Handles message sending, auto-scroll, loading indicators, language toggle, and error handling

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const languageSelect = document.getElementById('languageSelect');
    const welcomeMessage = document.getElementById('welcomeMessage');
    const backBtn = document.getElementById('backBtn');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const mobileHistoryToggle = document.getElementById('mobileHistoryToggle');
    const chatHistorySidebarContainer = document.getElementById('chatHistorySidebarContainer');

    // State
    let isLoading = false;
    let currentLanguage = 'en';
    let isMobileSidebarOpen = false;

    // Initialize
    init();

    function init() {
        // Load chat history
        loadChatHistory();

        // Set up event listeners
        chatForm.addEventListener('submit', handleSubmit);
        messageInput.addEventListener('input', handleInputChange);
        messageInput.addEventListener('keydown', handleKeyDown);
        languageSelect.addEventListener('change', handleLanguageChange);
        backBtn.addEventListener('click', () => window.location.href = '/home');
        
        // Clear history button
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', handleClearHistory);
        }

        // Mobile history toggle
        if (mobileHistoryToggle && chatHistorySidebarContainer) {
            mobileHistoryToggle.addEventListener('click', toggleMobileSidebar);
        }

        // Suggestion buttons
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const text = this.querySelector('span').textContent;
                messageInput.value = text;
                handleInputChange();
                messageInput.focus();
            });
        });

        // Auto-resize textarea
        messageInput.addEventListener('input', autoResizeTextarea);
    }

    // Load chat history from server
    async function loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            
            if (!response.ok) {
                throw new Error('Failed to load chat history');
            }

            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                // Hide welcome message if there's history
                if (welcomeMessage) {
                    welcomeMessage.style.display = 'none';
                }

                // Display each message in main chat
                data.messages.forEach(msg => {
                    displayMessage(msg.message, 'user', false);
                    displayMessage(msg.response, 'bot', false);
                });

                // Update sidebar with history
                updateChatHistorySidebar(data.messages);

                // Scroll to bottom
                scrollToBottom();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            showError('Failed to load chat history. Please refresh the page.');
        }
    }

    // Update chat history sidebar
    function updateChatHistorySidebar(messages) {
        const sidebar = document.getElementById('chatHistorySidebar');
        if (!sidebar) return;

        sidebar.innerHTML = '';

        if (messages.length === 0) {
            sidebar.innerHTML = '<div class="text-center text-gray-400 text-sm py-4">No chat history yet</div>';
            return;
        }

        // Group messages by session/conversation
        const sessions = {};
        messages.forEach(msg => {
            const sessionId = msg.id || msg.created_at;
            if (!sessions[sessionId]) {
                sessions[sessionId] = {
                    message: msg.message,
                    response: msg.response,
                    created_at: msg.created_at
                };
            }
        });

        // Display sessions
        Object.values(sessions).reverse().forEach((session, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'p-3 rounded-lg hover:bg-green-50 cursor-pointer transition text-sm border border-gray-100 mb-2';
            
            // Truncate message
            const preview = session.message.length > 50 ? session.message.substring(0, 50) + '...' : session.message;
            
            const date = new Date(session.created_at);
            const isToday = date.toDateString() === new Date().toDateString();
            const timeStr = isToday ? date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : date.toLocaleDateString();
            
            historyItem.innerHTML = `
                <div class="flex items-start gap-2">
                    <i class="fas fa-comment-dots text-green-600 mt-1"></i>
                    <div class="flex-1 min-w-0">
                        <div class="text-gray-700 font-medium truncate">${escapeHtml(preview)}</div>
                        <div class="text-xs text-gray-400 mt-1">${timeStr}</div>
                    </div>
                </div>
            `;
            
            // Click to scroll to message
            historyItem.addEventListener('click', () => {
                // Highlight effect
                historyItem.classList.add('bg-green-100');
                setTimeout(() => historyItem.classList.remove('bg-green-100'), 500);
            });
            
            sidebar.appendChild(historyItem);
        });
    }

    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Add single message to sidebar
    function addToSidebar(session) {
        const sidebar = document.getElementById('chatHistorySidebar');
        if (!sidebar) return;

        // Remove "no history" message if exists
        const noHistory = sidebar.querySelector('.text-center');
        if (noHistory) {
            noHistory.remove();
        }

        const historyItem = document.createElement('div');
        historyItem.className = 'p-3 rounded-lg hover:bg-green-50 cursor-pointer transition text-sm border border-gray-100 mb-2 animate-fade-in';
        
        const preview = session.message.length > 50 ? session.message.substring(0, 50) + '...' : session.message;
        const date = new Date(session.created_at);
        const timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        historyItem.innerHTML = `
            <div class="flex items-start gap-2">
                <i class="fas fa-comment-dots text-green-600 mt-1"></i>
                <div class="flex-1 min-w-0">
                    <div class="text-gray-700 font-medium truncate">${escapeHtml(preview)}</div>
                    <div class="text-xs text-gray-400 mt-1">${timeStr}</div>
                </div>
            </div>
        `;
        
        // Add to top of sidebar
        sidebar.insertBefore(historyItem, sidebar.firstChild);
    }

    // Handle clear history
    async function handleClearHistory() {
        if (!confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/api/chat/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to clear history');
            }

            // Clear sidebar
            const sidebar = document.getElementById('chatHistorySidebar');
            if (sidebar) {
                sidebar.innerHTML = '<div class="text-center text-gray-400 text-sm py-4">No chat history yet</div>';
            }

            // Clear messages
            chatMessages.innerHTML = '';
            
            // Show welcome message
            if (welcomeMessage) {
                welcomeMessage.style.display = 'block';
            }

            // Show success notification
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'bg-green-50 border border-green-200 text-green-700 px-4 py-2 rounded-lg mb-4 text-center text-sm animate-fade-in';
            notificationDiv.innerHTML = `
                <i class="fas fa-check-circle mr-2"></i>
                Chat history cleared successfully
            `;
            chatMessages.appendChild(notificationDiv);

            setTimeout(() => {
                notificationDiv.remove();
            }, 3000);

        } catch (error) {
            console.error('Error clearing history:', error);
            showError('Failed to clear chat history. Please try again.');
        }
    }

    // Toggle mobile sidebar
    function toggleMobileSidebar() {
        isMobileSidebarOpen = !isMobileSidebarOpen;
        
        if (isMobileSidebarOpen) {
            chatHistorySidebarContainer.classList.remove('hidden');
            chatHistorySidebarContainer.classList.add('mobile-sidebar-open');
            mobileHistoryToggle.innerHTML = '<i class="fas fa-times"></i>';
        } else {
            chatHistorySidebarContainer.classList.add('hidden');
            chatHistorySidebarContainer.classList.remove('mobile-sidebar-open');
            mobileHistoryToggle.innerHTML = '<i class="fas fa-history"></i>';
        }
    }

    // Handle form submission
    async function handleSubmit(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        if (!message || isLoading) return;

        // Hide welcome message on first message
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }

        // Display user message
        displayMessage(message, 'user');

        // Clear input
        messageInput.value = '';
        handleInputChange();
        autoResizeTextarea();

        // Show loading indicator
        showLoading();

        try {
            // Send message to server
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    language: currentLanguage
                })
            });

            const data = await response.json();

            if (!response.ok) {
                // Check if it's a rate limit error
                if (response.status === 429 && data.rate_limit_exceeded) {
                    const resetDate = new Date(data.reset_time * 1000);
                    const resetTime = resetDate.toLocaleTimeString();
                    throw new Error(`${data.error} Please try again after ${resetTime}.`);
                }
                throw new Error(data.error || 'Failed to send message');
            }

            // Display bot response
            displayMessage(data.response, 'bot');

            // Update sidebar with new message
            const newMessage = {
                message: message,
                response: data.response,
                created_at: new Date().toISOString()
            };
            addToSidebar(newMessage);

        } catch (error) {
            console.error('Error sending message:', error);
            showError(error.message || 'Failed to send message. Please try again.');
        } finally {
            hideLoading();
        }
    }

    // Display a message in the chat
    function displayMessage(text, sender, shouldScroll = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `max-w-[75%] rounded-2xl px-4 py-3 ${
            sender === 'user' 
                ? 'bg-gradient-to-r from-emerald-500 to-green-600 text-white' 
                : 'bg-gray-100 text-gray-800'
        }`;

        // Add icon for bot messages
        if (sender === 'bot') {
            const iconSpan = document.createElement('span');
            iconSpan.className = 'inline-block mr-2';
            iconSpan.innerHTML = '<i class="fas fa-robot text-green-600"></i>';
            bubbleDiv.appendChild(iconSpan);
        }

        // Add message text
        const textSpan = document.createElement('span');
        textSpan.className = 'text-sm leading-relaxed whitespace-pre-wrap';
        textSpan.textContent = text;
        bubbleDiv.appendChild(textSpan);

        // Add timestamp
        const timeDiv = document.createElement('div');
        timeDiv.className = `text-xs mt-1 ${sender === 'user' ? 'text-right text-green-100' : 'text-gray-500'}`;
        timeDiv.textContent = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        bubbleDiv.appendChild(timeDiv);

        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);

        if (shouldScroll) {
            scrollToBottom();
        }
    }

    // Show loading indicator
    function showLoading() {
        isLoading = true;
        loadingIndicator.classList.remove('hidden');
        sendBtn.disabled = true;
        scrollToBottom();
    }

    // Hide loading indicator
    function hideLoading() {
        isLoading = false;
        loadingIndicator.classList.add('hidden');
        sendBtn.disabled = messageInput.value.trim() === '';
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 flex items-center animate-fade-in';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle mr-2"></i>
            <span class="text-sm">${message}</span>
        `;
        chatMessages.appendChild(errorDiv);
        scrollToBottom();

        // Remove error after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 100);
    }

    // Handle input change
    function handleInputChange() {
        const hasText = messageInput.value.trim().length > 0;
        sendBtn.disabled = !hasText || isLoading;
    }

    // Handle keyboard shortcuts
    function handleKeyDown(e) {
        // Enter without Shift sends message
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    }

    // Handle language change
    function handleLanguageChange(e) {
        currentLanguage = e.target.value;
        
        // Show language change notification
        const langNames = {
            'en': 'English',
            'hi': 'हिंदी',
            'kn': 'ಕನ್ನಡ',
            'te': 'తెలుగు',
            'ta': 'தமிழ்',
            'ml': 'മലയാളം',
            'mr': 'मराठी',
            'gu': 'ગુજરાતી',
            'bn': 'বাংলা',
            'pa': 'ਪੰਜਾਬੀ'
        };

        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 rounded-lg mb-4 text-center text-sm animate-fade-in';
        notificationDiv.innerHTML = `
            <i class="fas fa-language mr-2"></i>
            Language changed to ${langNames[currentLanguage]}
        `;
        chatMessages.appendChild(notificationDiv);
        scrollToBottom();

        // Remove notification after 3 seconds
        setTimeout(() => {
            notificationDiv.remove();
        }, 3000);
    }

    // Auto-resize textarea
    function autoResizeTextarea() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }
});

// Add fade-in animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fade-in {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .animate-fade-in {
        animation: fade-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
