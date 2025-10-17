// Community Map JavaScript
// Handles Leaflet.js initialization, marker clustering, region click handlers, filters, nearby farmers, and privacy settings

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const myLocationBtn = document.getElementById('myLocationBtn');
    const privacySettingsBtn = document.getElementById('privacySettingsBtn');
    const applyFilters = document.getElementById('applyFilters');
    const clearFilters = document.getElementById('clearFilters');
    const cropFilter = document.getElementById('cropFilter');
    const languageFilter = document.getElementById('languageFilter');
    const activityFilter = document.getElementById('activityFilter');
    const radiusSelect = document.getElementById('radiusSelect');
    const regionPanel = document.getElementById('regionPanel');
    const closeRegionPanel = document.getElementById('closeRegionPanel');
    const privacyModal = document.getElementById('privacyModal');
    const privacyForm = document.getElementById('privacyForm');
    const closePrivacyModal = document.getElementById('closePrivacyModal');
    const cancelPrivacyModal = document.getElementById('cancelPrivacyModal');

    // State
    let map = null;
    let markerClusterGroup = null;
    let currentFilters = {
        crop: '',
        language: '',
        activity: ''
    };
    let userLocation = null;
    let farmerData = [];

    // Initialize
    init();

    function init() {
        // Set up event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        myLocationBtn.addEventListener('click', goToMyLocation);
        privacySettingsBtn.addEventListener('click', openPrivacyModal);
        applyFilters.addEventListener('click', applyMapFilters);
        clearFilters.addEventListener('click', clearMapFilters);
        radiusSelect.addEventListener('change', loadNearbyFarmers);
        closeRegionPanel.addEventListener('click', closeRegPanel);
        closePrivacyModal.addEventListener('click', closePrivMod);
        cancelPrivacyModal.addEventListener('click', closePrivMod);
        privacyForm.addEventListener('submit', handlePrivacySubmit);

        // Initialize map
        initializeMap();

        // Load data
        loadMapData();
        loadNetworkStats();
        loadNearbyFarmers();
    }

    // Initialize Leaflet map
    function initializeMap() {
        // Create map centered on India
        map = L.map('map').setView([20.5937, 78.9629], 5);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);

        // Initialize marker cluster group
        markerClusterGroup = L.markerClusterGroup({
            chunkedLoading: true,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true,
            iconCreateFunction: function(cluster) {
                const count = cluster.getChildCount();
                let className = 'marker-cluster-';
                
                if (count >= 50) {
                    className += 'large';
                } else if (count >= 10) {
                    className += 'medium';
                } else {
                    className += 'small';
                }

                return L.divIcon({
                    html: `<div><span>${count}</span></div>`,
                    className: 'marker-cluster ' + className,
                    iconSize: L.point(40, 40)
                });
            }
        });

        map.addLayer(markerClusterGroup);

        // Add custom CSS for markers
        addMarkerStyles();
    }

    // Add marker styles
    function addMarkerStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .marker-cluster {
                background-clip: padding-box;
                border-radius: 20px;
            }
            .marker-cluster div {
                width: 30px;
                height: 30px;
                margin-left: 5px;
                margin-top: 5px;
                text-align: center;
                border-radius: 15px;
                font: 12px "Helvetica Neue", Arial, Helvetica, sans-serif;
                font-weight: bold;
            }
            .marker-cluster span {
                line-height: 30px;
                color: white;
            }
            .marker-cluster-small {
                background-color: rgba(249, 115, 22, 0.6);
            }
            .marker-cluster-small div {
                background-color: rgba(249, 115, 22, 0.8);
            }
            .marker-cluster-medium {
                background-color: rgba(234, 179, 8, 0.6);
            }
            .marker-cluster-medium div {
                background-color: rgba(234, 179, 8, 0.8);
            }
            .marker-cluster-large {
                background-color: rgba(34, 197, 94, 0.6);
            }
            .marker-cluster-large div {
                background-color: rgba(34, 197, 94, 0.8);
            }
            .custom-marker {
                background-color: #10b981;
                border: 2px solid white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
        `;
        document.head.appendChild(style);
    }

    // Load map data
    async function loadMapData() {
        try {
            const params = new URLSearchParams(currentFilters);
            const response = await fetch(`/api/map/farmers?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error('Failed to load map data');
            }

            const data = await response.json();
            farmerData = data.farmers || [];

            displayFarmersOnMap(farmerData);

        } catch (error) {
            console.error('Error loading map data:', error);
            showNotification('Failed to load map data', 'error');
        }
    }

    // Display farmers on map
    function displayFarmersOnMap(farmers) {
        // Clear existing markers
        markerClusterGroup.clearLayers();

        if (farmers.length === 0) {
            showNotification('No farmers found with current filters', 'info');
            return;
        }

        farmers.forEach(farmer => {
            if (!farmer.latitude || !farmer.longitude) return;

            // Create marker
            const marker = L.circleMarker([farmer.latitude, farmer.longitude], {
                radius: 8,
                fillColor: getMarkerColor(farmer.farmer_count),
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            });

            // Add popup
            const popupContent = `
                <div class="p-2">
                    <h4 class="font-bold text-gray-800 mb-2">${farmer.region_name}</h4>
                    <p class="text-sm text-gray-600 mb-1">
                        <i class="fas fa-users mr-1"></i>${farmer.farmer_count} farmers
                    </p>
                    ${farmer.top_crops ? `
                        <p class="text-sm text-gray-600 mb-2">
                            <i class="fas fa-seedling mr-1"></i>${farmer.top_crops}
                        </p>
                    ` : ''}
                    <button class="view-region-btn bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700 transition" data-region="${farmer.region_name}" data-region-type="${farmer.region_type}">
                        View Details
                    </button>
                </div>
            `;

            marker.bindPopup(popupContent);

            // Add click handler for view details button
            marker.on('popupopen', function() {
                const btn = document.querySelector('.view-region-btn');
                if (btn) {
                    btn.addEventListener('click', function() {
                        viewRegionDetails(this.dataset.region, this.dataset.regionType);
                    });
                }
            });

            markerClusterGroup.addLayer(marker);
        });
    }

    // Get marker color based on farmer count
    function getMarkerColor(count) {
        if (count >= 50) return '#22c55e'; // green
        if (count >= 10) return '#eab308'; // yellow
        return '#f97316'; // orange
    }

    // View region details
    async function viewRegionDetails(regionName, regionType) {
        try {
            const response = await fetch(`/api/map/region/${encodeURIComponent(regionName)}?type=${regionType}`);
            
            if (!response.ok) {
                throw new Error('Failed to load region details');
            }

            const data = await response.json();
            displayRegionPanel(data);

        } catch (error) {
            console.error('Error loading region details:', error);
            showNotification('Failed to load region details', 'error');
        }
    }

    // Display region panel
    function displayRegionPanel(data) {
        document.getElementById('regionName').textContent = data.region_name || 'Region';
        
        const regionContent = document.getElementById('regionContent');
        regionContent.innerHTML = `
            <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
                <h4 class="font-bold text-gray-800 mb-3">Overview</h4>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Total Farmers</span>
                        <span class="font-bold text-gray-800">${data.farmer_count || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Active Farmers</span>
                        <span class="font-bold text-green-600">${data.active_farmers || 0}</span>
                    </div>
                </div>
            </div>

            ${data.top_crops && data.top_crops.length > 0 ? `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 class="font-bold text-gray-800 mb-3">
                        <i class="fas fa-seedling mr-2 text-green-600"></i>Top Crops
                    </h4>
                    <div class="space-y-2">
                        ${data.top_crops.map(crop => `
                            <div class="flex items-center justify-between">
                                <span class="text-sm text-gray-700 capitalize">${crop.name}</span>
                                <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">${crop.count} farmers</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${data.trending_topics && data.trending_topics.length > 0 ? `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 class="font-bold text-gray-800 mb-3">
                        <i class="fas fa-fire mr-2 text-orange-600"></i>Trending Topics
                    </h4>
                    <div class="space-y-2">
                        ${data.trending_topics.map(topic => `
                            <div class="bg-orange-50 rounded p-2">
                                <p class="text-sm text-gray-700">${topic}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${data.recent_activities && data.recent_activities.length > 0 ? `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 class="font-bold text-gray-800 mb-3">
                        <i class="fas fa-clock mr-2 text-blue-600"></i>Recent Activities
                    </h4>
                    <div class="space-y-2">
                        ${data.recent_activities.map(activity => `
                            <div class="text-sm text-gray-600">
                                <i class="fas fa-circle text-xs text-blue-500 mr-2"></i>${activity}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;

        // Show panel
        regionPanel.classList.remove('hidden');
        setTimeout(() => {
            regionPanel.classList.remove('translate-x-full');
        }, 10);
    }

    // Close region panel
    function closeRegPanel() {
        regionPanel.classList.add('translate-x-full');
        setTimeout(() => {
            regionPanel.classList.add('hidden');
        }, 300);
    }

    // Apply filters
    function applyMapFilters() {
        currentFilters = {
            crop: cropFilter.value,
            language: languageFilter.value,
            activity: activityFilter.value
        };

        loadMapData();
        showNotification('Filters applied', 'success');
    }

    // Clear filters
    function clearMapFilters() {
        cropFilter.value = '';
        languageFilter.value = '';
        activityFilter.value = '';
        currentFilters = {
            crop: '',
            language: '',
            activity: ''
        };

        loadMapData();
        showNotification('Filters cleared', 'info');
    }

    // Load network stats
    async function loadNetworkStats() {
        try {
            const response = await fetch('/api/map/stats');
            
            if (!response.ok) {
                throw new Error('Failed to load stats');
            }

            const data = await response.json();
            
            document.getElementById('totalFarmers').textContent = data.total_farmers || 0;
            document.getElementById('activeRegions').textContent = data.active_regions || 0;

        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    // Load nearby farmers
    async function loadNearbyFarmers() {
        try {
            const radius = radiusSelect.value;
            const response = await fetch(`/api/map/nearby?radius=${radius}`);
            
            if (!response.ok) {
                throw new Error('Failed to load nearby farmers');
            }

            const data = await response.json();
            displayNearbyFarmers(data.farmers || []);
            
            document.getElementById('nearbyFarmers').textContent = data.farmers ? data.farmers.length : 0;

        } catch (error) {
            console.error('Error loading nearby farmers:', error);
        }
    }

    // Display nearby farmers
    function displayNearbyFarmers(farmers) {
        const nearbyFarmersList = document.getElementById('nearbyFarmersList');
        nearbyFarmersList.innerHTML = '';

        if (farmers.length === 0) {
            nearbyFarmersList.innerHTML = `
                <div class="col-span-full text-center py-8 text-gray-500">
                    <i class="fas fa-map-marker-alt text-4xl mb-2"></i>
                    <p>No nearby farmers found</p>
                </div>
            `;
            return;
        }

        farmers.forEach(farmer => {
            const card = document.createElement('div');
            card.className = 'bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition';

            card.innerHTML = `
                <div class="flex items-center space-x-3 mb-2">
                    <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-green-600"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="font-semibold text-gray-800 truncate">${farmer.name}</h4>
                        <p class="text-xs text-gray-600 truncate">${farmer.location || 'Location not set'}</p>
                    </div>
                </div>
                ${farmer.distance ? `
                    <p class="text-xs text-gray-500 mb-2">
                        <i class="fas fa-map-marker-alt mr-1"></i>${farmer.distance.toFixed(1)} km away
                    </p>
                ` : ''}
                ${farmer.crops ? `
                    <p class="text-xs text-gray-600 mb-3">
                        <i class="fas fa-seedling mr-1"></i>${farmer.crops}
                    </p>
                ` : ''}
                <button class="connect-farmer-btn w-full bg-green-600 text-white py-1 rounded text-xs hover:bg-green-700 transition" data-farmer-id="${farmer.id}">
                    <i class="fas fa-user-plus mr-1"></i>Connect
                </button>
            `;

            const connectBtn = card.querySelector('.connect-farmer-btn');
            connectBtn.addEventListener('click', () => connectWithFarmer(farmer.id));

            nearbyFarmersList.appendChild(card);
        });
    }

    // Connect with farmer
    async function connectWithFarmer(farmerId) {
        try {
            const response = await fetch(`/api/friends/request/${farmerId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to send request');
            }

            showNotification('Friend request sent!', 'success');

        } catch (error) {
            console.error('Error connecting with farmer:', error);
            showNotification(error.message || 'Failed to send request', 'error');
        }
    }

    // Go to my location
    function goToMyLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    map.setView([lat, lng], 10);
                    
                    // Add user location marker
                    L.marker([lat, lng], {
                        icon: L.divIcon({
                            className: 'custom-marker',
                            iconSize: [20, 20]
                        })
                    }).addTo(map).bindPopup('Your Location').openPopup();

                    userLocation = { lat, lng };
                    loadNearbyFarmers();
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    showNotification('Unable to get your location', 'error');
                }
            );
        } else {
            showNotification('Geolocation is not supported by your browser', 'error');
        }
    }

    // Open privacy modal
    function openPrivacyModal() {
        privacyModal.classList.remove('hidden');
    }

    // Close privacy modal
    function closePrivMod() {
        privacyModal.classList.add('hidden');
    }

    // Handle privacy form submit
    async function handlePrivacySubmit(e) {
        e.preventDefault();

        const privacyLevel = document.querySelector('input[name="privacy"]:checked').value;

        try {
            const response = await fetch('/api/user/privacy', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location_privacy: privacyLevel
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update privacy settings');
            }

            closePrivMod();
            showNotification('Privacy settings updated', 'success');
            loadMapData();

        } catch (error) {
            console.error('Error updating privacy:', error);
            showNotification('Failed to update privacy settings', 'error');
        }
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
