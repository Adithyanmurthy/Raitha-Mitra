// Simplified Authentication functionality for AI Raitha Mitra (No OTP)
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthState();
    }

    bindEvents() {
        // Navigation buttons
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const getStartedBtn = document.getElementById('getStartedBtn');
        const diseaseDetectionBtn = document.getElementById('diseaseDetectionBtn');

        // Profile buttons
        const profileBtn = document.getElementById('profileBtn');
        const viewProfileBtn = document.getElementById('viewProfileBtn');
        const changePasswordBtn = document.getElementById('changePasswordBtn');
        const predictionHistoryBtn = document.getElementById('predictionHistoryBtn');

        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                window.location.href = '/login';
            });
        }

        if (registerBtn) {
            registerBtn.addEventListener('click', () => {
                window.location.href = '/register';
            });
        }

        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', () => {
                // Check if user is logged in
                if (this.currentUser) {
                    window.location.href = '/disease-detection';
                } else {
                    window.location.href = '/register';
                }
            });
        }

        if (diseaseDetectionBtn) {
            diseaseDetectionBtn.addEventListener('click', () => {
                // Check if user is logged in
                if (this.currentUser) {
                    window.location.href = '/disease-detection';
                } else {
                    window.location.href = '/login';
                }
            });
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }

        // Profile dropdown
        if (profileBtn) {
            profileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdown = document.getElementById('profileDropdown');
                if (dropdown) {
                    // Toggle both 'hidden' and 'show' classes for compatibility
                    dropdown.classList.toggle('hidden');
                    dropdown.classList.toggle('show');
                }
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            const dropdown = document.getElementById('profileDropdown');
            if (dropdown && !dropdown.classList.contains('hidden')) {
                dropdown.classList.add('hidden');
                dropdown.classList.remove('show');
            }
        });

        // Profile menu items
        if (viewProfileBtn) {
            viewProfileBtn.addEventListener('click', () => {
                this.showProfile();
            });
        }

        if (changePasswordBtn) {
            changePasswordBtn.addEventListener('click', () => {
                this.showChangePassword();
            });
        }

        if (predictionHistoryBtn) {
            predictionHistoryBtn.addEventListener('click', () => {
                this.showPredictionHistory();
            });
        }

        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Register form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegister();
            });
        }

        // Location button
        const getLocationBtn = document.getElementById('getLocationBtn');
        if (getLocationBtn) {
            getLocationBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.getLocation();
            });
        }

        // Toggle password visibility
        const togglePassword = document.getElementById('togglePassword');
        if (togglePassword) {
            togglePassword.addEventListener('click', (e) => {
                e.preventDefault();
                const passwordInput = document.getElementById('password');
                const icon = togglePassword.querySelector('i');
                
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    passwordInput.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        }
    }

    checkAuthState() {
        // Check if user is logged in
        const token = localStorage.getItem('authToken');
        const userData = localStorage.getItem('userData');

        if (token && userData) {
            try {
                this.currentUser = JSON.parse(userData);
                this.updateUI(true);
            } catch (error) {
                console.error('Error parsing user data:', error);
                this.logout();
            }
        } else {
            this.updateUI(false);
        }
    }

    updateUI(isLoggedIn) {
        const authButtons = document.getElementById('authButtons');
        const userMenu = document.getElementById('userMenu');
        const userGreeting = document.getElementById('userGreeting');

        if (isLoggedIn && this.currentUser) {
            // Show user menu, hide auth buttons
            if (authButtons) authButtons.classList.add('hidden');
            if (userMenu) userMenu.classList.remove('hidden');
            
            // Update greeting
            if (userGreeting) {
                const name = this.currentUser.name || this.currentUser.email.split('@')[0];
                userGreeting.textContent = `Hello, ${name}`;
            }
        } else {
            // Show auth buttons, hide user menu
            if (authButtons) authButtons.classList.remove('hidden');
            if (userMenu) userMenu.classList.add('hidden');
        }
    }

    async handleLogin() {
        const emailOrMobile = document.getElementById('emailOrMobile').value;
        const password = document.getElementById('password').value;
        const submitBtn = document.getElementById('loginSubmitBtn');
        const errorDiv = document.getElementById('errorMessage');

        // Clear previous errors
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }

        // Validate inputs
        if (!emailOrMobile || !password) {
            this.showError('Please fill in all fields');
            return;
        }

        // Show loading state
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...';
            submitBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ emailOrMobile: emailOrMobile, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Store auth data
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userData', JSON.stringify(data.user));
                
                this.currentUser = data.user;
                
                // Show success message
                this.showSuccess('Login successful! Redirecting...');
                
                // Redirect after short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.showError(data.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            // Reset button
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Sign In';
                submitBtn.disabled = false;
            }
        }
    }

    async handleRegister() {
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const mobile = document.getElementById('mobile').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const location = document.getElementById('location').value;
        const submitBtn = document.getElementById('registerSubmitBtn');
        const errorDiv = document.getElementById('errorMessage');

        // Clear previous errors
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }

        // Validate inputs
        if (!name || !email || !mobile || !password || !confirmPassword || !location) {
            this.showError('Please fill in all fields');
            return;
        }

        if (password !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }

        if (password.length < 6) {
            this.showError('Password must be at least 6 characters long');
            return;
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showError('Please enter a valid email address');
            return;
        }

        // Validate mobile format (Indian mobile number)
        const mobileRegex = /^[6-9]\d{9}$/;
        if (!mobileRegex.test(mobile)) {
            this.showError('Please enter a valid 10-digit mobile number');
            return;
        }

        // Show loading state
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creating Account...';
            submitBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, mobile, password, location })
            });

            const data = await response.json();

            if (response.ok) {
                // Registration successful - no OTP needed, directly log in
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userData', JSON.stringify(data.user));
                
                this.currentUser = data.user;
                
                // Show success message
                this.showSuccess('Account created successfully! Redirecting...');
                
                // Redirect after short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.showError(data.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            // Reset button
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-user-plus mr-2"></i>Create Account';
                submitBtn.disabled = false;
            }
        }
    }

    getLocation() {
        const locationInput = document.getElementById('location');
        const getLocationBtn = document.getElementById('getLocationBtn');
        
        if (!navigator.geolocation) {
            this.showError('Geolocation is not supported by your browser');
            return;
        }

        // Update button state
        if (getLocationBtn) {
            getLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            getLocationBtn.disabled = true;
        }

        // Update input placeholder
        if (locationInput) {
            locationInput.placeholder = 'Getting location...';
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                try {
                    // Use reverse geocoding to get location name
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                    const data = await response.json();
                    
                    // Extract state or city
                    const location = data.address.state || data.address.city || data.address.county || 'Unknown Location';
                    
                    if (locationInput) {
                        locationInput.value = location;
                        locationInput.placeholder = 'Click to get current location';
                    }
                    
                    this.showSuccess(`Location detected: ${location}`);
                } catch (error) {
                    console.error('Reverse geocoding error:', error);
                    // Fallback: just use coordinates
                    if (locationInput) {
                        locationInput.value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
                    }
                    this.showSuccess('Location detected');
                }
                
                // Reset button
                if (getLocationBtn) {
                    getLocationBtn.innerHTML = '<i class="fas fa-crosshairs"></i>';
                    getLocationBtn.disabled = false;
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                let errorMessage = 'Unable to get your location';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location permission denied. Please enable location access.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out.';
                        break;
                }
                
                this.showError(errorMessage);
                
                // Reset button
                if (getLocationBtn) {
                    getLocationBtn.innerHTML = '<i class="fas fa-crosshairs"></i>';
                    getLocationBtn.disabled = false;
                }
                
                // Reset input placeholder
                if (locationInput) {
                    locationInput.placeholder = 'Click to get current location';
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    async logout() {
        try {
            // Call logout API to clear server session
            await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } catch (error) {
            console.error('Logout API error:', error);
        }
        
        // Clear stored data
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        
        this.currentUser = null;
        this.updateUI(false);
        
        // Redirect to home page
        window.location.href = '/';
    }

    async showProfile() {
        if (!this.currentUser) return;

        // Create modal HTML
        const modalHTML = `
            <div id="profileModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Profile Information</h3>
                        <button id="closeProfileModal" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Name</label>
                            <p class="mt-1 text-sm text-gray-900">${this.currentUser.name}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Email</label>
                            <p class="mt-1 text-sm text-gray-900">${this.currentUser.email}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Mobile</label>
                            <p class="mt-1 text-sm text-gray-900">${this.currentUser.mobile}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Member Since</label>
                            <p class="mt-1 text-sm text-gray-900">${new Date(this.currentUser.created_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                    
                    <div class="mt-6 flex justify-end">
                        <button id="closeProfileModalBtn" class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Bind close events
        const closeBtn = document.getElementById('closeProfileModal');
        const closeBtnBottom = document.getElementById('closeProfileModalBtn');
        const modal = document.getElementById('profileModal');

        const closeModal = () => {
            if (modal) {
                modal.remove();
            }
        };

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (closeBtnBottom) closeBtnBottom.addEventListener('click', closeModal);
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
        }
    }

    async showChangePassword() {
        // Create modal HTML
        const modalHTML = `
            <div id="changePasswordModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Change Password</h3>
                        <button id="closeChangePasswordModal" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <form id="changePasswordForm" class="space-y-4">
                        <div>
                            <label for="currentPassword" class="block text-sm font-medium text-gray-700">Current Password</label>
                            <input type="password" id="currentPassword" name="currentPassword" required
                                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500">
                        </div>
                        <div>
                            <label for="newPassword" class="block text-sm font-medium text-gray-700">New Password</label>
                            <input type="password" id="newPassword" name="newPassword" required
                                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500">
                        </div>
                        <div>
                            <label for="confirmNewPassword" class="block text-sm font-medium text-gray-700">Confirm New Password</label>
                            <input type="password" id="confirmNewPassword" name="confirmNewPassword" required
                                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500">
                        </div>
                        
                        <div id="changePasswordError" class="hidden bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
                            <span class="block sm:inline" id="changePasswordErrorText"></span>
                        </div>
                        
                        <div id="changePasswordSuccess" class="hidden bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded relative">
                            <span class="block sm:inline" id="changePasswordSuccessText"></span>
                        </div>
                        
                        <div class="flex justify-end space-x-3">
                            <button type="button" id="cancelChangePassword" class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors">
                                Cancel
                            </button>
                            <button type="submit" id="submitChangePassword" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                                Change Password
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Bind events
        const modal = document.getElementById('changePasswordModal');
        const closeBtn = document.getElementById('closeChangePasswordModal');
        const cancelBtn = document.getElementById('cancelChangePassword');
        const form = document.getElementById('changePasswordForm');

        const closeModal = () => {
            if (modal) {
                modal.remove();
            }
        };

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
        }

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleChangePassword(closeModal);
            });
        }
    }

    async handleChangePassword(closeModal) {
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmNewPassword = document.getElementById('confirmNewPassword').value;
        const submitBtn = document.getElementById('submitChangePassword');
        const errorDiv = document.getElementById('changePasswordError');
        const successDiv = document.getElementById('changePasswordSuccess');

        // Clear previous messages
        if (errorDiv) errorDiv.classList.add('hidden');
        if (successDiv) successDiv.classList.add('hidden');

        // Validate inputs
        if (!currentPassword || !newPassword || !confirmNewPassword) {
            this.showChangePasswordError('Please fill in all fields');
            return;
        }

        if (newPassword !== confirmNewPassword) {
            this.showChangePasswordError('New passwords do not match');
            return;
        }

        if (newPassword.length < 6) {
            this.showChangePasswordError('New password must be at least 6 characters long');
            return;
        }

        // Show loading state
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Changing...';
            submitBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify({ 
                    current_password: currentPassword, 
                    new_password: newPassword 
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showChangePasswordSuccess('Password changed successfully!');
                
                // Close modal after delay
                setTimeout(() => {
                    closeModal();
                }, 2000);
            } else {
                this.showChangePasswordError(data.error || 'Failed to change password');
            }
        } catch (error) {
            console.error('Change password error:', error);
            this.showChangePasswordError('Network error. Please try again.');
        } finally {
            // Reset button
            if (submitBtn) {
                submitBtn.innerHTML = 'Change Password';
                submitBtn.disabled = false;
            }
        }
    }

    async showPredictionHistory() {
        try {
            // Get user_id from current user
            const userId = this.currentUser?.id || this.currentUser?.user_id;
            if (!userId) {
                this.showError('User not logged in');
                return;
            }

            // Fetch prediction history
            const response = await fetch(`/api/predictions/history?user_id=${userId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch prediction history');
            }

            // Create modal HTML
            const modalHTML = `
                <div id="historyModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div class="bg-white rounded-lg p-6 w-full max-w-4xl mx-4 max-h-[80vh] overflow-y-auto">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-semibold text-gray-900">Prediction History</h3>
                            <button id="closeHistoryModal" class="text-gray-400 hover:text-gray-600">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        
                        <div class="space-y-4">
                            ${data.predictions.length === 0 ? 
                                '<p class="text-gray-500 text-center py-8">No predictions found. Start by detecting crop diseases!</p>' :
                                data.predictions.map(prediction => `
                                    <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors" onclick="window.authManager.showPredictionDetails(${JSON.stringify(prediction).replace(/"/g, '&quot;')})">
                                        <div class="flex justify-between items-start mb-2">
                                            <h4 class="font-medium text-gray-900">${prediction.predicted_disease}</h4>
                                            <span class="text-sm text-gray-500">${new Date(prediction.created_at).toLocaleDateString()}</span>
                                        </div>
                                        <p class="text-sm text-gray-600 mb-2">Confidence: ${(prediction.confidence * 100).toFixed(1)}%</p>
                                        ${prediction.image_path ? `<img src="${prediction.image_path}" alt="Crop image" class="w-20 h-20 object-cover rounded mb-2">` : ''}
                                        <p class="text-xs text-gray-500">Yield Impact: ${prediction.yield_impact || 'Not determined'}</p>
                                        <div class="mt-2 text-xs text-blue-600">
                                            <i class="fas fa-eye mr-1"></i>Click to view detailed treatment information
                                        </div>
                                    </div>
                                `).join('')
                            }
                        </div>
                        
                        <div class="mt-6 flex justify-end">
                            <button id="closeHistoryModalBtn" class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            `;

            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHTML);

            // Bind close events
            const closeBtn = document.getElementById('closeHistoryModal');
            const closeBtnBottom = document.getElementById('closeHistoryModalBtn');
            const modal = document.getElementById('historyModal');

            const closeModal = () => {
                if (modal) {
                    modal.remove();
                }
            };

            if (closeBtn) closeBtn.addEventListener('click', closeModal);
            if (closeBtnBottom) closeBtnBottom.addEventListener('click', closeModal);
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) closeModal();
                });
            }

        } catch (error) {
            console.error('Prediction history error:', error);
            alert('Failed to load prediction history. Please try again.');
        }
    }

    showPredictionDetails(prediction) {
        // Create detailed prediction modal
        const modalHTML = `
            <div id="predictionDetailModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-xl font-bold text-gray-900">
                            <i class="fas fa-leaf text-green-600 mr-2"></i>
                            ${prediction.predicted_disease}
                        </h3>
                        <button id="closePredictionDetail" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Left Column: Image and Basic Info -->
                        <div>
                            ${prediction.image_path ? `
                                <div class="mb-4">
                                    <img src="${prediction.image_path}" alt="Crop Disease" class="w-full h-64 object-cover rounded-lg shadow-md">
                                </div>
                            ` : `
                                <div class="mb-4 bg-gray-100 h-64 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-image text-gray-400 text-4xl"></i>
                                    <span class="ml-2 text-gray-500">No image available</span>
                                </div>
                            `}
                            
                            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h4 class="font-semibold text-blue-800 mb-2">
                                    <i class="fas fa-info-circle mr-2"></i>Prediction Details
                                </h4>
                                <div class="space-y-2 text-sm">
                                    <div class="flex justify-between">
                                        <span class="text-gray-600">Confidence:</span>
                                        <span class="font-medium text-blue-700">${(prediction.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-gray-600">Yield Impact:</span>
                                        <span class="font-medium text-blue-700">${prediction.yield_impact || 'Not determined'}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-gray-600">Date:</span>
                                        <span class="font-medium text-blue-700">${new Date(prediction.created_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Right Column: Treatment Information -->
                        <div class="space-y-4">
                            <!-- Symptoms -->
                            ${prediction.symptoms ? `
                                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                                    <h4 class="font-semibold text-red-800 mb-2">
                                        <i class="fas fa-exclamation-triangle mr-2"></i>Symptoms
                                    </h4>
                                    <div class="text-sm text-red-700 whitespace-pre-line">${prediction.symptoms}</div>
                                </div>
                            ` : ''}
                            
                            <!-- Organic Treatment -->
                            ${prediction.organic_treatment ? `
                                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                                    <h4 class="font-semibold text-green-800 mb-2">
                                        <i class="fas fa-leaf mr-2"></i>Organic Treatment
                                    </h4>
                                    <div class="text-sm text-green-700 whitespace-pre-line">${prediction.organic_treatment}</div>
                                </div>
                            ` : ''}
                            
                            <!-- Chemical Treatment -->
                            ${prediction.chemical_treatment ? `
                                <div class="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                    <h4 class="font-semibold text-orange-800 mb-2">
                                        <i class="fas fa-flask mr-2"></i>Chemical Treatment
                                    </h4>
                                    <div class="text-sm text-orange-700 whitespace-pre-line">${prediction.chemical_treatment}</div>
                                </div>
                            ` : ''}
                            
                            <!-- Prevention Tips -->
                            ${prediction.prevention_tips ? `
                                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                    <h4 class="font-semibold text-purple-800 mb-2">
                                        <i class="fas fa-shield-alt mr-2"></i>Prevention Tips
                                    </h4>
                                    <div class="text-sm text-purple-700 whitespace-pre-line">${prediction.prevention_tips}</div>
                                </div>
                            ` : ''}
                            
                            <!-- Market Prices -->
                            ${prediction.market_prices ? `
                                <div class="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                                    <h4 class="font-semibold text-indigo-800 mb-2">
                                        <i class="fas fa-chart-line mr-2"></i>Market Prices
                                    </h4>
                                    <div class="text-sm text-indigo-700 whitespace-pre-line">${prediction.market_prices}</div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="mt-6 flex justify-end space-x-3">
                        <button id="closePredictionDetailBtn" class="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400 transition-colors">
                            Close
                        </button>
                        <button onclick="window.print()" class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
                            <i class="fas fa-print mr-2"></i>Print Report
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Bind close events
        const closeBtn = document.getElementById('closePredictionDetail');
        const closeBtnBottom = document.getElementById('closePredictionDetailBtn');
        const modal = document.getElementById('predictionDetailModal');

        const closeModal = () => {
            if (modal) {
                modal.remove();
            }
        };

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (closeBtnBottom) closeBtnBottom.addEventListener('click', closeModal);
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        if (errorDiv && errorText) {
            errorText.textContent = message;
            errorDiv.classList.remove('hidden');
        }
    }

    showSuccess(message) {
        const successDiv = document.getElementById('successMessage');
        const successText = document.getElementById('successText');
        
        if (successDiv && successText) {
            successText.textContent = message;
            successDiv.classList.remove('hidden');
        }
    }

    showChangePasswordError(message) {
        const errorDiv = document.getElementById('changePasswordError');
        const errorText = document.getElementById('changePasswordErrorText');
        
        if (errorDiv && errorText) {
            errorText.textContent = message;
            errorDiv.classList.remove('hidden');
        }
    }

    showChangePasswordSuccess(message) {
        const successDiv = document.getElementById('changePasswordSuccess');
        const successText = document.getElementById('changePasswordSuccessText');
        
        if (successDiv && successText) {
            successText.textContent = message;
            successDiv.classList.remove('hidden');
        }
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.authManager = new AuthManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthManager;
}