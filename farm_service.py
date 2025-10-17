"""
Farm Service Module
Handles autonomous farm planning, task recommendations, and schedule generation
"""

import os
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from database import DatabaseManager

# Initialize Gemini AI
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

db = DatabaseManager()

# Cache for AI-generated schedules (speeds up repeated requests)
_schedule_cache = {}
_cache_duration = 600  # 10 minutes


def calculate_growth_stage(planting_date, crop_type):
    """
    Calculate current growth stage based on planting date and crop type
    Returns growth stage and days since planting
    """
    if isinstance(planting_date, str):
        planting_date = datetime.strptime(planting_date, '%Y-%m-%d').date()
    
    days_since_planting = (datetime.now().date() - planting_date).days
    
    # Growth stage definitions (in days) for common crops
    growth_stages = {
        'rice': {
            'germination': (0, 10),
            'seedling': (11, 30),
            'tillering': (31, 60),
            'flowering': (61, 90),
            'grain_filling': (91, 110),
            'maturity': (111, 140)
        },
        'wheat': {
            'germination': (0, 7),
            'seedling': (8, 25),
            'tillering': (26, 60),
            'flowering': (61, 90),
            'grain_filling': (91, 110),
            'maturity': (111, 130)
        },
        'tomato': {
            'germination': (0, 7),
            'seedling': (8, 21),
            'vegetative': (22, 45),
            'flowering': (46, 65),
            'fruiting': (66, 90),
            'harvest': (91, 120)
        },
        'potato': {
            'sprouting': (0, 14),
            'vegetative': (15, 45),
            'tuber_initiation': (46, 70),
            'tuber_bulking': (71, 100),
            'maturity': (101, 120)
        },
        'corn': {
            'germination': (0, 10),
            'seedling': (11, 30),
            'vegetative': (31, 60),
            'tasseling': (61, 75),
            'grain_filling': (76, 100),
            'maturity': (101, 120)
        },
        'default': {
            'early': (0, 30),
            'mid': (31, 60),
            'late': (61, 90),
            'harvest': (91, 120)
        }
    }
    
    # Get crop-specific stages or use default
    crop_lower = crop_type.lower()
    stages = growth_stages.get(crop_lower, growth_stages['default'])
    
    # Determine current stage
    current_stage = 'unknown'
    for stage_name, (start, end) in stages.items():
        if start <= days_since_planting <= end:
            current_stage = stage_name
            break
    
    if current_stage == 'unknown':
        if days_since_planting > max([end for _, end in stages.values()]):
            current_stage = 'post_harvest'
        else:
            current_stage = 'early'
    
    return {
        'stage': current_stage,
        'days_since_planting': days_since_planting,
        'crop_type': crop_type
    }


def adjust_for_weather(tasks, weather_forecast):
    """
    Adjust task recommendations based on weather forecast
    Returns modified tasks with weather-based adjustments
    """
    if not weather_forecast:
        return tasks
    
    adjusted_tasks = []
    
    for task in tasks:
        task_copy = task.copy()
        adjustments = []
        
        # Check for rain
        if 'rain' in weather_forecast.get('description', '').lower():
            if task.get('activity_type') in ['irrigation', 'spraying', 'fertilization']:
                adjustments.append("⚠️ Postpone due to rain forecast")
                task_copy['weather_note'] = "Rain expected - consider rescheduling"
            elif task.get('activity_type') == 'harvesting':
                adjustments.append("⚠️ Harvest before rain if possible")
                task_copy['weather_note'] = "Rain expected - harvest urgently if crop is ready"
        
        # Check for high temperature
        if weather_forecast.get('temperature', 0) > 35:
            if task.get('activity_type') in ['transplanting', 'spraying']:
                adjustments.append("🌡️ Perform early morning or evening due to heat")
                task_copy['weather_note'] = "High temperature - schedule for cooler hours"
        
        # Check for strong wind
        if weather_forecast.get('wind_speed', 0) > 20:
            if task.get('activity_type') == 'spraying':
                adjustments.append("💨 Avoid spraying due to strong wind")
                task_copy['weather_note'] = "Strong wind - postpone spraying"
        
        # Check for low humidity
        if weather_forecast.get('humidity', 100) < 30:
            if task.get('activity_type') == 'irrigation':
                adjustments.append("💧 Increase irrigation due to low humidity")
                task_copy['weather_note'] = "Low humidity - increase water application"
        
        if adjustments:
            task_copy['adjustments'] = adjustments
        
        adjusted_tasks.append(task_copy)
    
    return adjusted_tasks


