// Yield Prediction JavaScript
// Handles prediction requests, confidence meter, timeline chart, actual yield recording, and prediction updates

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const viewHistoryBtn = document.getElementById('viewHistoryBtn');
    const predictionForm = document.getElementById('predictionForm');
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const resultsDisplay = document.getElementById('resultsDisplay');
    const recordActualBtn = document.getElementById('recordActualBtn');
    const newPredictionBtn = document.getElementById('newPredictionBtn');
    const actualYieldModal = document.getElementById('actualYieldModal');
    const actualYieldForm = document.getElementById('actualYieldForm');
    const closeActualModal = document.getElementById('closeActualModal');
    const cancelActualModal = document.getElementById('cancelActualModal');

    // State
    let currentPrediction = null;

    // Initialize
    init();

    function init() {
        // Set up event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        viewHistoryBtn.addEventListener('click', viewHistory);
        predictionForm.addEventListener('submit', handlePredictionSubmit);
        recordActualBtn.addEventListener('click', openActualYieldModal);
        newPredictionBtn.addEventListener('click', resetForm);
        closeActualModal.addEventListener('click', closeActualModal_);
        cancelActualModal.addEventListener('click', closeActualModal_);
        actualYieldForm.addEventListener('submit', handleActualYieldSubmit);

        // Set default planting date to 3 months ago
        const threeMonthsAgo = new Date();
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        document.getElementById('plantingDate').value = formatDate(threeMonthsAgo);
    }

    // Handle prediction form submit
    async function handlePredictionSubmit(e) {
        e.preventDefault();

        const formData = {
            crop_type: document.getElementById('cropType').value,
            planting_date: document.getElementById('plantingDate').value,
            farm_size: document.getElementById('farmSize').value || null,
            soil_type: document.getElementById('soilType').value || null,
            irrigation_type: document.getElementById('irrigationType').value || null
        };

        try {
            // Show loading state
            showLoading();

            const response = await fetch('/api/yield/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                // Check if it's a rate limit error
                if (response.status === 429 && data.rate_limit_exceeded) {
                    const resetDate = new Date(data.reset_time * 1000);
                    const resetTime = resetDate.toLocaleTimeString();
                    throw new Error(`${data.error} Please try again after ${resetTime}.`);
                }
                throw new Error(data.error || 'Failed to generate prediction');
            }
            currentPrediction = data;

            // Display results
            displayResults(data);

        } catch (error) {
            console.error('Error generating prediction:', error);
            showNotification(error.message || 'Failed to generate prediction', 'error');
            hideLoading();
        }
    }

    // Show loading state
    function showLoading() {
        emptyState.classList.add('hidden');
        resultsDisplay.classList.add('hidden');
        loadingState.classList.remove('hidden');
    }

    // Hide loading state
    function hideLoading() {
        loadingState.classList.add('hidden');
    }

    // Display prediction results
    function displayResults(data) {
        hideLoading();
        emptyState.classList.add('hidden');
        resultsDisplay.classList.remove('hidden');

        // Update prediction summary
        document.getElementById('predictedYield').textContent = data.predicted_yield ? data.predicted_yield.toFixed(1) : '--';
        document.getElementById('qualityGrade').textContent = data.quality_grade || data.predicted_quality || '--';
        document.getElementById('harvestDate').textContent = data.harvest_date ? formatDisplayDate(data.harvest_date) : '--';

        // Update confidence score
        updateConfidenceScore(data.confidence_score || 0);

        // Update timeline
        updateTimeline(data.planting_date, data.harvest_date);

        // Update checklist
        updateChecklist(data.preparation_checklist || []);

        // Update regional comparison
        updateRegionalComparison(data.regional_comparison || {});

        // Store prediction ID for recording actual yield
        if (data.prediction_id) {
            document.getElementById('predictionId').value = data.prediction_id;
        }

        // Scroll to results
        resultsDisplay.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Update confidence score meter
    function updateConfidenceScore(score) {
        // Ensure score is between 0 and 1
        const normalizedScore = Math.max(0, Math.min(1, score));
        const percentage = Math.round(normalizedScore * 100);
        const confidenceBar = document.getElementById('confidenceBar');
        const confidenceText = document.getElementById('confidenceText');

        // Animate the bar
        setTimeout(() => {
            confidenceBar.style.width = `${percentage}%`;
            confidenceBar.style.maxWidth = '100%';
            confidenceText.textContent = `${percentage}%`;

            // Change color based on confidence
            if (percentage >= 80) {
                confidenceBar.className = 'bg-gradient-to-r from-green-500 to-emerald-600 h-6 rounded-full transition-all duration-1000 flex items-center justify-end pr-2';
            } else if (percentage >= 60) {
                confidenceBar.className = 'bg-gradient-to-r from-yellow-500 to-orange-600 h-6 rounded-full transition-all duration-1000 flex items-center justify-end pr-2';
            } else {
                confidenceBar.className = 'bg-gradient-to-r from-red-500 to-pink-600 h-6 rounded-full transition-all duration-1000 flex items-center justify-end pr-2';
            }
        }, 100);
    }

    // Update timeline visualization
    function updateTimeline(plantingDate, harvestDate) {
        const timeline = document.getElementById('timeline');
        timeline.innerHTML = '';

        if (!plantingDate || !harvestDate) {
            timeline.innerHTML = '<p class="text-sm text-gray-500">Timeline data not available</p>';
            return;
        }

        const planting = new Date(plantingDate);
        const harvest = new Date(harvestDate);
        const today = new Date();
        
        const totalDays = Math.ceil((harvest - planting) / (1000 * 60 * 60 * 24));
        const daysPassed = Math.ceil((today - planting) / (1000 * 60 * 60 * 24));
        const daysRemaining = Math.max(0, totalDays - daysPassed);
        const progress = Math.min(100, Math.max(0, (daysPassed / totalDays) * 100));

        timeline.innerHTML = `
            <div class="mb-4">
                <div class="flex justify-between text-sm text-gray-600 mb-2">
                    <span><i class="fas fa-seedling mr-1"></i>Planted: ${formatDisplayDate(plantingDate)}</span>
                    <span><i class="fas fa-calendar-day mr-1"></i>Today</span>
                    <span><i class="fas fa-tractor mr-1"></i>Harvest: ${formatDisplayDate(harvestDate)}</span>
                </div>
                <div class="relative bg-gray-200 rounded-full h-4">
                    <div class="absolute top-0 left-0 bg-gradient-to-r from-green-500 to-emerald-600 h-4 rounded-full transition-all duration-1000" style="width: ${progress}%"></div>
                    <div class="absolute top-0 left-0 w-full h-4 flex items-center justify-center">
                        <span class="text-xs font-bold text-white drop-shadow">${Math.round(progress)}%</span>
                    </div>
                </div>
                <div class="flex justify-between text-xs text-gray-500 mt-2">
                    <span>${daysPassed} days passed</span>
                    <span>${daysRemaining} days remaining</span>
                </div>
            </div>
            <div class="grid grid-cols-3 gap-3 mt-4">
                <div class="bg-green-50 rounded-lg p-3 text-center">
                    <i class="fas fa-seedling text-green-600 text-xl mb-1"></i>
                    <p class="text-xs text-gray-600">Planting</p>
                </div>
                <div class="bg-blue-50 rounded-lg p-3 text-center">
                    <i class="fas fa-leaf text-blue-600 text-xl mb-1"></i>
                    <p class="text-xs text-gray-600">Growing</p>
                </div>
                <div class="bg-yellow-50 rounded-lg p-3 text-center">
                    <i class="fas fa-tractor text-yellow-600 text-xl mb-1"></i>
                    <p class="text-xs text-gray-600">Harvest</p>
                </div>
            </div>
        `;
    }

    // Update preparation checklist
    function updateChecklist(items) {
        const checklist = document.getElementById('checklist');
        checklist.innerHTML = '';

        if (!items || items.length === 0) {
            checklist.innerHTML = '<p class="text-sm text-gray-500">No preparation items at this time</p>';
            return;
        }

        items.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'flex items-start space-x-3 p-3 bg-orange-50 rounded-lg border border-orange-200';
            
            // Handle both string and object formats
            let displayText = '';
            if (typeof item === 'string') {
                displayText = item;
            } else if (typeof item === 'object' && item !== null) {
                // Extract action and description from object
                displayText = item.action || item.description || JSON.stringify(item);
                if (item.action && item.description && item.action !== item.description) {
                    displayText = `${item.action} - ${item.description}`;
                }
                // Add priority badge if available
                if (item.priority) {
                    const priorityColor = item.priority === 'High' ? 'red' : item.priority === 'Medium' ? 'yellow' : 'green';
                    displayText = `<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded bg-${priorityColor}-100 text-${priorityColor}-700 mr-2">${item.priority}</span>${displayText}`;
                }
            }
            
            div.innerHTML = `
                <i class="fas fa-check-circle text-orange-600 mt-0.5"></i>
                <span class="text-sm text-gray-700 flex-1">${displayText}</span>
            `;
            checklist.appendChild(div);
        });
    }

    // Update regional comparison
    function updateRegionalComparison(comparison) {
        const container = document.getElementById('regionalComparison');
        container.innerHTML = '';

        if (!comparison || Object.keys(comparison).length === 0) {
            container.innerHTML = '<p class="text-sm text-gray-500">Regional comparison data not available</p>';
            return;
        }

        const yourYield = currentPrediction?.predicted_yield || 0;
        const regionalAvg = comparison.regional_average || 0;
        const difference = yourYield - regionalAvg;
        const percentDiff = regionalAvg > 0 ? ((difference / regionalAvg) * 100).toFixed(1) : 0;

        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p class="text-sm text-gray-600 mb-1">Your Predicted Yield</p>
                    <p class="text-2xl font-bold text-purple-600">${yourYield.toFixed(1)} <span class="text-sm font-normal">quintals/acre</span></p>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <p class="text-sm text-gray-600 mb-1">Regional Average</p>
                    <p class="text-2xl font-bold text-gray-600">${regionalAvg.toFixed(1)} <span class="text-sm font-normal">quintals/acre</span></p>
                </div>
            </div>
            <div class="mt-4 p-4 rounded-lg ${difference >= 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}">
                <p class="text-sm ${difference >= 0 ? 'text-green-700' : 'text-red-700'}">
                    <i class="fas fa-${difference >= 0 ? 'arrow-up' : 'arrow-down'} mr-2"></i>
                    Your prediction is <strong>${Math.abs(percentDiff)}%</strong> ${difference >= 0 ? 'above' : 'below'} the regional average
                </p>
            </div>
        `;
    }

    // Open actual yield modal
    function openActualYieldModal() {
        if (!currentPrediction || !currentPrediction.prediction_id) {
            showNotification('No prediction available to record', 'error');
            return;
        }
        actualYieldModal.classList.remove('hidden');
    }

    // Close actual yield modal
    function closeActualModal_() {
        actualYieldModal.classList.add('hidden');
        actualYieldForm.reset();
    }

    // Handle actual yield form submit
    async function handleActualYieldSubmit(e) {
        e.preventDefault();

        const predictionId = document.getElementById('predictionId').value;
        const formData = {
            actual_yield: parseFloat(document.getElementById('actualYield').value),
            actual_quality: document.getElementById('actualQuality').value,
            notes: document.getElementById('yieldNotes').value || null
        };

        try {
            const response = await fetch('/api/yield/record-actual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prediction_id: predictionId,
                    ...formData
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to record actual yield');
            }

            closeActualModal_();
            showNotification('Actual yield recorded successfully!', 'success');

            // Update current prediction
            if (currentPrediction) {
                currentPrediction.actual_yield = formData.actual_yield;
                currentPrediction.actual_quality = formData.actual_quality;
            }

        } catch (error) {
            console.error('Error recording actual yield:', error);
            showNotification(error.message || 'Failed to record actual yield', 'error');
        }
    }

    // Reset form for new prediction
    function resetForm() {
        predictionForm.reset();
        currentPrediction = null;
        resultsDisplay.classList.add('hidden');
        emptyState.classList.remove('hidden');
        
        // Set default planting date
        const threeMonthsAgo = new Date();
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        document.getElementById('plantingDate').value = formatDate(threeMonthsAgo);

        // Scroll to form
        predictionForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // View prediction history
    async function viewHistory() {
        try {
            const response = await fetch('/api/yield/history');
            
            if (!response.ok) {
                throw new Error('Failed to load history');
            }

            const data = await response.json();
            
            if (data.predictions && data.predictions.length > 0) {
                displayHistoryModal(data.predictions);
            } else {
                showNotification('No prediction history available', 'info');
            }

        } catch (error) {
            console.error('Error loading history:', error);
            showNotification('Failed to load history', 'error');
        }
    }

    // Display history modal
    function displayHistoryModal(predictions) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-y-auto p-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-xl font-bold text-gray-800">
                        <i class="fas fa-history mr-2 text-blue-600"></i>
                        Prediction History
                    </h3>
                    <button class="close-history text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    ${predictions.map(pred => `
                        <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <h4 class="font-semibold text-gray-800">${pred.crop_type}</h4>
                                    <p class="text-sm text-gray-600">Planted: ${formatDisplayDate(pred.planting_date)}</p>
                                </div>
                                <span class="text-xs bg-gray-100 px-2 py-1 rounded">${formatDisplayDate(pred.created_at)}</span>
                            </div>
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                                <div>
                                    <p class="text-xs text-gray-500">Predicted</p>
                                    <p class="font-semibold text-green-600">${pred.predicted_yield ? pred.predicted_yield.toFixed(1) : '--'}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-500">Actual</p>
                                    <p class="font-semibold text-blue-600">${pred.actual_yield ? pred.actual_yield.toFixed(1) : 'Not recorded'}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-500">Quality</p>
                                    <p class="font-semibold text-purple-600">${pred.predicted_quality || '--'}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-gray-500">Confidence</p>
                                    <p class="font-semibold text-orange-600">${pred.confidence_score ? Math.round(pred.confidence_score * 100) + '%' : '--'}</p>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close button
        modal.querySelector('.close-history').addEventListener('click', () => {
            modal.remove();
        });

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    // Format date to YYYY-MM-DD
    function formatDate(date) {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // Format date for display
    function formatDisplayDate(dateStr) {
        if (!dateStr) return '--';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
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

// Add animation and loader styles
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
    .loader {
        border-top-color: #10b981;
        animation: spinner 1.5s linear infinite;
    }
    @keyframes spinner {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
