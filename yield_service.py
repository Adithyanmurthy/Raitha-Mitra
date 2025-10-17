"""
Yield Service Module
Handles yield prediction, confidence scoring, and preparation checklists
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


def calculate_confidence(data_completeness, weather_stability):
    """
    Calculate confidence score for yield prediction
    Returns confidence score (0-100)
    """
    # Data completeness score (0-50 points)
    completeness_score = data_completeness * 50
    
    # Weather stability score (0-50 points)
    stability_score = weather_stability * 50
    
    # Total confidence
    confidence = completeness_score + stability_score
    
    # Ensure within bounds
    confidence = max(0, min(100, confidence))
    
    return round(confidence, 2)


def compare_with_regional_average(crop, region, predicted_yield):
    """
    Compare predicted yield with regional averages
    Returns comparison data and insights
    """
    # Regional average yields (kg per hectare) - sample data
    regional_averages = {
        'rice': {
            'Karnataka': 3500,
            'Punjab': 4200,
            'West Bengal': 2800,
            'Tamil Nadu': 3200,
            'default': 3000
        },
        'wheat': {
            'Punjab': 4500,
            'Haryana': 4300,
            'Uttar Pradesh': 3200,
            'Madhya Pradesh': 2800,
            'default': 3500
        },
        'tomato': {
            'Karnataka': 25000,
            'Maharashtra': 22000,
            'Andhra Pradesh': 24000,
            'Tamil Nadu': 23000,
            'default': 23000
        },
        'potato': {
            'Uttar Pradesh': 22000,
            'West Bengal': 24000,
            'Bihar': 20000,
            'Punjab': 26000,
            'default': 23000
        },
        'corn': {
            'Karnataka': 4500,
            'Andhra Pradesh': 5000,
            'Bihar': 3500,
            'Rajasthan': 3000,
            'default': 4000
        }
    }
    
    crop_lower = crop.lower()
    
    # Get regional average
    crop_data = regional_averages.get(crop_lower, {})
    regional_avg = crop_data.get(region, crop_data.get('default', 3000))
    
    # Calculate difference
    difference = predicted_yield - regional_avg
    percentage_diff = (difference / regional_avg) * 100 if regional_avg > 0 else 0
    
    # Generate insight
    if percentage_diff > 20:
        insight = f"Excellent! Your predicted yield is {abs(percentage_diff):.1f}% above the regional average."
        performance = "Above Average"
    elif percentage_diff > 0:
        insight = f"Good! Your predicted yield is {abs(percentage_diff):.1f}% above the regional average."
        performance = "Above Average"
    elif percentage_diff > -10:
        insight = f"Your predicted yield is close to the regional average (within {abs(percentage_diff):.1f}%)."
        performance = "Average"
    else:
        insight = f"Your predicted yield is {abs(percentage_diff):.1f}% below the regional average. Consider improving farming practices."
        performance = "Below Average"
    
    return {
        'regional_average': regional_avg,
        'predicted_yield': predicted_yield,
        'difference': difference,
        'percentage_difference': round(percentage_diff, 2),
        'performance': performance,
        'insight': insight
    }


def generate_preparation_checklist(predicted_yield, harvest_date):
    """
    Generate preparation checklist based on predicted yield and harvest date
    Returns list of action items
    """
    if isinstance(harvest_date, str):
        harvest_date = datetime.strptime(harvest_date, '%Y-%m-%d').date()
    
    days_until_harvest = (harvest_date - datetime.now().date()).days
    
    checklist = []
    
    # Immediate actions (more than 30 days before harvest)
    if days_until_harvest > 30:
        checklist.append({
            "category": "Crop Management",
            "action": "Continue regular monitoring and maintenance",
            "priority": "Medium",
            "timing": "Ongoing",
            "description": "Monitor crop health, manage pests and diseases"
        })
        checklist.append({
            "category": "Nutrition",
            "action": "Apply final fertilizer dose if needed",
            "priority": "High",
            "timing": f"{days_until_harvest - 20} days before harvest",
            "description": "Ensure adequate nutrition for optimal yield"
        })
    
    # Pre-harvest actions (15-30 days before)
    if days_until_harvest > 15:
        checklist.append({
            "category": "Storage",
            "action": "Prepare storage facilities",
            "priority": "High",
            "timing": "2-3 weeks before harvest",
            "description": "Clean and prepare storage areas, check for pests"
        })
        checklist.append({
            "category": "Equipment",
            "action": "Service harvesting equipment",
            "priority": "High",
            "timing": "2 weeks before harvest",
            "description": "Ensure all equipment is in working condition"
        })
        checklist.append({
            "category": "Labor",
            "action": "Arrange harvesting labor",
            "priority": "High",
            "timing": "2 weeks before harvest",
            "description": f"Arrange workers for harvesting approximately {predicted_yield} kg"
        })
    
    # Immediate pre-harvest (less than 15 days)
    if days_until_harvest <= 15:
        checklist.append({
            "category": "Market",
            "action": "Check market prices and arrange buyers",
            "priority": "High",
            "timing": "1-2 weeks before harvest",
            "description": "Get best prices for your produce"
        })
        checklist.append({
            "category": "Transport",
            "action": "Arrange transportation",
            "priority": "High",
            "timing": "1 week before harvest",
            "description": f"Arrange vehicles for transporting {predicted_yield} kg"
        })
        checklist.append({
            "category": "Irrigation",
            "action": "Stop irrigation before harvest",
            "priority": "Medium",
            "timing": "3-5 days before harvest",
            "description": "Allow crop to dry for easier harvesting"
        })
    
    # Post-harvest planning
    checklist.append({
        "category": "Post-Harvest",
        "action": "Plan for grading and packaging",
        "priority": "Medium",
        "timing": "Before harvest",
        "description": "Prepare for sorting, grading, and packaging produce"
    })
    
    # Quality control
    if predicted_yield > 5000:  # Large yield
        checklist.append({
            "category": "Quality Control",
            "action": "Arrange quality testing",
            "priority": "Medium",
            "timing": "At harvest",
            "description": "Ensure produce meets quality standards for better prices"
        })
    
    return checklist


def predict_yield(user_id, crop_type, planting_date, farm_data=None):
    """
    Predict crop yield using AI and historical data
    Returns prediction with confidence score and recommendations
    """
    if isinstance(planting_date, str):
        planting_date = datetime.strptime(planting_date, '%Y-%m-%d').date()
    
    # Get user's historical data
    user_predictions = db.get_yield_predictions(user_id)
    user_activities = db.get_activity_history(user_id, limit=50)
    
    # Calculate data completeness
    data_points = 0
    total_possible = 5
    
    if farm_data:
        if farm_data.get('area'):
            data_points += 1
        if farm_data.get('soil_type'):
            data_points += 1
        if farm_data.get('irrigation_type'):
            data_points += 1
    
    if user_activities:
        data_points += 1
    
    if user_predictions:
        data_points += 1
    
    data_completeness = data_points / total_possible
    
    # Assume moderate weather stability (in production, use actual weather data)
    weather_stability = 0.7
    
    # Calculate confidence
    confidence_score = calculate_confidence(data_completeness, weather_stability)
    
    # Use AI for prediction if available
    if gemini_model and farm_data:
        try:
            # Build context
            context = f"""Crop: {crop_type}
