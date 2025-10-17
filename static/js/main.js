// AI Raitha Mitra - Main JavaScript File

// Global Variables
let currentLanguage = 'en';

// Language Translations
const translations = {
    en: {
        mainTitle: "Krishi Mitra AI",
        subtitle: "Upload a photo of your crop leaf to get instant AI-powered disease analysis and treatment recommendations",
        placeholderText: "Use your camera or upload an image to begin",
        useCameraBtn: "Use Camera",
        uploadImageBtn: "Upload Image",
        capturePhotoBtn: "Capture Photo",
        startOverBtn: "Start Over",
        loaderText: "Analyzing leaf & fetching market rates with Gemini...",
        analysisReport: "Analysis Report",
        detectedDisease: "Detected Disease:",
        yieldImpact: "Predicted Yield Impact:",
        marketRatesTitle: "✨ Today's Market Rates",
        symptomsTitle: "Symptoms",
        organicTitle: "Organic Treatment",
        chemicalTitle: "Chemical Treatment",
        preventionTitle: "Prevention Tips",
        newAnalysisBtn: "New Analysis",
        noMarketPrices: "Market prices not available",
        noDetails: "Details not available"
    },
    kn: {
        mainTitle: "ಕೃಷಿ ಮಿತ್ರ AI",
        subtitle: "ತ್ವರಿತ AI-ಚಾಲಿತ ರೋಗ ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ಚಿಕಿತ್ಸಾ ಶಿಫಾರಸುಗಳನ್ನು ಪಡೆಯಲು ನಿಮ್ಮ ಬೆಳೆಯ ಎಲೆಯ ಫೋಟೋವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        placeholderText: "ಪ್ರಾರಂಭಿಸಲು ನಿಮ್ಮ ಕ್ಯಾಮೆರಾವನ್ನು ಬಳಸಿ ಅಥವಾ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        useCameraBtn: "ಕ್ಯಾಮೆರಾ ಬಳಸಿ",
        uploadImageBtn: "ಚಿತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        capturePhotoBtn: "ಫೋಟೋ ತೆಗೆಯಿರಿ",
        startOverBtn: "ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ",
        loaderText: "ಎಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ ಮತ್ತು ಮಾರುಕಟ್ಟೆ ದರಗಳನ್ನು ಪಡೆಯುತ್ತಿದೆ...",
        analysisReport: "ವಿಶ್ಲೇಷಣೆ ವರದಿ",
        detectedDisease: "ಪತ್ತೆಯಾದ ರೋಗ:",
        yieldImpact: "ಅಂದಾಜು ಇಳುವರಿ ಪ್ರಭಾವ:",
        marketRatesTitle: "✨ ಇಂದಿನ ಮಾರುಕಟ್ಟೆ ದರಗಳು",
        symptomsTitle: "ರೋಗಲಕ್ಷಣಗಳು",
        organicTitle: "ಸಾವಯವ ಚಿಕಿತ್ಸೆ",
        chemicalTitle: "ರಾಸಾಯನಿಕ ಚಿಕಿತ್ಸೆ",
        preventionTitle: "ತಡೆಗಟ್ಟುವಿಕೆ ಸಲಹೆಗಳು",
        newAnalysisBtn: "ಹೊಸ ವಿಶ್ಲೇಷಣೆ",
        noMarketPrices: "ಮಾರುಕಟ್ಟೆ ದರಗಳು ಲಭ್ಯವಿಲ್ಲ",
        noDetails: "ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ"
    }
};

// Utility Functions
function updateLanguage(lang) {
    currentLanguage = lang;
    const t = translations[lang];
    
    // Update text content
    const elements = {
        'main-title': t.mainTitle,
        'subtitle': t.subtitle,
        'placeholder-text': t.placeholderText,
        'start-camera': t.useCameraBtn,
        'upload-label': t.uploadImageBtn,
        'capture-photo': t.capturePhotoBtn,
        'reset-btn': t.startOverBtn,
        'loader-text': t.loaderText,
        'analysis-report': t.analysisReport,
        'detected-disease': t.detectedDisease,
        'yield-impact': t.yieldImpact,
        'market-rates-title': t.marketRatesTitle,
        'symptoms-title': t.symptomsTitle,
        'organic-title': t.organicTitle,
        'chemical-title': t.chemicalTitle,
        'prevention-title': t.preventionTitle,
        'final-reset-btn': t.newAnalysisBtn
    };
    
    Object.entries(elements).forEach(([id, text]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = text;
    });
}

