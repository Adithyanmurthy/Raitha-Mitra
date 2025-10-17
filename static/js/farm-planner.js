// Farm Planner JavaScript
// Handles calendar navigation, task creation/editing, task completion, AI schedule generation, and date filtering

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const backBtn = document.getElementById('backBtn');
    const addActivityBtn = document.getElementById('addActivityBtn');
    const generateScheduleBtn = document.getElementById('generateScheduleBtn');
    const prevWeek = document.getElementById('prevWeek');
    const nextWeek = document.getElementById('nextWeek');
    const todayBtn = document.getElementById('todayBtn');
    const weekRange = document.getElementById('weekRange');
    const weeklyCalendar = document.getElementById('weeklyCalendar');
    const emptyState = document.getElementById('emptyState');
    const activityModal = document.getElementById('activityModal');
    const generateModal = document.getElementById('generateModal');
    const activityForm = document.getElementById('activityForm');
    const generateForm = document.getElementById('generateForm');
    const closeModal = document.getElementById('closeModal');
    const cancelModal = document.getElementById('cancelModal');
    const closeGenerateModal = document.getElementById('closeGenerateModal');
    const cancelGenerateModal = document.getElementById('cancelGenerateModal');
    const totalTasks = document.getElementById('totalTasks');
    const completedTasks = document.getElementById('completedTasks');
    const pendingTasks = document.getElementById('pendingTasks');
    const aiSuggestions = document.getElementById('aiSuggestions');

    // State
    let currentWeekStart = getWeekStart(new Date());
    let activities = [];
    let editingActivityId = null;

    // Activity type colors
    const activityColors = {
        'irrigation': 'blue',
        'fertilization': 'green',
        'pest_control': 'red',
        'harvesting': 'yellow',
        'planting': 'indigo',
        'weeding': 'orange',
        'other': 'purple'
    };

    // Initialize
    init();

    function init() {
        // Set up event listeners
        backBtn.addEventListener('click', () => window.location.href = '/home');
        addActivityBtn.addEventListener('click', openAddModal);
        generateScheduleBtn.addEventListener('click', openGenerateModal);
        prevWeek.addEventListener('click', () => navigateWeek(-1));
        nextWeek.addEventListener('click', () => navigateWeek(1));
        todayBtn.addEventListener('click', goToToday);
        closeModal.addEventListener('click', closeActivityModal);
        cancelModal.addEventListener('click', closeActivityModal);
        closeGenerateModal.addEventListener('click', closeGenModal);
        cancelGenerateModal.addEventListener('click', closeGenModal);
        activityForm.addEventListener('submit', handleActivitySubmit);
        generateForm.addEventListener('submit', handleGenerateSubmit);

        // Add activity triggers
        document.querySelectorAll('.add-activity-trigger').forEach(btn => {
            btn.addEventListener('click', openAddModal);
        });

        // Load initial schedule
        loadSchedule();
    }

    // Get start of week (Monday)
    function getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        return new Date(d.setDate(diff));
    }

    // Navigate weeks
    function navigateWeek(direction) {
        currentWeekStart.setDate(currentWeekStart.getDate() + (direction * 7));
        loadSchedule();
    }

    // Go to today
    function goToToday() {
        currentWeekStart = getWeekStart(new Date());
        loadSchedule();
    }

    // Load schedule from server
    async function loadSchedule() {
        try {
            const weekEnd = new Date(currentWeekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);

            const startDate = formatDate(currentWeekStart);
            const endDate = formatDate(weekEnd);

            const response = await fetch(`/api/farm/schedule?start_date=${startDate}&end_date=${endDate}`);
            
            if (!response.ok) {
                throw new Error('Failed to load schedule');
            }

            const data = await response.json();
            activities = data.schedule || data.activities || [];

            // Update UI
            updateWeekRange();
            renderCalendar();
            updateStats();

        } catch (error) {
            console.error('Error loading schedule:', error);
            showNotification('Failed to load schedule', 'error');
        }
    }

    // Update week range display
    function updateWeekRange() {
        const weekEnd = new Date(currentWeekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        const options = { month: 'short', day: 'numeric', year: 'numeric' };
        const startStr = currentWeekStart.toLocaleDateString('en-US', options);
        const endStr = weekEnd.toLocaleDateString('en-US', options);

        weekRange.textContent = `${startStr} - ${endStr}`;
    }

    // Render calendar
    function renderCalendar() {
        weeklyCalendar.innerHTML = '';

        if (activities.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');

        // Group activities by date
        const activityByDate = {};
        activities.forEach(activity => {
            const date = activity.scheduled_date;
            if (!activityByDate[date]) {
                activityByDate[date] = [];
            }
            activityByDate[date].push(activity);
        });

        // Render each day
        for (let i = 0; i < 7; i++) {
            const date = new Date(currentWeekStart);
            date.setDate(date.getDate() + i);
            const dateStr = formatDate(date);
            const dayActivities = activityByDate[dateStr] || [];

            const dayCard = createDayCard(date, dayActivities);
            weeklyCalendar.appendChild(dayCard);
        }
    }

    // Create day card
    function createDayCard(date, dayActivities) {
        const isToday = formatDate(date) === formatDate(new Date());
        const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
        const dayDate = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

        const card = document.createElement('div');
        card.className = `border rounded-lg p-4 ${isToday ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-white'}`;

        const header = document.createElement('div');
        header.className = 'flex justify-between items-center mb-3';
        header.innerHTML = `
            <div>
                <h4 class="font-bold text-gray-800">${dayName}</h4>
                <p class="text-sm text-gray-600">${dayDate}</p>
            </div>
            ${isToday ? '<span class="text-xs bg-green-600 text-white px-2 py-1 rounded-full">Today</span>' : ''}
        `;
        card.appendChild(header);

        if (dayActivities.length === 0) {
            const empty = document.createElement('p');
            empty.className = 'text-sm text-gray-400 italic';
            empty.textContent = 'No activities';
            card.appendChild(empty);
        } else {
            const taskList = document.createElement('div');
            taskList.className = 'space-y-2';

            dayActivities.forEach(activity => {
                const taskCard = createTaskCard(activity);
                taskList.appendChild(taskCard);
            });

            card.appendChild(taskList);
        }

        return card;
    }

    // Create task card
    function createTaskCard(activity) {
        const color = activityColors[activity.activity_type] || 'purple';
        const isCompleted = activity.status === 'completed';

        const card = document.createElement('div');
        card.className = `bg-${color}-50 border border-${color}-200 rounded-lg p-3 cursor-pointer hover:shadow-md transition`;

        card.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex items-start space-x-2 flex-1">
                    <input type="checkbox" 
                           class="task-checkbox mt-1 w-4 h-4 text-green-600 rounded focus:ring-green-500" 
                           ${isCompleted ? 'checked' : ''}
                           data-id="${activity.id}">
                    <div class="flex-1">
                        <h5 class="font-semibold text-gray-800 text-sm ${isCompleted ? 'line-through' : ''}">
                            ${formatActivityType(activity.activity_type)}
                        </h5>
                        ${activity.crop_type ? `<p class="text-xs text-gray-600 mt-1"><i class="fas fa-seedling mr-1"></i>${activity.crop_type}</p>` : ''}
                        ${activity.description ? `<p class="text-xs text-gray-600 mt-1">${activity.description}</p>` : ''}
                        ${activity.ai_generated ? '<span class="inline-block mt-1 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full"><i class="fas fa-magic mr-1"></i>AI</span>' : ''}
                    </div>
                </div>
                <button class="edit-task-btn text-gray-400 hover:text-gray-600 ml-2" data-id="${activity.id}">
                    <i class="fas fa-edit"></i>
                </button>
            </div>
        `;

        // Add event listeners
        const checkbox = card.querySelector('.task-checkbox');
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            toggleTaskCompletion(activity.id, e.target.checked);
        });

        const editBtn = card.querySelector('.edit-task-btn');
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openEditModal(activity);
        });

        return card;
    }

    // Format activity type
    function formatActivityType(type) {
        return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }

    // Toggle task completion
    async function toggleTaskCompletion(activityId, isCompleted) {
        try {
            const response = await fetch(`/api/farm/activity/${activityId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: isCompleted ? 'completed' : 'pending',
                    completed_date: isCompleted ? formatDate(new Date()) : null
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update activity');
            }

            // Reload schedule
            await loadSchedule();
            showNotification(isCompleted ? 'Task completed!' : 'Task marked as pending', 'success');

        } catch (error) {
            console.error('Error updating activity:', error);
            showNotification('Failed to update task', 'error');
            // Reload to reset checkbox
            loadSchedule();
        }
    }

    // Update stats
    function updateStats() {
        const total = activities.length;
        const completed = activities.filter(a => a.status === 'completed').length;
        const pending = total - completed;

        totalTasks.textContent = total;
        completedTasks.textContent = completed;
        pendingTasks.textContent = pending;
    }

    // Open add modal
    function openAddModal() {
        editingActivityId = null;
        document.getElementById('modalTitle').textContent = 'Add Activity';
        activityForm.reset();
        document.getElementById('scheduledDate').value = formatDate(new Date());
        activityModal.classList.remove('hidden');
    }

    // Open edit modal
    function openEditModal(activity) {
        editingActivityId = activity.id;
        document.getElementById('modalTitle').textContent = 'Edit Activity';
        document.getElementById('activityId').value = activity.id;
        document.getElementById('activityType').value = activity.activity_type;
        document.getElementById('cropType').value = activity.crop_type || '';
        document.getElementById('scheduledDate').value = activity.scheduled_date;
        document.getElementById('description').value = activity.description || '';
        activityModal.classList.remove('hidden');
    }

    // Close activity modal
    function closeActivityModal() {
        activityModal.classList.add('hidden');
        activityForm.reset();
        editingActivityId = null;
    }

    // Handle activity form submit
    async function handleActivitySubmit(e) {
        e.preventDefault();

        const formData = {
            activity_type: document.getElementById('activityType').value,
            crop_type: document.getElementById('cropType').value,
            scheduled_date: document.getElementById('scheduledDate').value,
            description: document.getElementById('description').value
        };

        try {
            const url = editingActivityId 
                ? `/api/farm/activity/${editingActivityId}`
                : '/api/farm/activity';
            
            const method = editingActivityId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Failed to save activity');
            }

            closeActivityModal();
            await loadSchedule();
            showNotification(editingActivityId ? 'Activity updated!' : 'Activity added!', 'success');

        } catch (error) {
            console.error('Error saving activity:', error);
            showNotification('Failed to save activity', 'error');
        }
    }

    // Open generate modal
    function openGenerateModal() {
        generateForm.reset();
        generateModal.classList.remove('hidden');
    }

    // Close generate modal
    function closeGenModal() {
        generateModal.classList.add('hidden');
        generateForm.reset();
    }

    // Handle generate form submit
    async function handleGenerateSubmit(e) {
        e.preventDefault();

        const formData = {
            crop_type: document.getElementById('genCropType').value,
            growth_stage: document.getElementById('growthStage').value
        };

        try {
            // Show loading
            const submitBtn = generateForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
            submitBtn.disabled = true;

            const response = await fetch('/api/farm/generate-schedule', {
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
                throw new Error(data.error || 'Failed to generate schedule');
            }

            closeGenModal();
            await loadSchedule();
            
            // Show AI suggestions
            if (data.suggestions) {
                displayAISuggestions(data.suggestions);
            }

            showNotification('AI schedule generated successfully!', 'success');

        } catch (error) {
            console.error('Error generating schedule:', error);
            showNotification('Failed to generate schedule', 'error');
        } finally {
            const submitBtn = generateForm.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Generate';
            submitBtn.disabled = false;
        }
    }

    // Display AI suggestions
    function displayAISuggestions(suggestions) {
        aiSuggestions.innerHTML = '';

        if (Array.isArray(suggestions)) {
            suggestions.forEach(suggestion => {
                const div = document.createElement('div');
                div.className = 'bg-white rounded-lg p-4 border border-purple-100';
                div.innerHTML = `
                    <p class="text-sm text-gray-700">
                        <i class="fas fa-lightbulb text-yellow-500 mr-2"></i>
                        ${suggestion}
                    </p>
                `;
                aiSuggestions.appendChild(div);
            });
        }
    }

    // Format date to YYYY-MM-DD
    function formatDate(date) {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
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
