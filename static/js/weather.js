// Weather functionality for AI Raitha Mitra
class WeatherWidget {
    constructor() {
        this.defaultCity = 'Bengaluru';
        this.currentLocation = null;
        this.init();
    }

    init() {
        this.bindEvents();
        // Don't auto-load weather - only load when user clicks location button
        // this.loadWeatherData();
        
        // Disable auto-refresh to improve performance
        // setInterval(() => {
        //     this.loadWeatherData();
        // }, 600000);
    }

    bindEvents() {
        const getLocationBtn = document.getElementById('getLocationBtn');
        if (getLocationBtn) {
            getLocationBtn.addEventListener('click', () => {
                this.getUserLocation();
            });
        }
    }

    async loadWeatherData(city = null, lat = null, lon = null) {
        try {
            this.showLoading();
            
            // Build API URL
            let url = '/api/weather';
            const params = new URLSearchParams();
            
            if (lat && lon) {
                params.append('lat', lat);
                params.append('lon', lon);
            } else if (city) {
                params.append('city', city);
            } else {
                params.append('city', this.defaultCity);
            }
            
            if (params.toString()) {
                url += '?' + params.toString();
            }
            
            const response = await fetch(url);
            const weatherData = await response.json();
            
            if (weatherData) {
                this.displayCurrentWeather(weatherData);
                await this.loadForecastData(city, lat, lon);
                this.hideLoading();
            } else {
                throw new Error('No weather data received');
            }
            
        } catch (error) {
            console.error('Weather API Error:', error);
            this.showError('Unable to load weather data');
        }
    }

    async loadForecastData(city = null, lat = null, lon = null) {
        try {
            // Build forecast API URL
            let url = '/api/weather/forecast';
            const params = new URLSearchParams();
            
            if (lat && lon) {
                params.append('lat', lat);
                params.append('lon', lon);
            } else if (city) {
                params.append('city', city);
            } else {
                params.append('city', this.defaultCity);
            }
            
            params.append('days', '5');
            
            if (params.toString()) {
                url += '?' + params.toString();
            }
            
            const response = await fetch(url);
            const forecastData = await response.json();
            
            if (forecastData && forecastData.forecast) {
                this.displayForecast(forecastData.forecast);
            }
            
        } catch (error) {
            console.error('Forecast API Error:', error);
        }
    }

    displayCurrentWeather(data) {
        // Update weather icon
        const weatherIcon = document.getElementById('weatherIcon');
        if (weatherIcon && data.icon) {
            // OpenWeatherMap icon format with fallback
            weatherIcon.src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
            weatherIcon.alt = data.description;
            weatherIcon.onerror = function() {
                this.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2264%22 height=%2264%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22%234A90E2%22 stroke-width=%222%22%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%225%22/%3E%3Cpath d=%22M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42%22/%3E%3C/svg%3E';
            };
        }

        // Update temperature
        const weatherTemp = document.getElementById('weatherTemp');
        if (weatherTemp) {
            weatherTemp.textContent = `${data.temperature}°C`;
        }

        // Update location
        const weatherLocation = document.getElementById('weatherLocation');
        if (weatherLocation) {
            weatherLocation.textContent = `${data.city}, ${data.country}`;
        }

        // Update description
        const weatherDescription = document.getElementById('weatherDescription');
        if (weatherDescription) {
            weatherDescription.textContent = data.description;
        }

        // Update feels like
        const weatherFeelsLike = document.getElementById('weatherFeelsLike');
        if (weatherFeelsLike) {
            weatherFeelsLike.textContent = `${data.feels_like}°C`;
        }

        // Update humidity
        const weatherHumidity = document.getElementById('weatherHumidity');
        if (weatherHumidity) {
            weatherHumidity.textContent = `${data.humidity}%`;
        }

        // Update wind
        const weatherWind = document.getElementById('weatherWind');
        if (weatherWind) {
            const windSpeed = Math.round(data.wind_speed * 3.6); // Convert m/s to km/h
            weatherWind.textContent = `${windSpeed} km/h`;
        }

        // Update pressure
        const weatherPressure = document.getElementById('weatherPressure');
        if (weatherPressure) {
            weatherPressure.textContent = `${data.pressure} hPa`;
        }

        // Update status
        this.updateStatus(data.status);
    }