// Authentication Functions
async function checkAuthentication() {
    // First check localStorage (fast check)
    const isLoggedIn = localStorage.getItem('userLoggedIn');
    if (isLoggedIn) {
        return true;
    }
    
    // If not in localStorage, check session with backend
    try {
        const response = await fetch('/api/check-session');
        if (response.ok) {
            const data = await response.json();
            if (data.logged_in) {
                // User is logged in via session, update localStorage
                localStorage.setItem('userLoggedIn', 'true');
                const userData = {
                    id: data.user_id,
                    name: data.user_name,
                    email: data.user_email
                };
                localStorage.setItem('userData', JSON.stringify(userData));
                return true;
            }
        }
    } catch (error) {
        console.error('Session check failed:', error);
    }
    
    // Not logged in
    alert('Please login first to access disease detection');
    window.location.href = '/login?redirect=disease';
    return false;
}

function logout() {
    localStorage.removeItem('userLoggedIn');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('userData');
    window.location.href = '/home';
}

// Navigation Functions
function navigateToHome() {
    window.location.href = '/home';
}

function navigateToLogin() {
    window.location.href = '/login';
}

function navigateToRegister() {
    window.location.href = '/register';
}

function navigateToDiseaseDetection() {
    const isLoggedIn = localStorage.getItem('userLoggedIn');
    if (isLoggedIn) {
        window.location.href = '/disease-detection';
    } else {
        alert('Please login first to access disease detection');
        window.location.href = '/login?redirect=disease';
    }
}

// Form Validation Functions
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateMobile(mobile) {
    const mobileRegex = /^[6-9]\d{9}$/;
    return mobileRegex.test(mobile);
}

function validatePassword(password) {
    return password.length >= 6;
}

// API Functions
async function apiCall(endpoint, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`http://127.0.0.1:5000${endpoint}`, config);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `HTTP error! Status: ${response.status}`);
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// OTP Functions
function setupOTPInputs() {
    const otpInputs = document.querySelectorAll('.otp-input');
    otpInputs.forEach((input, index) => {
        input.addEventListener('input', function() {
            if (this.value.length === 1 && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
        });

        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && this.value === '' && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
    });
}

function getOTPValue() {
    const otpInputs = document.querySelectorAll('.otp-input');
    return Array.from(otpInputs).map(input => input.value).join('');
}

function clearOTPInputs() {
    const otpInputs = document.querySelectorAll('.otp-input');
    otpInputs.forEach(input => input.value = '');
    if (otpInputs.length > 0) otpInputs[0].focus();
}

// Location Functions
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                resolve(`${lat}, ${lon}`);
            },
            error => {
                reject(new Error('Unable to get location'));
            }
        );
    });
}

