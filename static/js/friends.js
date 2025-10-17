// Friends Network JavaScript
// Handles friend request sending, acceptance/decline, friend removal, friend search, and suggested connections

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const searchFarmersBtn = document.getElementById('searchFarmersBtn');
    const friendsTab = document.getElementById('friendsTab');
    const suggestionsTab = document.getElementById('suggestionsTab');
    const friendsContent = document.getElementById('friendsContent');
    const suggestionsContent = document.getElementById('suggestionsContent');
    const friendsGrid = document.getElementById('friendsGrid');
    const friendsEmpty = document.getElementById('friendsEmpty');
    const suggestionsGrid = document.getElementById('suggestionsGrid');
    const suggestionsEmpty = document.getElementById('suggestionsEmpty');
    const requestsSection = document.getElementById('requestsSection');
    const requestsList = document.getElementById('requestsList');
    const toggleRequests = document.getElementById('toggleRequests');
    const friendRequestBadge = document.getElementById('friendRequestBadge');
    const requestCount = document.getElementById('requestCount');
    const friendsCount = document.getElementById('friendsCount');
    const friendsSearchInput = document.getElementById('friendsSearchInput');

    // Modals
    const profileModal = document.getElementById('profileModal');
    const searchModal = document.getElementById('searchModal');
    const removeModal = document.getElementById('removeModal');
    const closeProfileModal = document.getElementById('closeProfileModal');
    const closeSearchModal = document.getElementById('closeSearchModal');
    const confirmRemoveBtn = document.getElementById('confirmRemoveBtn');
    const cancelRemoveBtn = document.getElementById('cancelRemoveBtn');
    const searchInput = document.getElementById('searchInput');
    const locationFilter = document.getElementById('locationFilter');
    const cropFilter = document.getElementById('cropFilter');

    // State
    let friends = [];
    let suggestions = [];
    let requests = [];
    let currentRemoveFriendId = null;
    let currentTab = 'friends';

    // Initialize
    init();

    function init() {
        // Set up event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        searchFarmersBtn.addEventListener('click', openSearchModal);
        friendsTab.addEventListener('click', () => switchTab('friends'));
        suggestionsTab.addEventListener('click', () => switchTab('suggestions'));
        toggleRequests.addEventListener('click', toggleRequestsSection);
        closeProfileModal.addEventListener('click', closeProfileMod);
        closeSearchModal.addEventListener('click', closeSearchMod);
        cancelRemoveBtn.addEventListener('click', closeRemoveMod);
        confirmRemoveBtn.addEventListener('click', confirmRemoveFriend);
        friendsSearchInput.addEventListener('input', debounce(filterFriends, 300));
        searchInput.addEventListener('input', debounce(performSearch, 300));
        locationFilter.addEventListener('change', performSearch);
        cropFilter.addEventListener('change', performSearch);

        // Search farmers triggers
        document.querySelectorAll('.search-farmers-trigger').forEach(btn => {
            btn.addEventListener('click', openSearchModal);
        });

        // Load initial data
        loadFriends();
        loadFriendRequests();
        loadSuggestions();
    }

    // Switch tabs
    function switchTab(tab) {
        currentTab = tab;

        if (tab === 'friends') {
            friendsTab.classList.add('text-green-600', 'border-b-2', 'border-green-600');
            friendsTab.classList.remove('text-gray-600');
            suggestionsTab.classList.remove('text-green-600', 'border-b-2', 'border-green-600');
            suggestionsTab.classList.add('text-gray-600');
            friendsContent.classList.remove('hidden');
            suggestionsContent.classList.add('hidden');
        } else {
            suggestionsTab.classList.add('text-green-600', 'border-b-2', 'border-green-600');
            suggestionsTab.classList.remove('text-gray-600');
            friendsTab.classList.remove('text-green-600', 'border-b-2', 'border-green-600');
            friendsTab.classList.add('text-gray-600');
            suggestionsContent.classList.remove('hidden');
            friendsContent.classList.add('hidden');
        }
    }

    // Load friends list
    async function loadFriends() {
        try {
            const response = await fetch('/api/friends/list');
            
            if (!response.ok) {
                throw new Error('Failed to load friends');
            }

            const data = await response.json();
            friends = data.friends || [];

            displayFriends(friends);
            friendsCount.textContent = `(${friends.length})`;

        } catch (error) {
            console.error('Error loading friends:', error);
            showNotification('Failed to load friends', 'error');
        }
    }

    // Display friends
    function displayFriends(friendsList) {
        friendsGrid.innerHTML = '';

        if (friendsList.length === 0) {
            friendsEmpty.classList.remove('hidden');
            return;
        }

        friendsEmpty.classList.add('hidden');

        friendsList.forEach(friend => {
            const card = createFriendCard(friend);
            friendsGrid.appendChild(card);
        });
    }

    // Create friend card
    function createFriendCard(friend) {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300';

        card.innerHTML = `
            <div class="text-center mb-4">
                <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i class="fas fa-user text-green-600 text-3xl"></i>
                </div>
                <h4 class="font-bold text-gray-800 text-lg mb-1">${friend.name}</h4>
                <p class="text-sm text-gray-600">
                    <i class="fas fa-map-marker-alt mr-1"></i>${friend.location || 'Location not set'}
                </p>
            </div>

            <div class="space-y-2 mb-4">
                ${friend.crops ? `
                    <div class="bg-green-50 rounded-lg p-2 text-center">
                        <p class="text-xs text-gray-600">Crops</p>
                        <p class="text-sm font-semibold text-green-700">${friend.crops}</p>
                    </div>
                ` : ''}
                ${friend.mutual_friends ? `
                    <div class="bg-blue-50 rounded-lg p-2 text-center">
                        <p class="text-xs text-gray-600">Mutual Friends</p>
                        <p class="text-sm font-semibold text-blue-700">${friend.mutual_friends}</p>
                    </div>
                ` : ''}
            </div>

            <div class="flex space-x-2">
                <button class="view-profile-btn flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition text-sm font-semibold" data-friend-id="${friend.id}">
                    <i class="fas fa-user mr-1"></i>Profile
                </button>
                <button class="message-friend-btn flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition text-sm font-semibold" data-friend-id="${friend.id}" data-friend-name="${friend.name}">
                    <i class="fas fa-envelope mr-1"></i>Message
                </button>
                <button class="remove-friend-btn bg-red-600 text-white px-3 py-2 rounded-lg hover:bg-red-700 transition text-sm" data-friend-id="${friend.id}" data-friend-name="${friend.name}">
                    <i class="fas fa-user-times"></i>
                </button>
            </div>
        `;

        // Add event listeners
        card.querySelector('.view-profile-btn').addEventListener('click', () => viewProfile(friend.id));
        card.querySelector('.message-friend-btn').addEventListener('click', () => messageFriend(friend.id, friend.name));
        card.querySelector('.remove-friend-btn').addEventListener('click', () => openRemoveModal(friend.id, friend.name));

        return card;
    }

    // Filter friends
    function filterFriends() {
        const query = friendsSearchInput.value.toLowerCase().trim();
        
        if (!query) {
            displayFriends(friends);
            return;
        }

        const filtered = friends.filter(friend => 
            friend.name.toLowerCase().includes(query) ||
            (friend.location && friend.location.toLowerCase().includes(query)) ||
            (friend.crops && friend.crops.toLowerCase().includes(query))
        );

        displayFriends(filtered);
    }

    // Load friend requests
    async function loadFriendRequests() {
        try {
            const response = await fetch('/api/friends/requests');
            
            if (!response.ok) {
                throw new Error('Failed to load friend requests');
            }

            const data = await response.json();
            requests = data.requests || [];

            displayFriendRequests(requests);
            updateRequestBadge(requests.length);

        } catch (error) {
            console.error('Error loading friend requests:', error);
        }
    }

    // Display friend requests
    function displayFriendRequests(reqs) {
        if (reqs.length === 0) {
            requestsSection.classList.add('hidden');
            return;
        }

        requestsSection.classList.remove('hidden');
        requestCount.textContent = `(${reqs.length})`;
        requestsList.innerHTML = '';

        reqs.forEach(req => {
            const card = document.createElement('div');
            card.className = 'bg-white rounded-lg p-4 border border-orange-200';

            card.innerHTML = `
                <div class="flex items-center space-x-3 mb-3">
                    <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-green-600 text-lg"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-800">${req.name}</h4>
                        <p class="text-xs text-gray-600">${req.location || 'Location not set'}</p>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button class="accept-request-btn flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition text-sm font-semibold" data-request-id="${req.request_id}">
                        <i class="fas fa-check mr-1"></i>Accept
                    </button>
                    <button class="decline-request-btn flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition text-sm font-semibold" data-request-id="${req.request_id}">
                        <i class="fas fa-times mr-1"></i>Decline
                    </button>
                </div>
            `;

            // Add event listeners
            card.querySelector('.accept-request-btn').addEventListener('click', () => acceptRequest(req.request_id));
            card.querySelector('.decline-request-btn').addEventListener('click', () => declineRequest(req.request_id));

            requestsList.appendChild(card);
        });
    }

    // Toggle requests section
    function toggleRequestsSection() {
        const icon = toggleRequests.querySelector('i');
        if (requestsList.classList.contains('hidden')) {
            requestsList.classList.remove('hidden');
            icon.className = 'fas fa-chevron-up';
        } else {
            requestsList.classList.add('hidden');
            icon.className = 'fas fa-chevron-down';
        }
    }

    // Update request badge
    function updateRequestBadge(count) {
        if (count > 0) {
            friendRequestBadge.textContent = count;
            friendRequestBadge.classList.remove('hidden');
        } else {
            friendRequestBadge.classList.add('hidden');
        }
    }

    // Accept friend request
    async function acceptRequest(requestId) {
        try {
            const response = await fetch(`/api/friends/accept/${requestId}`, {
                method: 'PUT'
            });

            if (!response.ok) {
                throw new Error('Failed to accept request');
            }

            showNotification('Friend request accepted!', 'success');
            await loadFriendRequests();
            await loadFriends();

        } catch (error) {
            console.error('Error accepting request:', error);
            showNotification('Failed to accept request', 'error');
        }
    }

    // Decline friend request
    async function declineRequest(requestId) {
        try {
            const response = await fetch(`/api/friends/decline/${requestId}`, {
                method: 'PUT'
            });

            if (!response.ok) {
                throw new Error('Failed to decline request');
            }

            showNotification('Friend request declined', 'info');
            await loadFriendRequests();

        } catch (error) {
            console.error('Error declining request:', error);
            showNotification('Failed to decline request', 'error');
        }
    }

    // Load suggestions
    async function loadSuggestions() {
        try {
            const response = await fetch('/api/friends/suggestions');
            
            if (!response.ok) {
                throw new Error('Failed to load suggestions');
            }

            const data = await response.json();
            suggestions = data.suggestions || [];

            displaySuggestions(suggestions);

        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    }

    // Display suggestions
    function displaySuggestions(suggs) {
        suggestionsGrid.innerHTML = '';

        if (suggs.length === 0) {
            suggestionsEmpty.classList.remove('hidden');
            return;
        }

        suggestionsEmpty.classList.add('hidden');

        suggs.forEach(sugg => {
            const card = createSuggestionCard(sugg);
            suggestionsGrid.appendChild(card);
        });
    }

    // Create suggestion card
    function createSuggestionCard(sugg) {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300';

        card.innerHTML = `
            <div class="text-center mb-4">
                <div class="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i class="fas fa-user text-purple-600 text-3xl"></i>
                </div>
                <h4 class="font-bold text-gray-800 text-lg mb-1">${sugg.name}</h4>
                <p class="text-sm text-gray-600">
                    <i class="fas fa-map-marker-alt mr-1"></i>${sugg.location || 'Location not set'}
                </p>
            </div>

            <div class="space-y-2 mb-4">
                ${sugg.reason ? `
                    <div class="bg-purple-50 rounded-lg p-2">
                        <p class="text-xs text-purple-700">
                            <i class="fas fa-lightbulb mr-1"></i>${sugg.reason}
                        </p>
                    </div>
                ` : ''}
                ${sugg.mutual_friends ? `
                    <div class="bg-blue-50 rounded-lg p-2 text-center">
                        <p class="text-xs text-gray-600">Mutual Friends</p>
                        <p class="text-sm font-semibold text-blue-700">${sugg.mutual_friends}</p>
                    </div>
                ` : ''}
            </div>

            <button class="send-request-btn w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white py-2 rounded-lg hover:from-purple-600 hover:to-pink-700 transition font-semibold" data-user-id="${sugg.id}">
                <i class="fas fa-user-plus mr-2"></i>Add Friend
            </button>
        `;

        // Add event listener
        card.querySelector('.send-request-btn').addEventListener('click', () => sendFriendRequest(sugg.id));

        return card;
    }

    // Send friend request
    async function sendFriendRequest(userId) {
        try {
            const response = await fetch(`/api/friends/request/${userId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to send request');
            }

            showNotification('Friend request sent!', 'success');
            await loadSuggestions();

        } catch (error) {
            console.error('Error sending request:', error);
            showNotification(error.message || 'Failed to send request', 'error');
        }
    }

    // Open search modal
    function openSearchModal() {
        searchInput.value = '';
        locationFilter.value = '';
        cropFilter.value = '';
        document.getElementById('searchResults').innerHTML = `
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

    // Perform search
    async function performSearch() {
        const query = searchInput.value.trim();
        const location = locationFilter.value;
        const crop = cropFilter.value;

        if (!query && !location && !crop) return;

        try {
            const params = new URLSearchParams();
            if (query) params.append('q', query);
            if (location) params.append('location', location);
            if (crop) params.append('crop', crop);

            const response = await fetch(`/api/friends/search?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error('Failed to search');
            }

            const data = await response.json();
            displaySearchResults(data.users || []);

        } catch (error) {
            console.error('Error searching:', error);
            showNotification('Failed to search', 'error');
        }
    }

    // Display search results
    function displaySearchResults(users) {
        const searchResults = document.getElementById('searchResults');
        searchResults.innerHTML = '';

        if (users.length === 0) {
            searchResults.innerHTML = `
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
                        <p class="text-sm text-gray-600">${user.location || 'Location not set'}</p>
                        ${user.is_friend ? '<span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Friend</span>' : ''}
                        ${user.request_pending ? '<span class="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">Request Pending</span>' : ''}
                    </div>
                </div>
                ${!user.is_friend && !user.request_pending ? `
                    <button class="send-request-search-btn bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm font-semibold" data-user-id="${user.id}">
                        <i class="fas fa-user-plus mr-1"></i>Add Friend
                    </button>
                ` : ''}
            `;

            if (!user.is_friend && !user.request_pending) {
                const btn = div.querySelector('.send-request-search-btn');
                btn.addEventListener('click', () => sendFriendRequest(user.id));
            }

            searchResults.appendChild(div);
        });
    }

    // View profile
    function viewProfile(friendId) {
        const friend = friends.find(f => f.id === friendId);
        if (!friend) return;

        document.getElementById('profileName').textContent = friend.name;
        document.getElementById('profileLocation').textContent = friend.location || 'Location not set';
        document.getElementById('profileCrops').textContent = friend.crops || 'Not specified';
        document.getElementById('profileJoined').textContent = friend.joined || 'Unknown';
        document.getElementById('profileMutual').textContent = friend.mutual_friends || '0';

        const profileActions = document.getElementById('profileActions');
        profileActions.innerHTML = `
            <button class="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold" onclick="window.location.href='/messages?user=${friendId}'">
                <i class="fas fa-envelope mr-2"></i>Send Message
            </button>
            <button class="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 transition font-semibold" data-friend-id="${friendId}" data-friend-name="${friend.name}">
                <i class="fas fa-user-times mr-2"></i>Remove Friend
            </button>
        `;

        profileActions.querySelector('button[data-friend-id]').addEventListener('click', function() {
            closeProfileMod();
            openRemoveModal(this.dataset.friendId, this.dataset.friendName);
        });

        profileModal.classList.remove('hidden');
    }

    // Close profile modal
    function closeProfileMod() {
        profileModal.classList.add('hidden');
    }

    // Message friend
    function messageFriend(friendId, friendName) {
        window.location.href = `/messages?user=${friendId}`;
    }

    // Open remove modal
    function openRemoveModal(friendId, friendName) {
        currentRemoveFriendId = friendId;
        document.getElementById('removeFriendName').textContent = friendName;
        removeModal.classList.remove('hidden');
    }

    // Close remove modal
    function closeRemoveMod() {
        removeModal.classList.add('hidden');
        currentRemoveFriendId = null;
    }

    // Confirm remove friend
    async function confirmRemoveFriend() {
        if (!currentRemoveFriendId) return;

        try {
            const response = await fetch(`/api/friends/remove/${currentRemoveFriendId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to remove friend');
            }

            closeRemoveMod();
            showNotification('Friend removed', 'info');
            await loadFriends();

        } catch (error) {
            console.error('Error removing friend:', error);
            showNotification('Failed to remove friend', 'error');
        }
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
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