def get_task_recommendations(crop, season, weather=None):
    """
    Get AI-powered task recommendations based on crop, season, and weather
    Returns list of recommended tasks
    """
    if not gemini_model:
        return get_default_task_recommendations(crop, season)
    
    try:
        weather_info = ""
        if weather:
            weather_info = f"\nCurrent weather: {weather.get('description', 'N/A')}, Temperature: {weather.get('temperature', 'N/A')}°C, Humidity: {weather.get('humidity', 'N/A')}%"
        
        prompt = f"""As an agricultural expert, provide specific farming task recommendations for:
Crop: {crop}
Season: {season}
{weather_info}

Provide 5-7 specific, actionable tasks that a farmer should perform this week. For each task, include:
1. Task name
2. Brief description (1-2 sentences)
3. Priority (High/Medium/Low)
4. Best time to perform

Format your response as a JSON array with this structure:
[
  {{
    "task": "Task name",
    "description": "Brief description",
    "priority": "High/Medium/Low",
    "timing": "Best time to perform"
  }}
]

Focus on practical, season-appropriate tasks."""
        
        response = gemini_model.generate_content(prompt)
        
        if response and response.text:
            # Try to extract JSON from response
            text = response.text.strip()
            # Remove markdown code blocks if present
            text = text.replace('```json', '').replace('```', '').strip()
            
            try:
                tasks = json.loads(text)
                return tasks
            except json.JSONDecodeError:
                # If JSON parsing fails, return default recommendations
                return get_default_task_recommendations(crop, season)
    
    except Exception as e:
        print(f"Error getting task recommendations: {e}")
        return get_default_task_recommendations(crop, season)


def get_default_task_recommendations(crop, season):
    """
    Fallback task recommendations when AI is unavailable
    """
    default_tasks = [
        {
            "task": "Inspect crop health",
            "description": "Check plants for signs of disease, pests, or nutrient deficiency",
            "priority": "High",
            "timing": "Early morning"
        },
        {
            "task": "Irrigation management",
            "description": "Ensure adequate water supply based on crop stage and weather",
            "priority": "High",
            "timing": "Early morning or evening"
        },
        {
            "task": "Weed control",
            "description": "Remove weeds to prevent competition for nutrients and water",
            "priority": "Medium",
            "timing": "Any time"
        },
        {
            "task": "Fertilizer application",
            "description": "Apply appropriate fertilizers based on crop growth stage",
            "priority": "Medium",
            "timing": "Morning"
        },
        {
            "task": "Pest monitoring",
            "description": "Check for pest activity and apply control measures if needed",
            "priority": "High",
            "timing": "Evening"
        }
    ]
    
    return default_tasks