Planting Date: {planting_date}
Days Since Planting: {(datetime.now().date() - planting_date).days}
"""
            
            if farm_data.get('area'):
                context += f"Farm Area: {farm_data['area']} hectares\n"
            if farm_data.get('soil_type'):
                context += f"Soil Type: {farm_data['soil_type']}\n"
            if farm_data.get('irrigation_type'):
                context += f"Irrigation: {farm_data['irrigation_type']}\n"
            if farm_data.get('location'):
                context += f"Location: {farm_data['location']}\n"
            
            # Add activity context
            if user_activities:
                context += "\nRecent Farm Activities:\n"
                for activity in user_activities[:5]:
                    context += f"- {activity.get('activity_type')}: {activity.get('description', 'N/A')}\n"
            
            prompt = f"""As an agricultural expert, predict the crop yield based on the following information:

{context}

Provide a yield prediction with:
1. Estimated total yield (in kg)
2. Expected quality grade (A/B/C)
3. Estimated harvest date
4. Key factors affecting yield
5. Recommendations for maximizing yield

Format as JSON:
{{
  "predicted_yield_kg": number,
  "quality_grade": "A/B/C",
  "harvest_date": "YYYY-MM-DD",
  "factors": ["factor1", "factor2", ...],
  "recommendations": ["rec1", "rec2", ...]
}}"""
            
            response = gemini_model.generate_content(prompt)
            
            if response and response.text:
                text = response.text.strip()
                text = text.replace('```json', '').replace('```', '').strip()
                
                try:
                    prediction_data = json.loads(text)
                    
                    predicted_yield = prediction_data.get('predicted_yield_kg', 0)
                    quality_grade = prediction_data.get('quality_grade', 'B')
                    harvest_date = prediction_data.get('harvest_date')
                    
                    if harvest_date:
                        harvest_date = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                    else:
                        # Default harvest date based on crop
                        days_to_harvest = 120  # Default
                        harvest_date = planting_date + timedelta(days=days_to_harvest)
                    
                    # Save prediction
                    factors_considered = {
                        'weather_score': weather_stability,
                        'data_completeness': data_completeness,
                        'ai_factors': prediction_data.get('factors', [])
                    }
                    
                    prediction_id = db.save_yield_prediction(
                        user_id=user_id,
                        crop_type=crop_type,
                        planting_date=planting_date.strftime('%Y-%m-%d'),
                        predicted_yield=predicted_yield,
                        confidence_score=confidence_score,
                        predicted_quality=quality_grade,
                        harvest_date=harvest_date.strftime('%Y-%m-%d'),
                        factors_considered=factors_considered
                    )
                    
                    # Generate preparation checklist
                    checklist = generate_preparation_checklist(predicted_yield, harvest_date)
                    
                    # Compare with regional average
                    region = farm_data.get('location', 'Karnataka')
                    comparison = compare_with_regional_average(crop_type, region, predicted_yield)
                    
                    return {
                        'prediction_id': prediction_id,
                        'predicted_yield': predicted_yield,
                        'quality_grade': quality_grade,
                        'predicted_quality': quality_grade,  # For backward compatibility
                        'confidence_score': confidence_score,
                        'planting_date': planting_date.strftime('%Y-%m-%d'),
                        'harvest_date': harvest_date.strftime('%Y-%m-%d'),
                        'days_until_harvest': (harvest_date - datetime.now().date()).days,
                        'factors': prediction_data.get('factors', []),
                        'recommendations': prediction_data.get('recommendations', []),
                        'preparation_checklist': checklist,
                        'regional_comparison': comparison,
                        'success': True
                    }
                
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            print(f"Error in AI yield prediction: {e}")
    
    # Fallback to default prediction
    return generate_default_prediction(user_id, crop_type, planting_date, farm_data, confidence_score)


def generate_default_prediction(user_id, crop_type, planting_date, farm_data, confidence_score):
    """
    Generate default yield prediction when AI is unavailable
    """
    # Default yields per hectare
    default_yields = {
        'rice': 3000,
        'wheat': 3500,
        'tomato': 23000,
        'potato': 23000,
        'corn': 4000,
        'onion': 20000,
        'cotton': 1500,
        'sugarcane': 70000
    }
    
    crop_lower = crop_type.lower()
    base_yield_per_hectare = default_yields.get(crop_lower, 2000)
    
    # Calculate yield based on area
    area = farm_data.get('area', 1) if farm_data else 1
    predicted_yield = base_yield_per_hectare * area
    
    # Adjust based on data quality
    if confidence_score < 50:
        predicted_yield *= 0.8  # Reduce prediction if low confidence
    
    # Default harvest dates (days from planting)
    harvest_days = {
        'rice': 120,
        'wheat': 120,
        'tomato': 90,
        'potato': 100,
        'corn': 110,
        'onion': 120,
        'cotton': 150,
        'sugarcane': 365
    }
    
    days_to_harvest = harvest_days.get(crop_lower, 120)
    harvest_date = planting_date + timedelta(days=days_to_harvest)
    
    # Save prediction
    factors_considered = {
        'weather_score': 0.7,
        'data_completeness': confidence_score / 100,
        'method': 'default'
    }
    
    prediction_id = db.save_yield_prediction(
        user_id=user_id,
        crop_type=crop_type,
        planting_date=planting_date.strftime('%Y-%m-%d'),
        predicted_yield=predicted_yield,
        confidence_score=confidence_score,
        predicted_quality='B',
        harvest_date=harvest_date.strftime('%Y-%m-%d'),
        factors_considered=factors_considered
    )
    
    # Generate checklist
    checklist = generate_preparation_checklist(predicted_yield, harvest_date)
    
    # Regional comparison
    region = farm_data.get('location', 'Karnataka') if farm_data else 'Karnataka'
    comparison = compare_with_regional_average(crop_type, region, predicted_yield)
    
    return {
        'prediction_id': prediction_id,
        'predicted_yield': round(predicted_yield, 2),
        'quality_grade': 'B',
        'predicted_quality': 'B',  # For backward compatibility
        'confidence_score': confidence_score,
        'planting_date': planting_date.strftime('%Y-%m-%d'),
        'harvest_date': harvest_date.strftime('%Y-%m-%d'),
        'days_until_harvest': (harvest_date - datetime.now().date()).days,
        'factors': ['Area', 'Crop type', 'Historical averages'],
        'recommendations': [
            'Monitor crop health regularly',
            'Ensure adequate irrigation',
            'Apply fertilizers as per schedule',
            'Control pests and diseases promptly'
        ],
        'preparation_checklist': checklist,
        'regional_comparison': comparison,
        'success': True
    }
