"""
Finance Service Module
Handles financial health scoring, cost analysis, and profit projections
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

# Simple cache for recommendations (speeds up repeated requests)
_recommendation_cache = {}
_cache_duration = 300  # 5 minutes in seconds

# Pre-computed default recommendations (instant response)
_default_recommendations_cache = None


def analyze_cost_efficiency(expenses, yield_data):
    """
    Analyze cost efficiency based on expenses and yield
    Returns efficiency score and breakdown
    """
    if not expenses:
        return {
            'efficiency_score': 0,
            'total_expenses': 0,
            'cost_per_kg': 0,
            'analysis': 'No expense data available'
        }
    
    # Calculate total expenses
    total_expenses = sum(expense.get('amount', 0) if expense.get('amount') is not None else 0 for expense in expenses)
    
    # Get yield information
    total_yield = 0
    if yield_data:
        if isinstance(yield_data, list):
            for y in yield_data:
                yield_val = y.get('actual_yield') or y.get('predicted_yield')
                if yield_val is not None:
                    try:
                        total_yield += float(yield_val)
                    except (ValueError, TypeError):
                        continue
        elif isinstance(yield_data, dict):
            yield_val = yield_data.get('actual_yield') or yield_data.get('predicted_yield')
            if yield_val is not None:
                try:
                    total_yield = float(yield_val)
                except (ValueError, TypeError):
                    total_yield = 0
    
    # Calculate cost per kg
    cost_per_kg = total_expenses / total_yield if total_yield > 0 else 0
    
    # Expense breakdown by category
    expense_by_category = {}
    for expense in expenses:
        category = expense.get('category', 'other')
        amount = expense.get('amount', 0) if expense.get('amount') is not None else 0
        expense_by_category[category] = expense_by_category.get(category, 0) + amount
    
    # Calculate efficiency score (0-100)
    # Lower cost per kg = higher efficiency
    # Benchmark: ₹10/kg is average, ₹5/kg is excellent, ₹20/kg is poor
    if cost_per_kg == 0:
        efficiency_score = 50  # Neutral if no data
    elif cost_per_kg <= 5:
        efficiency_score = 100
    elif cost_per_kg <= 10:
        efficiency_score = 80 - ((cost_per_kg - 5) * 6)  # 80-50
    elif cost_per_kg <= 20:
        efficiency_score = 50 - ((cost_per_kg - 10) * 3)  # 50-20
    else:
        efficiency_score = 20
    
    # Generate analysis
    if efficiency_score >= 80:
        analysis = "Excellent cost efficiency! Your production costs are well-optimized."
    elif efficiency_score >= 60:
        analysis = "Good cost efficiency. There's room for minor improvements."
    elif efficiency_score >= 40:
        analysis = "Moderate cost efficiency. Consider optimizing input costs."
    else:
        analysis = "Low cost efficiency. Focus on reducing production costs."
    
    return {
        'efficiency_score': round(efficiency_score, 2),
        'total_expenses': round(total_expenses, 2),
        'total_yield': round(total_yield, 2),
        'cost_per_kg': round(cost_per_kg, 2),
        'expense_breakdown': expense_by_category,
        'analysis': analysis
    }


def project_profit(yield_prediction, market_prices, costs):
    """
    Project profit based on yield prediction, market prices, and costs
    Returns profit projection and analysis
    """
    # Extract values
    predicted_yield = yield_prediction.get('predicted_yield', 0) if isinstance(yield_prediction, dict) else yield_prediction
    
    # Get market price (average if range provided)
    if isinstance(market_prices, dict):
        price_per_kg = market_prices.get('average_price', 20)
    elif isinstance(market_prices, (int, float)):
        price_per_kg = market_prices
    else:
        price_per_kg = 20  # Default
    
    # Calculate revenue
    projected_revenue = predicted_yield * price_per_kg
    
    # Calculate total costs
    total_costs = costs if isinstance(costs, (int, float)) else sum(costs.values()) if isinstance(costs, dict) else 0
    
    # Calculate profit
    projected_profit = projected_revenue - total_costs
    profit_margin = (projected_profit / projected_revenue * 100) if projected_revenue > 0 else 0
    
    # ROI calculation
    roi = (projected_profit / total_costs * 100) if total_costs > 0 else 0
    
    # Generate analysis
    if profit_margin >= 40:
        analysis = "Excellent profit margin! Your farm is highly profitable."
        recommendation = "Maintain current practices and consider expanding."
    elif profit_margin >= 25:
        analysis = "Good profit margin. Your farm is performing well."
        recommendation = "Look for opportunities to increase efficiency."
    elif profit_margin >= 10:
        analysis = "Moderate profit margin. There's room for improvement."
        recommendation = "Focus on reducing costs or improving yield quality."
    elif profit_margin >= 0:
        analysis = "Low profit margin. Immediate action needed."
        recommendation = "Review all expenses and explore better market prices."
    else:
        analysis = "Projected loss. Critical situation."
        recommendation = "Urgent: Reduce costs, improve yield, or find better markets."
    
    return {
        'projected_revenue': round(projected_revenue, 2),
        'total_costs': round(total_costs, 2),
        'projected_profit': round(projected_profit, 2),
        'profit_margin': round(profit_margin, 2),
        'roi': round(roi, 2),
        'analysis': analysis,
        'recommendation': recommendation
    }


def generate_recommendations(score_breakdown):
    """
    Generate AI-powered recommendations based on financial score breakdown
    Returns list of actionable recommendations
    """
    if not gemini_model:
        return generate_default_recommendations(score_breakdown)
    
    try:
        # Create cache key from score breakdown (rounded to reduce cache misses)
        cache_key = f"{round(score_breakdown.get('cost_efficiency_score', 50), -1)}_{round(score_breakdown.get('yield_performance_score', 50), -1)}_{round(score_breakdown.get('market_timing_score', 50), -1)}"
        
        # Check cache first
        if cache_key in _recommendation_cache:
            cached_data, cached_time = _recommendation_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < _cache_duration:
                return cached_data
        
        # Build context from score breakdown
        context = json.dumps(score_breakdown, indent=2)
        
        prompt = f"""As an agricultural financial advisor, analyze this farmer's financial health data and provide concise, actionable recommendations:

{context}

Provide exactly 4 SHORT recommendations to improve financial health. Keep each recommendation brief and focused.

Format as JSON array:
[
  {{
    "focus_area": "Category",
    "action": "Short specific action (max 10 words)",
    "impact": "High/Medium/Low",
    "difficulty": "Easy/Medium/Hard",
    "details": "One sentence explanation (max 15 words)"
  }}
]

Keep it concise and practical for Indian farmers."""
        
        response = gemini_model.generate_content(prompt)
        
        if response and response.text:
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            
            try:
                recommendations = json.loads(text)
                # Cache the result
                _recommendation_cache[cache_key] = (recommendations, datetime.now())
                return recommendations
            except json.JSONDecodeError:
                return generate_default_recommendations(score_breakdown)
    
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return generate_default_recommendations(score_breakdown)


def generate_default_recommendations(score_breakdown):
    """
    Generate default recommendations when AI is unavailable
    Fast fallback with cached results
    """
    global _default_recommendations_cache
    
    # Create cache key
    cache_key = f"default_{round(score_breakdown.get('cost_efficiency_score', 50), -1)}_{round(score_breakdown.get('yield_performance_score', 50), -1)}_{round(score_breakdown.get('market_timing_score', 50), -1)}"
    
    # Check if we have cached default recommendations
    if _default_recommendations_cache and cache_key in _default_recommendations_cache:
        return _default_recommendations_cache[cache_key]
    
    recommendations = []
    
    # Cost efficiency recommendations
    if score_breakdown.get('cost_efficiency_score', 50) < 60:
        recommendations.append({
            "focus_area": "Cost Reduction",
            "action": "Optimize fertilizer usage with soil testing",
            "impact": "High",
            "difficulty": "Medium",
            "details": "Apply only necessary fertilizers based on soil needs."
        })
    
    # Yield performance recommendations
    if score_breakdown.get('yield_performance_score', 50) < 60:
        recommendations.append({
            "focus_area": "Revenue Increase",
            "action": "Improve irrigation and pest control timing",
            "impact": "High",
            "difficulty": "Medium",
            "details": "Better timing increases yield quality and quantity."
        })
    
    # Market timing recommendations
    if score_breakdown.get('market_timing_score', 50) < 60:
        recommendations.append({
            "focus_area": "Revenue Increase",
            "action": "Monitor prices and sell at peak times",
            "impact": "Medium",
            "difficulty": "Easy",
            "details": "Track market trends to maximize selling price."
        })
    
    # General recommendation (always show)
    recommendations.append({
        "focus_area": "Efficiency",
        "action": "Track all farm expenses and yields",
        "impact": "Medium",
        "difficulty": "Easy",
        "details": "Good records help identify improvement areas."
    })
    
    # Cache the default recommendations
    if _default_recommendations_cache is None:
        _default_recommendations_cache = {}
    _default_recommendations_cache[cache_key] = recommendations
    
    return recommendations


def calculate_health_score(user_id):
    """
    Calculate overall financial health score for a farmer
    Returns score (0-100) with detailed breakdown
    """
    try:
        # Get user's financial data
        expenses = db.get_expenses(user_id) or []
        yield_predictions = db.get_yield_predictions(user_id) or []
        
        # Initialize scores
        cost_efficiency_score = 50  # Default neutral
        yield_performance_score = 50
        market_timing_score = 50
    except Exception as e:
        print(f"Error getting financial data: {e}")
        expenses = []
        yield_predictions = []
        cost_efficiency_score = 50
        yield_performance_score = 50
        market_timing_score = 50
    
    # Calculate cost efficiency score
    if expenses and yield_predictions:
        cost_analysis = analyze_cost_efficiency(expenses, yield_predictions)
        cost_efficiency_score = cost_analysis.get('efficiency_score', 50) or 50
    
    # Calculate yield performance score
    if yield_predictions:
        # Compare actual vs predicted yields
        total_predictions = 0
        accurate_predictions = 0
        total_yield_quality = 0
        
        for prediction in yield_predictions:
            total_predictions += 1
            actual_yield = prediction.get('actual_yield')
            predicted_yield = prediction.get('predicted_yield', 0)
            
            # Ensure values are numbers, not None
            if actual_yield is not None and predicted_yield is not None:
                actual_yield = float(actual_yield) if actual_yield else 0
                predicted_yield = float(predicted_yield) if predicted_yield else 0
                
                if actual_yield > 0:
                    # Check accuracy
                    accuracy = (actual_yield / predicted_yield) if predicted_yield > 0 else 0
                    if 0.8 <= accuracy <= 1.2:  # Within 20% is good
                        accurate_predictions += 1
                    
                    # Quality score
                    quality = prediction.get('actual_quality', 'B')
                    quality_scores = {'A': 100, 'B': 70, 'C': 40}
                    total_yield_quality += quality_scores.get(quality, 50)
        
        if total_predictions > 0:
            accuracy_score = (accurate_predictions / total_predictions) * 50
            quality_score = (total_yield_quality / total_predictions) * 0.5 if total_yield_quality > 0 else 25
            yield_performance_score = accuracy_score + quality_score
    
    # Calculate market timing score (simplified - based on profit margins)
    if expenses and yield_predictions:
        # Get recent expenses
        recent_expenses = expenses[:10] if len(expenses) > 10 else expenses
        total_recent_expenses = sum(e.get('amount', 0) if e.get('amount') is not None else 0 for e in recent_expenses)
        
        # Estimate revenue based on predictions
        recent_predictions = yield_predictions[:5] if len(yield_predictions) > 5 else yield_predictions
        estimated_revenue = 0
        for pred in recent_predictions:
            yield_amount = pred.get('actual_yield') or pred.get('predicted_yield')
            # Ensure yield_amount is a number and not None
            if yield_amount is not None:
                try:
                    yield_amount = float(yield_amount)
                    if yield_amount > 0:
                        # Assume average price of ₹20/kg
                        estimated_revenue += yield_amount * 20
                except (ValueError, TypeError):
                    continue
        
        if estimated_revenue > 0:
            profit_margin = ((estimated_revenue - total_recent_expenses) / estimated_revenue) * 100
            if profit_margin >= 40:
                market_timing_score = 90
            elif profit_margin >= 25:
                market_timing_score = 75
            elif profit_margin >= 10:
                market_timing_score = 60
            elif profit_margin >= 0:
                market_timing_score = 40
            else:
                market_timing_score = 20
    
    # Calculate overall score (weighted average)
    overall_score = (
        cost_efficiency_score * 0.35 +
        yield_performance_score * 0.40 +
        market_timing_score * 0.25
    )
    
    # Calculate financial metrics
    total_expenses = sum(e.get('amount', 0) if e.get('amount') is not None else 0 for e in expenses) if expenses else 0
    
    # Estimate revenue from yield predictions
    projected_revenue = 0
    if yield_predictions:
        for pred in yield_predictions:
            yield_amount = pred.get('actual_yield') or pred.get('predicted_yield')
            # Ensure yield_amount is a number and not None
            if yield_amount is not None:
                try:
                    yield_amount = float(yield_amount)
                    if yield_amount > 0:
                        # Assume average price of ₹20/kg
                        projected_revenue += yield_amount * 20
                except (ValueError, TypeError):
                    continue
    
    # Calculate profit margin and ROI
    net_profit = projected_revenue - total_expenses
    profit_margin = ((net_profit / projected_revenue) * 100) if projected_revenue > 0 else 0
    roi = ((net_profit / total_expenses) * 100) if total_expenses > 0 else 0
    
    # Prepare detailed breakdown
    score_breakdown = {
        'cost_efficiency_score': round(cost_efficiency_score, 2),
        'yield_performance_score': round(yield_performance_score, 2),
        'market_timing_score': round(market_timing_score, 2),
        'total_expenses': total_expenses,
        'projected_revenue': projected_revenue,
        'net_profit': net_profit,
        'profit_margin': round(profit_margin, 2),
        'roi': round(roi, 2),
        'number_of_predictions': len(yield_predictions),
        'number_of_expenses': len(expenses)
    }
    
    # Add cost analysis if available
    if expenses and yield_predictions:
        cost_analysis = analyze_cost_efficiency(expenses, yield_predictions)
        score_breakdown['cost_analysis'] = cost_analysis
    
    # Generate recommendations
    recommendations = generate_recommendations(score_breakdown)
    score_breakdown['recommendations'] = recommendations
    
    # Save score to database
    db.save_financial_score(
        user_id=user_id,
        overall_score=overall_score,
        score_breakdown=score_breakdown
    )
    
    # Determine health status
    if overall_score >= 80:
        health_status = "Excellent"
        status_message = "Your farm's financial health is excellent! Keep up the great work."
    elif overall_score >= 60:
        health_status = "Good"
        status_message = "Your farm's financial health is good. There are opportunities for improvement."
    elif overall_score >= 40:
        health_status = "Fair"
        status_message = "Your farm's financial health is fair. Focus on the recommendations to improve."
    else:
        health_status = "Needs Improvement"
        status_message = "Your farm's financial health needs attention. Follow the recommendations carefully."
    
    return {
        'overall_score': round(overall_score, 2),
        'health_status': health_status,
        'status_message': status_message,
        'cost_efficiency_score': round(cost_efficiency_score, 2),
        'yield_performance_score': round(yield_performance_score, 2),
        'market_timing_score': round(market_timing_score, 2),
        'breakdown': score_breakdown,
        'score_breakdown': score_breakdown,  # For backward compatibility
        'recommendations': recommendations,  # Top-level for easy access
        'success': True
    }