// Password Toggle Function
function setupPasswordToggle(passwordFieldId, toggleButtonId) {
    const passwordField = document.getElementById(passwordFieldId);
    const toggleButton = document.getElementById(toggleButtonId);
    
    if (passwordField && toggleButton) {
        toggleButton.addEventListener('click', function() {
            const icon = this.querySelector('i');
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordField.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    }
}

// Smooth Scrolling
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Dynamic Background Functions
function setupVideoBackground() {
    const video = document.getElementById('heroVideo');
    const videoToggle = document.getElementById('videoToggle');
    const videoIcon = document.getElementById('videoIcon');
    const videoText = document.getElementById('videoText');
    const watchDemoBtn = document.getElementById('watchDemoBtn');
    const heroBackground = document.getElementById('heroBackground');
    
    // Start background slideshow
    if (heroBackground) {
        heroBackground.classList.add('hero-slideshow');
    }
    
    // Try to load and play video
    if (video) {
        // Attempt to load video
        video.addEventListener('loadeddata', function() {
            console.log('Video loaded successfully');
            video.style.display = 'block';
            video.style.opacity = '1';
            
            video.play().then(function() {
                console.log('Video playing');
                // Hide slideshow background when video plays
                if (heroBackground) {
                    heroBackground.style.opacity = '0';
                }
            }).catch(function(error) {
                console.log('Autoplay prevented:', error);
                handleVideoError();
            });
        });
        
        video.addEventListener('error', function() {
            console.log('Video failed to load, using slideshow background');
            handleVideoError();
        });
        
        // Video toggle functionality
        if (videoToggle) {
            videoToggle.addEventListener('click', function() {
                if (video.style.display === 'none') {
                    // Try to show video
                    video.style.display = 'block';
                    video.play().then(function() {
                        video.style.opacity = '1';
                        heroBackground.style.opacity = '0';
                        videoIcon.className = 'fas fa-pause mr-2';
                        videoText.textContent = 'Pause Video';
                    }).catch(function() {
                        handleVideoError();
                    });
                } else if (video.paused) {
                    video.play();
                    video.style.opacity = '1';
                    heroBackground.style.opacity = '0';
                    videoIcon.className = 'fas fa-pause mr-2';
                    videoText.textContent = 'Pause Video';
                } else {
                    video.pause();
                    video.style.opacity = '0';
                    heroBackground.style.opacity = '1';
                    videoIcon.className = 'fas fa-play mr-2';
                    videoText.textContent = 'Play Video';
                }
            });
        }
    }
    
    function handleVideoError() {
        if (video) {
            video.style.display = 'none';
        }
        if (heroBackground) {
            heroBackground.style.opacity = '1';
        }
        if (videoToggle) {
            videoToggle.style.display = 'none';
        }
    }
    
    // Watch Demo button functionality
    if (watchDemoBtn) {
        watchDemoBtn.addEventListener('click', function() {
            // Create demo modal
            showDemoModal();
        });
    }
}

function showDemoModal() {
    const modalHTML = `
        <div id="demoModal" class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-lg w-full max-w-5xl max-h-[95vh] overflow-y-auto">
                <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                    <h3 class="text-2xl font-bold text-gray-900">Raitha Mitra Demo</h3>
                    <button id="closeDemoModal" class="text-gray-400 hover:text-gray-600 text-2xl">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-6">
                    <!-- Video Player -->
                    <div class="aspect-video bg-black rounded-lg overflow-hidden mb-6">
                        <video id="demoVideo" class="w-full h-full" controls>
                            <source src="/static/videos/demo.mp4" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    
                    <!-- Feature Highlights -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                        <div class="p-4 bg-green-50 rounded-lg">
                            <i class="fas fa-camera text-green-600 text-2xl mb-2"></i>
                            <h5 class="font-semibold text-gray-800">1. Capture</h5>
                            <p class="text-sm text-gray-600">Take a photo of your crop leaf</p>
                        </div>
                        <div class="p-4 bg-blue-50 rounded-lg">
                            <i class="fas fa-brain text-blue-600 text-2xl mb-2"></i>
                            <h5 class="font-semibold text-gray-800">2. Analyze</h5>
                            <p class="text-sm text-gray-600">AI identifies diseases instantly</p>
                        </div>
                        <div class="p-4 bg-purple-50 rounded-lg">
                            <i class="fas fa-prescription-bottle-alt text-purple-600 text-2xl mb-2"></i>
                            <h5 class="font-semibold text-gray-800">3. Treat</h5>
                            <p class="text-sm text-gray-600">Get treatment recommendations</p>
                        </div>
                    </div>
                    
                    <!-- Try It Button -->
                    <div class="mt-6 text-center">
                        <button id="startInteractiveDemo" class="bg-gradient-to-r from-emerald-500 to-green-600 text-white px-8 py-3 rounded-lg hover:from-emerald-600 hover:to-green-700 transition-all duration-300 shadow-lg hover:shadow-xl font-semibold">
                            <i class="fas fa-rocket mr-2"></i>Try It Now
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Get video element
    const demoVideo = document.getElementById('demoVideo');
    
    // Function to close modal and stop video
    function closeModal() {
        if (demoVideo) {
            demoVideo.pause();
            demoVideo.currentTime = 0;
        }
        document.getElementById('demoModal').remove();
    }
    
    // Setup modal close functionality
    document.getElementById('closeDemoModal').addEventListener('click', closeModal);
    
    // Setup interactive demo
    document.getElementById('startInteractiveDemo').addEventListener('click', function() {
        closeModal();
        // Navigate to disease detection page
        navigateToDiseaseDetection();
    });
    
    // Close on backdrop click
    document.getElementById('demoModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function escapeHandler(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('demoModal');
            if (modal) {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        }
    });
}

// Mobile Menu Toggle
function setupMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
}

// Initialize Common Functions
document.addEventListener('DOMContentLoaded', function() {
    // Setup smooth scrolling
    setupSmoothScrolling();
    
    // Setup mobile menu
    setupMobileMenu();
    
    // Setup video background if on home page
    if (window.location.pathname === '/' || window.location.pathname === '/home' || window.location.pathname.includes('home')) {
        setupVideoBackground();
    }
    
    // Setup language selector if present
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', function() {
            updateLanguage(this.value);
        });
    }
    
    // Setup OTP inputs if present
    setupOTPInputs();
    
    // Setup password toggles if present
    setupPasswordToggle('password', 'togglePassword');
    
    // Update initial language
    updateLanguage(currentLanguage);
});

// Export functions for use in other files
window.RaithaMitra = {
    checkAuthentication,
    logout,
    navigateToHome,
    navigateToLogin,
    navigateToRegister,
    navigateToDiseaseDetection,
    validateEmail,
    validateMobile,
    validatePassword,
    apiCall,
    getCurrentLocation,
    getOTPValue,
    clearOTPInputs,
    updateLanguage,
    setupPasswordToggle: setupPasswordToggle
};