    displayForecast(forecastData) {
        const forecastContainer = document.getElementById('weatherForecast');
        if (!forecastContainer || !forecastData) return;

        forecastContainer.innerHTML = '';

        forecastData.slice(0, 5).forEach((day, index) => {
            const forecastItem = document.createElement('div');
            forecastItem.className = 'forecast-item text-center p-2 rounded-lg bg-gray-50 flex-1 hover:bg-gray-100 transition-colors';
            
            // Format day name
            const dayName = index === 0 ? 'Today' : 
                          index === 1 ? 'Tomorrow' : 
                          day.day;
            
            forecastItem.innerHTML = `
                <div class="text-xs text-gray-600 mb-1">${dayName}</div>
                <img src="https://openweathermap.org/img/wn/${day.icon}@2x.png" alt="${day.description}" class="w-8 h-8 mx-auto mb-1" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2232%22 height=%2232%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22%234A90E2%22 stroke-width=%222%22%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%225%22/%3E%3Cpath d=%22M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42%22/%3E%3C/svg%3E'">
                <div class="text-xs font-medium text-gray-800">${day.temp_max}°</div>
                <div class="text-xs text-gray-500">${day.temp_min}°</div>
            `;
            
            forecastContainer.appendChild(forecastItem);
        });
    }

    getUserLocation() {
        const getLocationBtn = document.getElementById('getLocationBtn');
        
        if (!navigator.geolocation) {
            this.showError('Geolocation is not supported by this browser');
            return;
        }

        // Update button state
        if (getLocationBtn) {
            getLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Getting Location...';
            getLocationBtn.disabled = true;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                this.currentLocation = { lat, lon };
                this.loadWeatherData(null, lat, lon);
                
                // Reset button
                if (getLocationBtn) {
                    getLocationBtn.innerHTML = '<i class="fas fa-map-marker-alt mr-2"></i>Use My Location';
                    getLocationBtn.disabled = false;
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                this.showError('Unable to get your location');
                
                // Reset button
                if (getLocationBtn) {
                    getLocationBtn.innerHTML = '<i class="fas fa-map-marker-alt mr-2"></i>Use My Location';
                    getLocationBtn.disabled = false;
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000 // 5 minutes
            }
        );
    }

    showLoading() {
        const weatherStatus = document.getElementById('weatherStatus');
        const weatherStatusText = document.getElementById('weatherStatusText');
        
        if (weatherStatus && weatherStatusText) {
            weatherStatusText.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Loading weather data...';
            weatherStatus.classList.remove('hidden');
        }
    }

    hideLoading() {
        const weatherStatus = document.getElementById('weatherStatus');
        if (weatherStatus) {
            weatherStatus.classList.add('hidden');
        }
    }

    showError(message) {
        const weatherStatus = document.getElementById('weatherStatus');
        const weatherStatusText = document.getElementById('weatherStatusText');
        
        if (weatherStatus && weatherStatusText) {
            weatherStatusText.innerHTML = `<i class="fas fa-exclamation-triangle mr-1"></i>${message}`;
            weatherStatus.classList.remove('hidden');
            
            // Hide error after 5 seconds
            setTimeout(() => {
                weatherStatus.classList.add('hidden');
            }, 5000);
        }
    }

    updateStatus(status) {
        const weatherStatus = document.getElementById('weatherStatus');
        const weatherStatusText = document.getElementById('weatherStatusText');
        
        if (weatherStatus && weatherStatusText) {
            if (status === 'demo') {
                weatherStatusText.innerHTML = '<i class="fas fa-info-circle mr-1"></i>Demo weather data (Configure API key for live data)';
                weatherStatus.classList.remove('hidden');
            } else if (status === 'success') {
                weatherStatus.classList.add('hidden');
            }
        }
    }

    // Method to refresh weather data
    refresh() {
        if (this.currentLocation) {
            this.loadWeatherData(null, this.currentLocation.lat, this.currentLocation.lon);
        } else {
            this.loadWeatherData();
        }
    }
}

// Initialize weather widget when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the home page
    if (document.getElementById('weatherWidget')) {
        window.weatherWidget = new WeatherWidget();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WeatherWidget;
}