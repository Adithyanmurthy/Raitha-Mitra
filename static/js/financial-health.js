// Financial Health JavaScript
// Handles score gauge visualization, category breakdown chart, expense form submission, report generation, and score updates

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const addExpenseBtn = document.getElementById('addExpenseBtn');
    const generateReportBtn = document.getElementById('generateReportBtn');
    const refreshScoreBtn = document.getElementById('refreshScoreBtn');
    const expenseModal = document.getElementById('expenseModal');
    const expenseForm = document.getElementById('expenseForm');
    const closeExpenseModal = document.getElementById('closeExpenseModal');
    const cancelExpenseModal = document.getElementById('cancelExpenseModal');
    const expenseFilter = document.getElementById('expenseFilter');
    const expenseList = document.getElementById('expenseList');

    // State
    let expenseChart = null;
    let currentScore = null;

    // Category colors for chart
    const categoryColors = {
        'seeds': '#3b82f6',
        'fertilizer': '#10b981',
        'pesticides': '#ef4444',
        'labor': '#f59e0b',
        'equipment': '#8b5cf6',
        'irrigation': '#ec4899',
        'transport': '#06b6d4',
        'other': '#6366f1'
    };

    // Initialize
    init();

    function init() {
        // Set up event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        addExpenseBtn.addEventListener('click', openExpenseModal);
        generateReportBtn.addEventListener('click', generateReport);
        refreshScoreBtn.addEventListener('click', loadFinancialScore);
        closeExpenseModal.addEventListener('click', closeExpModal);
        cancelExpenseModal.addEventListener('click', closeExpModal);
        expenseForm.addEventListener('submit', handleExpenseSubmit);
        expenseFilter.addEventListener('change', loadExpenses);

        // Set default expense date to today
        document.getElementById('expenseDate').value = formatDate(new Date());

        // Load initial data
        loadFinancialScore();
        loadExpenses();
        initializeChart();
    }

    // Load financial score from server
    async function loadFinancialScore() {
        try {
            // Show loading
            document.getElementById('scoreValue').textContent = '--';
            document.getElementById('scoreLabel').textContent = 'Loading...';

            const response = await fetch('/api/finance/score');
            
            const data = await response.json();

            if (!response.ok) {
                // Check if it's a rate limit error
                if (response.status === 429 && data.rate_limit_exceeded) {
                    const resetDate = new Date(data.reset_time * 1000);
                    const resetTime = resetDate.toLocaleTimeString();
                    throw new Error(`${data.error} Please try again after ${resetTime}.`);
                }
                throw new Error(data.error || 'Failed to load financial score');
            }
            
            console.log('Financial Score Data:', data); // Debug log
            currentScore = data;

            // Update UI immediately (fast)
            updateScoreDisplay(data);
            updateQuickStats(data);
            
            // Load recommendations (can be slower, but doesn't block UI)
            updateRecommendations(data.recommendations || []);

        } catch (error) {
            console.error('Error loading financial score:', error);
            showNotification('Failed to load financial score', 'error');
        }
    }

    // Update score display
    function updateScoreDisplay(data) {
        const score = data.overall_score || 0;
        const costScore = data.cost_efficiency_score || 0;
        const yieldScore = data.yield_performance_score || 0;
        const timingScore = data.market_timing_score || 0;

        console.log('Score Display:', { score, costScore, yieldScore, timingScore }); // Debug log

        // Update main score
        document.getElementById('scoreValue').textContent = Math.round(score);

        // Update score label
        const scoreLabel = document.getElementById('scoreLabel');
        if (score >= 80) {
            scoreLabel.textContent = 'Excellent';
            scoreLabel.className = 'text-sm font-semibold mt-2 px-3 py-1 rounded-full bg-green-100 text-green-700';
        } else if (score >= 60) {
            scoreLabel.textContent = 'Good';
            scoreLabel.className = 'text-sm font-semibold mt-2 px-3 py-1 rounded-full bg-yellow-100 text-yellow-700';
        } else if (score >= 40) {
            scoreLabel.textContent = 'Fair';
            scoreLabel.className = 'text-sm font-semibold mt-2 px-3 py-1 rounded-full bg-orange-100 text-orange-700';
        } else {
            scoreLabel.textContent = 'Needs Improvement';
            scoreLabel.className = 'text-sm font-semibold mt-2 px-3 py-1 rounded-full bg-red-100 text-red-700';
        }

        // Animate score circle
        const circle = document.getElementById('scoreCircle');
        const circumference = 703.72;
        const offset = circumference - (score / 100) * circumference;
        setTimeout(() => {
            circle.style.strokeDashoffset = offset;
        }, 100);

        // Update breakdown scores
        document.getElementById('costScore').textContent = Math.round(costScore);
        document.getElementById('yieldScore').textContent = Math.round(yieldScore);
        document.getElementById('timingScore').textContent = Math.round(timingScore);

        // Animate breakdown bars
        setTimeout(() => {
            document.getElementById('costBar').style.width = `${costScore}%`;
            document.getElementById('yieldBar').style.width = `${yieldScore}%`;
            document.getElementById('timingBar').style.width = `${timingScore}%`;
        }, 200);
    }

    // Update quick stats
    function updateQuickStats(data) {
        // Try both breakdown and score_breakdown for compatibility
        const breakdown = data.score_breakdown || data.breakdown || {};
        
        console.log('Quick Stats Breakdown:', breakdown); // Debug log
        
        const totalExpenses = breakdown.total_expenses || 0;
        const projectedRevenue = breakdown.projected_revenue || 0;
        const profitMargin = breakdown.profit_margin || 0;
        const roi = breakdown.roi || 0;
        
        document.getElementById('totalExpenses').textContent = 
            totalExpenses > 0 ? `₹${formatNumber(totalExpenses)}` : '₹0';
        
        document.getElementById('projectedRevenue').textContent = 
            projectedRevenue > 0 ? `₹${formatNumber(projectedRevenue)}` : '₹0';
        
        document.getElementById('profitMargin').textContent = 
            profitMargin !== 0 ? `${profitMargin.toFixed(1)}%` : '0%';
        
        document.getElementById('roi').textContent = 
            roi !== 0 ? `${roi.toFixed(1)}%` : '0%';
    }

    // Update recommendations
    function updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations');
        container.innerHTML = '';

        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = `
                <div class="bg-white rounded-lg p-4 border border-purple-100">
                    <p class="text-sm text-gray-600">
                        <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                        No recommendations available. Add more data to get personalized insights.
                    </p>
                </div>
            `;
            return;
        }

        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.className = 'bg-white rounded-lg p-3 border border-purple-100';
            
            // Handle both string and object formats
            let content = '';
            if (typeof rec === 'string') {
                content = `
                    <p class="text-sm text-gray-700">
                        <i class="fas fa-lightbulb text-yellow-500 mr-2"></i>
                        ${rec}
                    </p>
                `;
            } else if (typeof rec === 'object' && rec !== null) {
                // Handle structured recommendation object - compact version
                const impactColor = rec.impact === 'High' ? 'green' : rec.impact === 'Medium' ? 'yellow' : 'blue';
                const difficultyColor = rec.difficulty === 'Easy' ? 'green' : rec.difficulty === 'Medium' ? 'yellow' : 'red';
                
                content = `
                    <div class="flex items-start gap-2">
                        <i class="fas fa-lightbulb text-yellow-500 text-sm mt-0.5"></i>
                        <div class="flex-1">
                            <div class="flex items-center gap-1.5 mb-1">
                                <span class="text-xs font-semibold px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">${rec.focus_area || 'General'}</span>
                                <span class="text-xs px-1.5 py-0.5 rounded bg-${impactColor}-100 text-${impactColor}-700">${rec.impact || 'Med'}</span>
                                <span class="text-xs px-1.5 py-0.5 rounded bg-${difficultyColor}-100 text-${difficultyColor}-700">${rec.difficulty || 'Med'}</span>
                            </div>
                            <p class="text-sm font-medium text-gray-800">${rec.action}</p>
                            ${rec.details ? `<p class="text-xs text-gray-600 mt-0.5">${rec.details}</p>` : ''}
                        </div>
                    </div>
                `;
            }
            
            div.innerHTML = content;
            container.appendChild(div);
        });
    }

    // Load expenses from server
    async function loadExpenses() {
        try {
            const filter = expenseFilter.value;
            const response = await fetch(`/api/finance/expenses?filter=${filter}`);
            
            if (!response.ok) {
                throw new Error('Failed to load expenses');
            }

            const data = await response.json();
            displayExpenses(data.expenses || []);
            updateExpenseChart(data.expenses || []);

        } catch (error) {
            console.error('Error loading expenses:', error);
            showNotification('Failed to load expenses', 'error');
        }
    }

    // Display expenses list
    function displayExpenses(expenses) {
        expenseList.innerHTML = '';

        if (expenses.length === 0) {
            expenseList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-inbox text-4xl mb-2"></i>
                    <p>No expenses recorded yet</p>
                </div>
            `;
            return;
        }

        expenses.forEach(expense => {
            const div = document.createElement('div');
            div.className = 'flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition';
            
            const categoryColor = categoryColors[expense.category] || '#6366f1';
            
            div.innerHTML = `
                <div class="flex items-center space-x-3 flex-1">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center" style="background-color: ${categoryColor}20;">
                        <i class="fas fa-${getCategoryIcon(expense.category)} text-lg" style="color: ${categoryColor};"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-800 capitalize">${expense.category}</h4>
                        <p class="text-xs text-gray-600">${formatDisplayDate(expense.expense_date)}</p>
                        ${expense.description ? `<p class="text-xs text-gray-500 mt-1">${expense.description}</p>` : ''}
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-bold text-red-600">₹${formatNumber(expense.amount)}</p>
                    ${expense.crop_related ? `<p class="text-xs text-gray-500">${expense.crop_related}</p>` : ''}
                </div>
            `;
            
            expenseList.appendChild(div);
        });
    }

    // Get category icon
    function getCategoryIcon(category) {
        const icons = {
            'seeds': 'seedling',
            'fertilizer': 'leaf',
            'pesticides': 'spray-can',
            'labor': 'users',
            'equipment': 'tools',
            'irrigation': 'tint',
            'transport': 'truck',
            'other': 'ellipsis-h'
        };
        return icons[category] || 'tag';
    }

    // Initialize expense chart
    function initializeChart() {
        const ctx = document.getElementById('expenseChart').getContext('2d');
        expenseChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ₹${formatNumber(value)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Update expense chart
    function updateExpenseChart(expenses) {
        if (!expenseChart) return;

        // Aggregate expenses by category
        const categoryTotals = {};
        expenses.forEach(expense => {
            const category = expense.category;
            categoryTotals[category] = (categoryTotals[category] || 0) + parseFloat(expense.amount);
        });

        // Prepare chart data
        const labels = Object.keys(categoryTotals).map(cat => cat.charAt(0).toUpperCase() + cat.slice(1));
        const data = Object.values(categoryTotals);
        const colors = Object.keys(categoryTotals).map(cat => categoryColors[cat] || '#6366f1');

        // Update chart
        expenseChart.data.labels = labels;
        expenseChart.data.datasets[0].data = data;
        expenseChart.data.datasets[0].backgroundColor = colors;
        expenseChart.update();
    }

    // Open expense modal
    function openExpenseModal() {
        expenseForm.reset();
        document.getElementById('expenseDate').value = formatDate(new Date());
        expenseModal.classList.remove('hidden');
    }

    // Close expense modal
    function closeExpModal() {
        expenseModal.classList.add('hidden');
        expenseForm.reset();
    }

    // Handle expense form submit
    async function handleExpenseSubmit(e) {
        e.preventDefault();

        const formData = {
            category: document.getElementById('expenseCategory').value,
            amount: parseFloat(document.getElementById('expenseAmount').value),
            expense_date: document.getElementById('expenseDate').value,
            description: document.getElementById('expenseDescription').value || null,
            crop_related: document.getElementById('cropRelated').value || null
        };

        try {
            const response = await fetch('/api/finance/expense', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Failed to save expense');
            }

            closeExpModal();
            await loadExpenses();
            showNotification('Expense added successfully!', 'success');

            // Suggest refreshing score
            setTimeout(() => {
                showNotification('Click "Refresh Score" to update your financial health', 'info');
            }, 1500);

        } catch (error) {
            console.error('Error saving expense:', error);
            showNotification('Failed to save expense', 'error');
        }
    }

    // Generate detailed report
    async function generateReport() {
        try {
            const response = await fetch('/api/finance/report');
            
            if (!response.ok) {
                throw new Error('Failed to generate report');
            }

            const data = await response.json();
            displayDetailedReport(data);

        } catch (error) {
            console.error('Error generating report:', error);
            showNotification('Failed to generate report', 'error');
        }
    }

    // Display detailed report
    function displayDetailedReport(data) {
        const reportContent = document.getElementById('reportContent');
        const detailedReport = document.getElementById('detailedReport');

        reportContent.innerHTML = `
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                <h4 class="font-bold text-gray-800 mb-4">Financial Summary</h4>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-sm text-gray-600">Total Income</p>
                        <p class="text-xl font-bold text-green-600">₹${formatNumber(data.total_income || 0)}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Total Expenses</p>
                        <p class="text-xl font-bold text-red-600">₹${formatNumber(data.total_expenses || 0)}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Net Profit</p>
                        <p class="text-xl font-bold text-blue-600">₹${formatNumber(data.net_profit || 0)}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-600">Profit Margin</p>
                        <p class="text-xl font-bold text-purple-600">${data.profit_margin ? data.profit_margin.toFixed(1) : 0}%</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg p-6 border border-gray-200">
                <h4 class="font-bold text-gray-800 mb-4">Expense Analysis</h4>
                <div class="space-y-3">
                    ${Object.entries(data.expense_by_category || {}).map(([category, amount]) => `
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-700 capitalize">${category}</span>
                            <span class="font-semibold text-gray-800">₹${formatNumber(amount)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="bg-white rounded-lg p-6 border border-gray-200">
                <h4 class="font-bold text-gray-800 mb-4">Insights & Recommendations</h4>
                <div class="space-y-2">
                    ${(data.insights || []).map(insight => `
                        <p class="text-sm text-gray-700">
                            <i class="fas fa-check-circle text-green-600 mr-2"></i>${insight}
                        </p>
                    `).join('')}
                </div>
            </div>
        `;

        detailedReport.classList.remove('hidden');
        detailedReport.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Format number with commas
    function formatNumber(num) {
        return parseFloat(num).toLocaleString('en-IN', { maximumFractionDigits: 0 });
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
    .transition-all {
        transition: all 0.3s ease;
    }
    .duration-1000 {
        transition-duration: 1s;
    }
    .duration-2000 {
        transition-duration: 2s;
    }
`;
document.head.appendChild(style);
