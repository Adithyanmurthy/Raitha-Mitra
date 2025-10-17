// Notification System for Raitha Mitra
// Handles unread message counts and friend request notifications

class NotificationSystem {
    constructor() {
        this.pollingInterval = 30000; // Poll every 30 seconds
        this.intervalId = null;
        this.isLoggedIn = false;
    }

    // Initialize the notification system
    init() {
        // Check if user is logged in
        this.isLoggedIn = localStorage.getItem('userLoggedIn') === 'true';
        
        if (!this.isLoggedIn) {
            return;
        }

        // Initial fetch
        this.fetchNotifications();

        // Start polling
        this.startPolling();

        // Setup click handlers
        this.setupClickHandlers();
    }

    // Start polling for notifications
    startPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.intervalId = setInterval(() => {
            this.fetchNotifications();
        }, this.pollingInterval);
    }

    // Stop polling
    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    // Fetch notifications from the server
    async fetchNotifications() {
        try {
            // Get user data from localStorage
            const userData = localStorage.getItem('userData');
            if (!userData) {
                return;
            }

            const user = JSON.parse(userData);
            const userId = user.id || user.user_id;

            if (!userId) {
                return;
            }

            const response = await fetch(`/api/notifications/counts?user_id=${userId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch notifications');
            }

            const data = await response.json();
            this.updateNotificationBadges(data);
        } catch (error) {
            console.error('Error fetching notifications:', error);
            // Silently fail - don't disrupt user experience
        }
    }

    // Update notification badges in the UI
    updateNotificationBadges(data) {
        const { unread_messages = 0, friend_requests = 0 } = data;

        // Update desktop navigation badges
        this.updateBadge('navMessageCount', unread_messages);
        this.updateBadge('navFriendRequestCount', friend_requests);

        // Update mobile navigation badges
        this.updateBadge('mobileMessageCount', unread_messages);
        this.updateBadge('mobileFriendRequestCount', friend_requests);

        // Update page title if there are notifications
        this.updatePageTitle(unread_messages + friend_requests);

        // Store counts for other components to use
        this.storeNotificationCounts(unread_messages, friend_requests);
    }

    // Update individual badge element
    updateBadge(elementId, count) {
        const badge = document.getElementById(elementId);
        if (!badge) return;

        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    // Update page title with notification count
    updatePageTitle(totalCount) {
        const baseTitle = 'Raitha Mitra';
        if (totalCount > 0) {
            document.title = `(${totalCount}) ${baseTitle}`;
        } else {
            document.title = baseTitle;
        }
    }

    // Store notification counts in localStorage for other components
    storeNotificationCounts(messages, friendRequests) {
        localStorage.setItem('unreadMessageCount', messages);
        localStorage.setItem('friendRequestCount', friendRequests);

        // Dispatch custom event for other components to listen to
        window.dispatchEvent(new CustomEvent('notificationsUpdated', {
            detail: {
                unreadMessages: messages,
                friendRequests: friendRequests
            }
        }));
    }

    // Setup click handlers for notification badges
    setupClickHandlers() {
        // Message badge click handlers
        const messageBadges = document.querySelectorAll('#navMessageCount, #mobileMessageCount');
        messageBadges.forEach(badge => {
            badge.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.location.href = '/messages';
            });
        });

        // Friend request badge click handlers
        const friendBadges = document.querySelectorAll('#navFriendRequestCount, #mobileFriendRequestCount');
        friendBadges.forEach(badge => {
            badge.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                window.location.href = '/friends';
            });
        });
    }

    // Manual refresh method
    refresh() {
        this.fetchNotifications();
    }

    // Destroy the notification system
    destroy() {
        this.stopPolling();
    }
}

// Create global notification system instance
const notificationSystem = new NotificationSystem();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    notificationSystem.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    notificationSystem.destroy();
});

// Export for use in other modules
window.NotificationSystem = notificationSystem;
