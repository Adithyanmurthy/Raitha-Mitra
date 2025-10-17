// Messages JavaScript
// Handles message sending, inbox updates (polling), conversation thread loading, mark as read, and user blocking

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const searchUsersBtn = document.getElementById('searchUsersBtn');
    const composeBtn = document.getElementById('composeBtn');
    const conversationsList = document.getElementById('conversationsList');
    const conversationsEmpty = document.getElementById('conversationsEmpty');
    const threadHeader = document.getElementById('threadHeader');
    const threadEmpty = document.getElementById('threadEmpty');
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const messageForm = document.getElementById('messageForm');
    const messageText = document.getElementById('messageText');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const closeThreadBtn = document.getElementById('closeThreadBtn');
    const blockUserBtn = document.getElementById('blockUserBtn');
    const unreadBadge = document.getElementById('unreadBadge');

    // Modals
    const composeModal = document.getElementById('composeModal');
    const searchModal = document.getElementById('searchModal');
    const blockModal = document.getElementById('blockModal');
    const composeForm = document.getElementById('composeForm');
    const closeComposeModal = document.getElementById('closeComposeModal');
    const cancelComposeModal = document.getElementById('cancelComposeModal');
    const closeSearchModal = document.getElementById('closeSearchModal');
    const confirmBlockBtn = document.getElementById('confirmBlockBtn');
    const cancelBlockBtn = document.getElementById('cancelBlockBtn');

    // State
    let currentThreadUserId = null;
    let selectedComposeUserId = null;
    let pollingInterval = null;
    let conversations = [];

    // Initialize
    init();

    function init() {
        // Set up event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        searchUsersBtn.addEventListener('click', openSearchModal);
        composeBtn.addEventListener('click', openComposeModal);
        closeThreadBtn.addEventListener('click', closeThread);
        blockUserBtn.addEventListener('click', openBlockModal);
        closeComposeModal.addEventListener('click', closeCompModal);
        cancelComposeModal.addEventListener('click', closeCompModal);
        closeSearchModal.addEventListener('click', closeSearchMod);
        cancelBlockBtn.addEventListener('click', closeBlockMod);
        confirmBlockBtn.addEventListener('click', confirmBlock);
        messageForm.addEventListener('submit', handleSendMessage);
        messageText.addEventListener('input', handleMessageInput);
        messageText.addEventListener('keydown', handleKeyDown);
        composeForm.addEventListener('submit', handleComposeSubmit);

        // Compose triggers
        document.querySelectorAll('.compose-trigger').forEach(btn => {
            btn.addEventListener('click', openComposeModal);
        });

        // User search
        document.getElementById('userSearch').addEventListener('input', debounce((e) => searchUsers(e.target.value), 300));
        document.getElementById('farmerSearch').addEventListener('input', debounce((e) => searchFarmers(e.target.value), 300));
        document.getElementById('clearSelection').addEventListener('click', clearUserSelection);

        // Auto-resize textarea
        messageText.addEventListener('input', autoResizeTextarea);

        // Load initial data
        loadInbox();

        // Start polling for new messages
        startPolling();
    }

    // Load inbox conversations
    async function loadInbox() {
        try {
            const response = await fetch('/api/messages/inbox');
            
            if (!response.ok) {
                throw new Error('Failed to load inbox');
            }

            const data = await response.json();
            conversations = data.conversations || [];

            displayConversations(conversations);
            updateUnreadBadge(data.unread_count || 0);

        } catch (error) {
            console.error('Error loading inbox:', error);
            showNotification('Failed to load messages', 'error');
        }
    }

    // Display conversations list
    function displayConversations(convs) {
        if (convs.length === 0) {
            conversationsEmpty.classList.remove('hidden');
            return;
        }

        conversationsEmpty.classList.add('hidden');
        conversationsList.innerHTML = '';

        convs.forEach(conv => {
            const div = document.createElement('div');
            div.className = `conversation-item p-4 border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition ${
                conv.other_user_id === currentThreadUserId ? 'bg-green-50' : ''
            }`;
            div.dataset.userId = conv.other_user_id;

            const hasUnread = conv.unread_count > 0;

            div.innerHTML = `
                <div class="flex items-start space-x-3">
                    <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-user text-green-600"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-start mb-1">
                            <h4 class="font-semibold text-gray-800 truncate ${hasUnread ? 'font-bold' : ''}">${conv.other_user_name}</h4>
                            <span class="text-xs text-gray-500 flex-shrink-0 ml-2">${formatTimeAgo(conv.last_message_time)}</span>
                        </div>
                        <p class="text-sm text-gray-600 truncate ${hasUnread ? 'font-semibold' : ''}">${conv.last_message}</p>
                        ${conv.other_user_location ? `<p class="text-xs text-gray-500 mt-1"><i class="fas fa-map-marker-alt mr-1"></i>${conv.other_user_location}</p>` : ''}
                    </div>
                    ${hasUnread ? `<span class="bg-green-600 text-white text-xs font-bold px-2 py-1 rounded-full flex-shrink-0">${conv.unread_count}</span>` : ''}
                </div>
            `;

            div.addEventListener('click', () => openThread(conv.other_user_id, conv.other_user_name, conv.other_user_location));
            conversationsList.appendChild(div);
        });
    }

    // Open message thread
    async function openThread(userId, userName, userLocation) {
        currentThreadUserId = userId;

        // Update UI
        document.getElementById('threadUserName').textContent = userName;
        document.getElementById('threadUserLocation').textContent = userLocation || 'Location not set';
        
        threadEmpty.classList.add('hidden');
        threadHeader.classList.remove('hidden');
        messagesContainer.classList.remove('hidden');
        messageInput.classList.remove('hidden');

        // Load messages
        await loadThread(userId);

        // Mark messages as read
        await markThreadAsRead(userId);

        // Update conversation list highlight
        document.querySelectorAll('.conversation-item').forEach(item => {
            if (parseInt(item.dataset.userId) === userId) {
                item.classList.add('bg-green-50');
            } else {
                item.classList.remove('bg-green-50');
            }
        });
    }

    // Load thread messages
    async function loadThread(userId) {
        try {
            const response = await fetch(`/api/messages/thread/${userId}`);
            
            if (!response.ok) {
                throw new Error('Failed to load thread');
            }

            const data = await response.json();
            displayMessages(data.messages || []);

        } catch (error) {
            console.error('Error loading thread:', error);
            showNotification('Failed to load messages', 'error');
        }
    }

    // Display messages in thread
    function displayMessages(messages) {
        messagesContainer.innerHTML = '';

        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="text-center text-gray-500">
                    <p>No messages yet. Start the conversation!</p>
                </div>
            `;
            return;
        }

        messages.forEach(msg => {
            const isSent = msg.is_sent;
            const div = document.createElement('div');
            div.className = `flex ${isSent ? 'justify-end' : 'justify-start'} animate-fade-in`;

            div.innerHTML = `
                <div class="max-w-[70%] ${isSent ? 'bg-gradient-to-r from-emerald-500 to-green-600 text-white' : 'bg-gray-100 text-gray-800'} rounded-2xl px-4 py-3">
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(msg.message_text)}</p>
                    <div class="flex items-center justify-end mt-1 space-x-2">
                        <span class="text-xs ${isSent ? 'text-green-100' : 'text-gray-500'}">${formatTime(msg.created_at)}</span>
                        ${isSent && msg.is_read ? '<i class="fas fa-check-double text-xs text-green-100"></i>' : ''}
                    </div>
                </div>
            `;

            messagesContainer.appendChild(div);
        });

        // Scroll to bottom
        scrollToBottom();
    }

    // Close thread
    function closeThread() {
        currentThreadUserId = null;
        threadHeader.classList.add('hidden');
        messagesContainer.classList.add('hidden');
        messageInput.classList.add('hidden');
        threadEmpty.classList.remove('hidden');
        messageText.value = '';

        // Remove highlights
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('bg-green-50');
        });
    }

    // Handle send message
    async function handleSendMessage(e) {
        e.preventDefault();

        const message = messageText.value.trim();
        if (!message || !currentThreadUserId) return;

        try {
            const response = await fetch('/api/messages/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    receiver_id: currentThreadUserId,
                    message_text: message
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to send message');
            }

            // Clear input
            messageText.value = '';
            handleMessageInput();
            autoResizeTextarea();

            // Reload thread
            await loadThread(currentThreadUserId);

            // Reload inbox to update conversation list
            await loadInbox();

        } catch (error) {
            console.error('Error sending message:', error);
            showNotification(error.message || 'Failed to send message', 'error');
        }
    }

    // Mark thread as read
    async function markThreadAsRead(userId) {
        try {
            // Get all unread messages in this thread
            const conv = conversations.find(c => c.other_user_id === userId);
            if (!conv || conv.unread_count === 0) return;

            // Mark as read (we'll use a simple approach - reload inbox after a delay)
            setTimeout(() => {
                loadInbox();
            }, 1000);

        } catch (error) {
            console.error('Error marking as read:', error);
        }
    }

    // Open compose modal
    function openComposeModal() {
        composeForm.reset();
        selectedComposeUserId = null;
        document.getElementById('selectedUserDiv').classList.add('hidden');
        document.getElementById('searchResults').classList.add('hidden');
        composeModal.classList.remove('hidden');
    }

    // Close compose modal
    function closeCompModal() {
        composeModal.classList.add('hidden');
        composeForm.reset();
        selectedComposeUserId = null;
    }

    // Handle compose submit
    async function handleComposeSubmit(e) {
        e.preventDefault();

        if (!selectedComposeUserId) {
            showNotification('Please select a recipient', 'error');
            return;
        }

        const message = document.getElementById('composeMessage').value.trim();
        if (!message) return;

        try {
            const response = await fetch('/api/messages/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    receiver_id: selectedComposeUserId,
                    message_text: message
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            closeCompModal();
            showNotification('Message sent successfully!', 'success');

            // Reload inbox
            await loadInbox();

            // Open the thread
            const conv = conversations.find(c => c.other_user_id === selectedComposeUserId);
            if (conv) {
                openThread(conv.other_user_id, conv.other_user_name, conv.other_user_location);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            showNotification('Failed to send message', 'error');
        }
    }

    // Search users for compose
    async function searchUsers(query) {
        if (!query || query.length < 2) {
            document.getElementById('searchResults').classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/api/friends/search?q=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error('Failed to search users');
            }

            const data = await response.json();
            displaySearchResults(data.users || []);

        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    // Display search results
    function displaySearchResults(users) {
        const searchResults = document.getElementById('searchResults');
        searchResults.innerHTML = '';

        if (users.length === 0) {
            searchResults.innerHTML = '<p class="p-3 text-sm text-gray-500">No users found</p>';
            searchResults.classList.remove('hidden');
            return;
        }

        users.forEach(user => {
            const div = document.createElement('div');
            div.className = 'p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-200 last:border-b-0';
            div.innerHTML = `
                <div class="flex items-center space-x-2">
                    <i class="fas fa-user text-green-600"></i>
                    <div>
                        <p class="font-medium text-gray-800">${user.name}</p>
                        ${user.location ? `<p class="text-xs text-gray-500">${user.location}</p>` : ''}
                    </div>
                </div>
            `;
            div.addEventListener('click', () => selectUser(user));
            searchResults.appendChild(div);
        });

        searchResults.classList.remove('hidden');
    }

    // Select user for compose
    function selectUser(user) {
        selectedComposeUserId = user.id;
        document.getElementById('selectedUserName').textContent = user.name;
        document.getElementById('selectedUserDiv').classList.remove('hidden');
        document.getElementById('searchResults').classList.add('hidden');
        document.getElementById('userSearch').value = '';
    }

    // Clear user selection
    function clearUserSelection() {
        selectedComposeUserId = null;
        document.getElementById('selectedUserDiv').classList.add('hidden');
    }

    // Open search modal
    function openSearchModal() {
        document.getElementById('farmerSearch').value = '';
        document.getElementById('farmerResults').innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-users text-4xl mb-2"></i>
                <p>Search for farmers to connect with</p>
            </div>
        `;
        searchModal.classList.remove('hidden');
    }

    // Close search modal
    function closeSearchMod() {
        searchModal.classList.add('hidden');
    }

    // Search farmers
    async function searchFarmers(query) {
        if (!query || query.length < 2) return;

        try {
            const response = await fetch(`/api/friends/search?q=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error('Failed to search farmers');
            }

            const data = await response.json();
            displayFarmerResults(data.users || []);

        } catch (error) {
            console.error('Error searching farmers:', error);
        }
    }

    // Display farmer results
    function displayFarmerResults(users) {
        const farmerResults = document.getElementById('farmerResults');
        farmerResults.innerHTML = '';

        if (users.length === 0) {
            farmerResults.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>No farmers found</p>
                </div>
            `;
            return;
        }

        users.forEach(user => {
            const div = document.createElement('div');
            div.className = 'flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition';
            div.innerHTML = `
                <div class="flex items-center space-x-3">
                    <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-green-600 text-lg"></i>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-800">${user.name}</h4>
                        ${user.location ? `<p class="text-sm text-gray-600"><i class="fas fa-map-marker-alt mr-1"></i>${user.location}</p>` : ''}
                    </div>
                </div>
                <button class="message-user-btn bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition" data-user-id="${user.id}" data-user-name="${user.name}" data-user-location="${user.location || ''}">
                    <i class="fas fa-envelope mr-2"></i>Message
                </button>
            `;

            const messageBtn = div.querySelector('.message-user-btn');
            messageBtn.addEventListener('click', () => {
                closeSearchMod();
                openThread(user.id, user.name, user.location || '');
            });

            farmerResults.appendChild(div);
        });
    }

    // Open block modal
    function openBlockModal() {
        if (!currentThreadUserId) return;
        
        const userName = document.getElementById('threadUserName').textContent;
        document.getElementById('blockUserName').textContent = userName;
        blockModal.classList.remove('hidden');
    }

    // Close block modal
    function closeBlockMod() {
        blockModal.classList.add('hidden');
    }

    // Confirm block
    async function confirmBlock() {
        if (!currentThreadUserId) return;

        try {
            const response = await fetch(`/api/messages/block/${currentThreadUserId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to block user');
            }

            closeBlockMod();
            closeThread();
            showNotification('User blocked successfully', 'success');
            await loadInbox();

        } catch (error) {
            console.error('Error blocking user:', error);
            showNotification('Failed to block user', 'error');
        }
    }

    // Start polling for new messages
    function startPolling() {
        // Poll every 10 seconds
        pollingInterval = setInterval(() => {
            loadInbox();
            
            // Reload current thread if open
            if (currentThreadUserId) {
                loadThread(currentThreadUserId);
            }
        }, 10000);
    }

    // Update unread badge
    function updateUnreadBadge(count) {
        if (count > 0) {
            unreadBadge.textContent = count;
            unreadBadge.classList.remove('hidden');
        } else {
            unreadBadge.classList.add('hidden');
        }
    }

    // Handle message input
    function handleMessageInput() {
        const hasText = messageText.value.trim().length > 0;
        sendMessageBtn.disabled = !hasText;
    }

    // Handle keyboard shortcuts
    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendMessageBtn.disabled) {
                messageForm.dispatchEvent(new Event('submit'));
            }
        }
    }

    // Auto-resize textarea
    function autoResizeTextarea() {
        messageText.style.height = 'auto';
        messageText.style.height = Math.min(messageText.scrollHeight, 120) + 'px';
    }

    // Scroll to bottom
    function scrollToBottom() {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }

    // Format time ago
    function formatTimeAgo(dateStr) {
        if (!dateStr) return '';
        
        const date = new Date(dateStr);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    // Format time
    function formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

    // Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Show notification
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-6 z-50 px-6 py-3 rounded-lg shadow-lg animate-slide-in ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
            ${message}
        `;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });
});

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
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
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
    .animate-fade-in {
        animation: fade-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
