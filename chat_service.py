"""
Chat Service Module
Handles intelligent chat interactions with context memory using Gemini AI
"""

import os
import re
import json
from datetime import datetime
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


def extract_farming_context(message):
    """
    Extract farming context from message (crops, issues, seasons)
    Returns a dictionary with identified entities
    """
    context = {
        'crops': [],
        'issues': [],
        'seasons': [],
        'activities': []
    }
    
    # Common crop names
    crops = [
        'rice', 'wheat', 'corn', 'maize', 'tomato', 'potato', 'onion', 'garlic',
        'apple', 'banana', 'mango', 'grape', 'orange', 'cotton', 'sugarcane',
        'soybean', 'groundnut', 'chickpea', 'lentil', 'pepper', 'chili', 'cucumber',
        'carrot', 'cabbage', 'cauliflower', 'brinjal', 'eggplant', 'okra', 'pumpkin'
    ]
    
    # Common issues/diseases
    issues = [
        'blight', 'rust', 'rot', 'wilt', 'mold', 'fungus', 'pest', 'insect',
        'disease', 'infection', 'yellowing', 'wilting', 'spots', 'scab', 'aphid',
        'caterpillar', 'beetle', 'mite', 'virus', 'bacteria', 'nematode'
    ]
    
    # Seasons
    seasons = ['summer', 'winter', 'monsoon', 'spring', 'autumn', 'rainy', 'dry']
    
    # Activities
    activities = [
        'planting', 'sowing', 'harvesting', 'irrigation', 'fertilizer', 'pesticide',
        'pruning', 'weeding', 'mulching', 'transplanting'
    ]
    
    message_lower = message.lower()
    
    # Extract crops
    for crop in crops:
        if crop in message_lower:
            context['crops'].append(crop)
    
    # Extract issues
    for issue in issues:
        if issue in message_lower:
            context['issues'].append(issue)
    
    # Extract seasons
    for season in seasons:
        if season in message_lower:
            context['seasons'].append(season)
    
    # Extract activities
    for activity in activities:
        if activity in message_lower:
            context['activities'].append(activity)
    
    return context


def build_context_prompt(user_id, message):
    """
    Build context-aware prompt including user history and profile
    """
    # Get recent conversation history
    recent_messages = db.get_recent_context(user_id, limit=5)
    
    # Get user profile
    user = db.get_user_by_email_or_mobile(str(user_id))  # Simplified - in production use proper user lookup
    
    # Extract context from current message
    current_context = extract_farming_context(message)
    
    # Build context summary
    context_parts = []
    
    # Add user location if available
    if user and user.get('location'):
        context_parts.append(f"Farmer location: {user['location']}")
    
    # Add conversation history
    if recent_messages:
        context_parts.append("\nRecent conversation context:")
        for msg in recent_messages[-3:]:  # Last 3 messages
            if msg.get('context_data'):
                ctx = msg['context_data']
                if ctx.get('crops'):
                    context_parts.append(f"- Previously discussed crops: {', '.join(ctx['crops'])}")
                if ctx.get('issues'):
                    context_parts.append(f"- Previously discussed issues: {', '.join(ctx['issues'])}")
    
    # Add current context
    if current_context['crops']:
        context_parts.append(f"\nCurrent query involves: {', '.join(current_context['crops'])}")
    if current_context['issues']:
        context_parts.append(f"Issues mentioned: {', '.join(current_context['issues'])}")
    if current_context['seasons']:
        context_parts.append(f"Season context: {', '.join(current_context['seasons'])}")
    if current_context['activities']:
        context_parts.append(f"Activities mentioned: {', '.join(current_context['activities'])}")
    
    context_summary = "\n".join(context_parts) if context_parts else "No previous context available."
    
    return context_summary, current_context


def get_conversation_summary(user_id, limit=10):
    """
    Get conversation summary for context building
    Returns a formatted summary of recent conversations
    """
    messages = db.get_recent_context(user_id, limit=limit)
    
    if not messages:
        return "No previous conversations."
    
    summary_parts = []
    for msg in messages:
        timestamp = msg.get('created_at', '')
        user_msg = msg.get('message', '')
        bot_response = msg.get('response', '')
        
        # Truncate long messages
        if len(user_msg) > 100:
            user_msg = user_msg[:100] + "..."
        if len(bot_response) > 150:
            bot_response = bot_response[:150] + "..."
        
        summary_parts.append(f"User: {user_msg}")
        summary_parts.append(f"Assistant: {bot_response}")
        summary_parts.append("---")
    
    return "\n".join(summary_parts)


def generate_contextual_response(user_id, message, language='en'):
    """
    Generate AI response with context using Gemini AI
    Returns the response text and extracted context
    """
    if not gemini_model:
        return {
            'response': "I'm sorry, the AI service is currently unavailable. Please try again later.",
            'context': {},
            'error': 'AI service not configured'
        }
    
    try:
        # Build context
        context_summary, extracted_context = build_context_prompt(user_id, message)
        
        # Language mapping
        language_names = {
            'en': 'English',
            'hi': 'Hindi',
            'kn': 'Kannada',
            'te': 'Telugu',
            'ta': 'Tamil',
            'ml': 'Malayalam',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'bn': 'Bengali',
            'pa': 'Punjabi'
        }
        
        target_language = language_names.get(language, 'English')
        
        # Build prompt
        prompt = f"""You are Raitha Mitra, an expert agricultural advisor for farmers in India. 
You provide practical, actionable advice in simple language that farmers can easily understand and implement.

CONTEXT:
{context_summary}

FARMER'S QUESTION:
{message}

INSTRUCTIONS:
- Start your response with "Namaste Kisan" (not "Namaste Kisan Bhai/Behan")
- Respond in {target_language} language
- Use simple, farmer-friendly language
- Provide specific, actionable advice
- Include practical tips and recommendations
- Reference the conversation context when relevant
- If discussing crops, mention season-appropriate practices
- If discussing diseases, provide treatment options
- Keep responses concise but informative (3-5 paragraphs maximum)
- Format lists with numbers (1., 2., 3.) or dashes (-) instead of asterisks
- Do NOT use markdown asterisks (*) or bold formatting
- Use plain text with clear line breaks
- Be encouraging and supportive

Respond to the farmer's question now:"""
        
        # Generate response
        response = gemini_model.generate_content(prompt)
        
        if response and response.text:
            response_text = response.text.strip()
            
            # Clean up markdown formatting
            # Remove bold markers
            response_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', response_text)
            # Remove italic markers
            response_text = re.sub(r'\*([^*]+)\*', r'\1', response_text)
            # Remove single asterisks at start of lines (bullet points)
            response_text = re.sub(r'^\* ', '- ', response_text, flags=re.MULTILINE)
            # Remove any remaining asterisks
            response_text = response_text.replace('**', '').replace('*', '')
            
            # Save to database
            db.save_chat_message(
                user_id=user_id,
                message=message,
                response=response_text,
                context_data=extracted_context,
                language=language
            )
            
            return {
                'response': response_text,
                'context': extracted_context,
                'success': True
            }
        else:
            return {
                'response': "I couldn't generate a response. Please try rephrasing your question.",
                'context': extracted_context,
                'error': 'Empty response from AI'
            }
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return {
            'response': f"I encountered an error while processing your question. Please try again. Error: {str(e)}",
            'context': {},
            'error': str(e)
        }
