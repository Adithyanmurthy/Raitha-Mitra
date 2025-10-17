// Privacy Settings JavaScript
// Handles location privacy settings management

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const saveBtn = document.getElementById('saveBtn');
    const locationStatus = document.getElementById('locationStatus');
    const privacyRadios = document.querySelectorAll('input[name="privacy"]');

    // Get user ID from session/localStorage
    const userId = localStorage.getItem('user_id');

    if (!userId) {
        alert('Please log in to access privacy settings');
        window.location.href = '/login';
        return;
    }

    // Initialize
    init();

    function init() {
        // Load current privacy settings
        loadPrivacySettings();

        // Event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        saveBtn.addEventListener('click', savePrivacySettings);

        // Highlight selected option
        privacyRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                // Remove highlight from all
                document.querySelectorAll('label[id^="privacy"]').forEach(label => {
                    label.classList.remove('border-green-500', 'bg-green-50');
                });
                
                // Add highlight to selected
                const selectedLabel = this.closest('label');
                selectedLabel.classList.add('border-green-500', 'bg-green-50');
            });
        });
    }

    // Load current privacy settings
    async function loadPrivacySettings() {
        try {
            const response = await fetch(`/api/privacy/location?user_id=${userId}`);
            const data = await response.json();

            if (data.success) {
                // Set current privacy level
                const currentPrivacy = data.location_privacy || 'district';
                const radio = document.querySelector(`input[name="privacy"][value="${currentPrivacy}"]`);
                if (radio) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change'));
                }

                // Update location status
                if (data.has_location) {
                    locationStatus.textContent = `Location set: ${data.location_text || 'Coordinates available'}`;
                    locationStatus.classList.remove('text-blue-700');
                    locationStatus.classList.add('text-green-700');
                } else {
                    locationStatus.textContent = 'No location set. You can set your location in the Community Map.';
                    locationStatus.classList.remove('text-green-700');
                    locationStatus.classList.add('text-blue-700');
                }
            } else {
                showError('Failed to load privacy settings');
            }
        } catch (error) {
            console.error('Error loading privacy settings:', error);
            showError('Failed to load privacy settings');
        }
    }

    // Save privacy settings
    async function savePrivacySettings() {
        try {
            // Get selected privacy level
            const selectedRadio = document.querySelector('input[name="privacy"]:checked');
            if (!selectedRadio) {
                showError('Please select a privacy level');
                return;
            }

            const privacyLevel = selectedRadio.value;

            // Show loading state
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';

            // Send update request
            const response = await fetch('/api/privacy/location', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: parseInt(userId),
                    privacy_level: privacyLevel
                })
            });

            const data = await response.json();

            if (data.success) {
                showSuccess('Privacy settings saved successfully!');
                
                // Reload settings after a short delay
                setTimeout(() => {
                    loadPrivacySettings();
                }, 1000);
            } else {
                showError(data.error || 'Failed to save privacy settings');
            }
        } catch (error) {
            console.error('Error saving privacy settings:', error);
            showError('Failed to save privacy settings');
        } finally {
            // Reset button state
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Privacy Settings';
        }
    }

    // Show success message
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.remove();
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