def generate_weekly_schedule(user_id, crop_type, growth_stage=None):
    """
    Generate AI-powered weekly schedule for farm activities
    Returns a list of scheduled tasks for the week
    """
    if not gemini_model:
        return generate_default_schedule(user_id, crop_type, growth_stage)
    
    try:
        # Determine growth stage if not provided
        if not growth_stage:
            recent_activities = db.get_activity_history(user_id, limit=10)
            planting_activity = next(
                (a for a in recent_activities if a.get('activity_type') == 'planting'),
                None
            )
            if planting_activity:
                planting_date = planting_activity.get('scheduled_date')
                stage_info = calculate_growth_stage(planting_date, crop_type)
                growth_stage = stage_info['stage']
            else:
                growth_stage = 'vegetative'  # Default
        
        # Check cache first
        cache_key = f"{crop_type}_{growth_stage}"
        if cache_key in _schedule_cache:
            cached_data, cached_time = _schedule_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < _cache_duration:
                # Return cached schedule but save with new dates for this user
                return _apply_cached_schedule(user_id, crop_type, cached_data)
        
        # Shorter, simpler prompt - only essential tasks
        prompt = f"""Create a simple 7-day farm schedule for {crop_type} ({growth_stage} stage).

Format as JSON:
[
  {{
    "day": "Monday",
    "tasks": [
      {{
        "activity_type": "irrigation/fertilization/pest_control/weeding/monitoring",
        "description": "Short task (max 8 words)",
        "priority": "High/Medium/Low"
      }}
    ]
  }}
]

Include only 1-2 ESSENTIAL tasks per day. Keep it simple and manageable."""
        
        response = gemini_model.generate_content(prompt)
        
        if response and response.text:
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            
            try:
                schedule = json.loads(text)
                
                # Cache the schedule
                _schedule_cache[cache_key] = (schedule, datetime.now())
                
                # Save tasks to database with correct dates
                today = datetime.now().date()
                current_day = today.weekday()  # 0=Monday, 6=Sunday
                
                for day_schedule in schedule:
                    day_name = day_schedule.get('day', 'Monday')
                    target_day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(day_name)
                    
                    # Calculate days from today to target day
                    days_ahead = target_day - current_day
                    if days_ahead < 0:  # If day has passed this week, schedule for next week
                        days_ahead += 7
                    
                    task_date = today + timedelta(days=days_ahead)
                    
                    for task in day_schedule.get('tasks', []):
                        db.save_farm_activity(
                            user_id=user_id,
                            activity_type=task.get('activity_type', 'monitoring'),
                            crop_type=crop_type,
                            scheduled_date=task_date.strftime('%Y-%m-%d'),
                            description=task.get('description', ''),
                            ai_generated=True
                        )
                
                return schedule
            
            except json.JSONDecodeError:
                return generate_default_schedule(user_id, crop_type, growth_stage)
    
    except Exception as e:
        print(f"Error generating weekly schedule: {e}")
        return generate_default_schedule(user_id, crop_type, growth_stage)


def _apply_cached_schedule(user_id, crop_type, cached_schedule):
    """
    Apply cached schedule with current dates for a user
    """
    today = datetime.now().date()
    current_day = today.weekday()  # 0=Monday, 6=Sunday
    
    for day_schedule in cached_schedule:
        day_name = day_schedule.get('day', 'Monday')
        target_day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(day_name)
        
        # Calculate days from today to target day
        days_ahead = target_day - current_day
        if days_ahead < 0:  # If day has passed this week, schedule for next week
            days_ahead += 7
        
        task_date = today + timedelta(days=days_ahead)
        
        for task in day_schedule.get('tasks', []):
            db.save_farm_activity(
                user_id=user_id,
                activity_type=task.get('activity_type', 'monitoring'),
                crop_type=crop_type,
                scheduled_date=task_date.strftime('%Y-%m-%d'),
                description=task.get('description', ''),
                ai_generated=True
            )
    
    return cached_schedule


def generate_default_schedule(user_id, crop_type, growth_stage):
    """
    Generate simple default weekly schedule when AI is unavailable
    Only essential tasks - manageable for farmers
    """
    today = datetime.now().date()
    current_day = today.weekday()  # 0=Monday, 6=Sunday
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    schedule = []
    
    # Simple weekly pattern - only 1 task per day
    weekly_pattern = [
        {"activity_type": "monitoring", "description": f"Check {crop_type} health", "priority": "High"},
        {"activity_type": "irrigation", "description": f"Water {crop_type} plants", "priority": "High"},
        {"activity_type": "weeding", "description": "Remove weeds", "priority": "Medium"},
        {"activity_type": "monitoring", "description": f"Inspect {crop_type} for pests", "priority": "High"},
        {"activity_type": "fertilization", "description": f"Apply fertilizer to {crop_type}", "priority": "Medium"},
        {"activity_type": "irrigation", "description": f"Water {crop_type} plants", "priority": "High"},
        {"activity_type": "monitoring", "description": f"Check {crop_type} growth", "priority": "Medium"}
    ]
    
    for i, day in enumerate(days):
        target_day = i
        days_ahead = target_day - current_day
        if days_ahead < 0:
            days_ahead += 7
        
        task_date = today + timedelta(days=days_ahead)
        task = weekly_pattern[i]
        
        schedule.append({
            "day": day,
            "date": task_date.strftime('%Y-%m-%d'),
            "tasks": [task]  # Only 1 task per day
        })
        
        # Save to database
        db.save_farm_activity(
            user_id=user_id,
            activity_type=task['activity_type'],
            crop_type=crop_type,
            scheduled_date=task_date.strftime('%Y-%m-%d'),
            description=task['description'],
            ai_generated=True
        )
    
    return schedule
