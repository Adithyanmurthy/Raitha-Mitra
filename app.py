import os
import json
import base64
import io
import re
import traceback
from datetime import datetime, timedelta
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import tensorflow as tf
from PIL import Image
import numpy as np
from database import DatabaseManager
from security_utils import (
    sanitize_message, sanitize_description, sanitize_text,
    validate_numeric, validate_integer, validate_date,
    validate_user_id, validate_amount, validate_latitude,
    validate_longitude, validate_enum
)
from rate_limiter import check_rate_limit, record_api_call, get_rate_limit_info

# Weather API imports
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("⚠️  Requests not available. Weather functionality will be disabled.")
    REQUESTS_AVAILABLE = False
    requests = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not available. Using environment variables directly.")
    pass

# --- 1. Initialization and Configuration ---
app = Flask(__name__)
CORS(app)

# Set Flask secret key for sessions
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'raitha-mitra-secret-key-2025-change-in-production')

# Initialize database
db = DatabaseManager()

# --- 2. Routes for serving HTML pages ---

# Health check endpoint for Render
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        health_status = {
            'status': 'healthy',
            'model_loaded': model is not None,
            'model_classes': len(class_names) if class_names else 0,
            'database': 'connected',
            'gemini_configured': gemini_text_model is not None,
            'model_path_exists': os.path.exists(MODEL_PATH),
            'classes_path_exists': os.path.exists(CLASSES_PATH)
        }
        
        # Test model if loaded
        if model is not None:
            try:
                # Create a dummy input to test model
                test_input = np.zeros((1, 128, 128, 3))
                test_pred = model.predict(test_input, verbose=0)
                health_status['model_test'] = 'passed'
            except Exception as model_error:
                health_status['model_test'] = f'failed: {str(model_error)}'
                health_status['status'] = 'degraded'
        
        return jsonify(health_status), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/disease-detection')
def disease_detection():
    return render_template('index.html')

@app.route('/api/test-model')
def test_model():
    """Simple endpoint to test if model is working"""
    try:
        if model is None:
            return jsonify({
                'status': 'error',
                'message': 'Model not loaded',
                'model_path_exists': os.path.exists(MODEL_PATH),
                'classes_path_exists': os.path.exists(CLASSES_PATH)
            }), 500
        
        # Create a simple test image
        test_image = np.random.rand(1, 128, 128, 3).astype(np.float32)
        
        # Try prediction
        prediction = model.predict(test_image, verbose=0)
        
        return jsonify({
            'status': 'success',
            'message': 'Model is working',
            'num_classes': len(class_names),
            'prediction_shape': prediction.shape,
            'sample_classes': class_names[:5]
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

# --- Weather API Routes ---
@app.route('/api/weather')
def get_weather():
    """Get current weather data"""
    city = request.args.get('city', 'Bengaluru')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    # Convert lat/lon to float if provided
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            lat = lon = None
    
    weather_data = get_weather_data(city, lat, lon)
    return jsonify(weather_data)

@app.route('/api/weather/forecast')
def get_forecast():
    """Get weather forecast data"""
    city = request.args.get('city', 'Bengaluru')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    days = int(request.args.get('days', 5))
    
    # Convert lat/lon to float if provided
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            lat = lon = None
    
    forecast_data = get_weather_forecast(city, lat, lon, days)
    return jsonify(forecast_data)

# --- Static file serving ---
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/static/uploads/<filename>')
def uploaded_files(filename):
    return send_from_directory('static/uploads', filename)

# --- 3. GEMINI API Configuration ---
try:
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyBnzoJxxBG4YsrKV-BietpSCRnVI4Hv-Fc')
    
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        raise ValueError("Please set GEMINI_API_KEY in your .env file")
        
    genai.configure(api_key=api_key)
    
    # Model for general text generation (treatments) - Using working model
    gemini_text_model = genai.GenerativeModel('gemini-2.5-flash')
    # Model for market prices - Using same working model (search tools may not be available in newer models)
    gemini_search_model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Gemini AI models configured successfully.")
    
    # Test the models
    try:
        # List available models
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"📋 Available Gemini models: {available_models[:3]}...")  # Show first 3
        
        # Test text model
        test_response = gemini_text_model.generate_content("Test")
        if test_response:
            print("✅ Gemini text model test successful")
        else:
            print("⚠️ Gemini text model test failed")
    except Exception as e:
        print(f"⚠️ Gemini model test failed: {e}")
        print("🔄 Will use fallback treatment data")
except Exception as e:
    print(f"❌ Error configuring Gemini AI: {e}")
    gemini_text_model = None
    gemini_search_model = None

# --- 4. Load the Local TensorFlow Model ---
MODEL_PATH = 'crop_disease_detection_model.h5'
CLASSES_PATH = 'class_names.json'
model = None
class_names = []

if os.path.exists(MODEL_PATH) and os.path.exists(CLASSES_PATH):
    try:
        print(f"📦 Loading model from: {MODEL_PATH}")
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        with open(CLASSES_PATH, 'r') as f:
            class_names = json.load(f)
        print(f"✅ Local disease detection model loaded successfully with {len(class_names)} classes.")
        print(f"🧠 Model input shape: {model.input_shape}")
    except Exception as e:
        print(f"❌ Error loading local model: {e}")
        import traceback
        traceback.print_exc()
        model = None
else:
    print(f"❌ Error: Local model or class names file not found.")
    print(f"   MODEL_PATH exists: {os.path.exists(MODEL_PATH)}")
    print(f"   CLASSES_PATH exists: {os.path.exists(CLASSES_PATH)}")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Files in directory: {os.listdir('.')[:10]}")

# --- 5. Yield Impact Database ---
yield_impact_db = {
    "Apple___Apple_scab": "Medium (20-50% loss)", "Apple___Black_rot": "Low to Medium (10-30% loss)", "Apple___Cedar_apple_rust": "Low (5-15% loss)", "Apple___healthy": "None",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "Medium (15-40% loss)", "Corn_(maize)___Common_rust_": "Low to Medium (10-25% loss)", "Corn_(maize)___Northern_Leaf_Blight": "Medium to High (20-50% loss)", "Corn_(maize)___healthy": "None",
    "Grape___Black_rot": "High (can destroy entire crop)", "Grape___Esca_(Black_Measles)": "High (30-70% loss)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Medium (15-35% loss)", "Grape___healthy": "None",
    "Potato___Early_blight": "Medium (20-30% tuber loss)", "Potato___Late_blight": "Very High (can cause 100% loss)", "Potato___healthy": "None", 
    "Tomato___Bacterial_spot": "Medium (15-40% loss)", "Tomato___Early_blight": "Medium (20-35% loss)", "Tomato___Late_blight": "High (40-70% loss if untreated)", "Tomato___Leaf_Mold": "Low to Medium (10-25% loss)", "Tomato___Septoria_leaf_spot": "Medium (20-40% loss)", "Tomato___Spider_mites Two-spotted_spider_mite": "Low to Medium (10-30% loss)", "Tomato___Target_Spot": "Medium (15-35% loss)", "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "High (50-80% loss)", "Tomato___Tomato_mosaic_virus": "Medium to High (25-60% loss)", "Tomato___healthy": "None",
    "default": "Not Determined"
}

# --- 6. Default Treatment Database ---
default_treatment_db = {
    "Apple - Black rot": {
        "symptoms": "• Black spots appear on leaves\n• Brown spots on fruits\n• Leaves turn yellow and fall\n• Fruits rot",
        "organic_treatment": "• Spray neem oil (10ml/liter water)\n• Baking soda solution (5g/liter)\n• Copper sulfate spray\n• Fennel and garlic solution",
        "chemical_treatment": "• Carbendazim 50% WP (1g/liter)\n• Mancozeb 75% WP (2g/liter)\n• Propiconazole 25% EC (1ml/liter)\n• Copper Oxychloride 50% WP",
        "prevention_tips": "• Remove and destroy infected leaves\n• Maintain proper spacing for air circulation\n• Avoid water on leaves\n• Regular monitoring"
    },
    "Apple - Apple scab": {
        "symptoms": "• Brown spots on leaves\n• Rough spots on fruits\n• Premature leaf fall\n• Reduced fruit quality",
        "organic_treatment": "• Baking soda and soap solution\n• Neem oil spray\n• Chamomile tea solution\n• Sulfur powder spray",
        "chemical_treatment": "• Myclobutanil 10% WP\n• Difenoconazole 25% EC\n• Captan 50% WP\n• Dodine 65% WP",
        "prevention_tips": "• Collect and destroy infected leaves\n• Maintain adequate spacing between trees\n• Preventive spray before rainy season\n• Grow resistant varieties"
    },
    "Tomato - Late blight": {
        "symptoms": "• Brown spots on leaves\n• White fungal growth\n• Spots on stem and fruits\n• Plant dries quickly",
        "organic_treatment": "• Copper sulfate spray\n• Baking soda solution\n• Neem oil and soap\n• Milk and water mixture",
        "chemical_treatment": "• Metalaxyl + Mancozeb\n• Cymoxanil + Mancozeb\n• Dimethomorph 50% WP\n• Fenamidone + Mancozeb",
        "prevention_tips": "• Remove infected plants\n• Proper spacing for air circulation\n• Preventive spray after rain\n• Use resistant varieties"
    },
    "Potato - Late blight": {
        "symptoms": "• Black spots on leaves\n• White fungal growth\n• Brown spots on stem\n• Brown spots on tubers",
        "organic_treatment": "• Copper sulfate spray\n• Bordeaux mixture\n• Neem oil spray\n• Garlic and chili solution",
        "chemical_treatment": "• Metalaxyl M + Mancozeb\n• Cymoxanil + Mancozeb\n• Propamocarb HCl 70% WP\n• Fluazinam 40% SC",
        "prevention_tips": "• Destroy infected plants\n• Treat seed potatoes\n• Proper drainage system\n• Regular monitoring during rainy season"
    },
    "healthy": {
        "symptoms": "• Plant is healthy! 🌱\n• Leaves are green and shiny\n• No disease symptoms visible\n• Normal plant growth",
        "organic_treatment": "• No treatment needed - Plant is healthy! ✅\n• Continue regular watering\n• Apply organic fertilizer\n• Maintain soil moisture",
        "chemical_treatment": "• No chemical treatment needed ✅\n• Only preventive spray if needed\n• Mancozeb once a month (preventive)\n• Copper sulfate during rainy season",
        "prevention_tips": "• Maintain this healthy condition! 🌟\n• Continue regular monitoring\n• Proper watering and fertilization\n• Cleanliness and good air circulation"
    },
    "default": {
        "symptoms": "• Unusual spots on leaves\n• Slow plant growth\n• Yellowing of leaves\n• Reduced fruit quality",
        "organic_treatment": "• Neem oil spray (10ml/liter)\n• Baking soda solution (5g/liter)\n• Garlic and chili solution\n• Chamomile tea spray",
        "chemical_treatment": "• Mancozeb 75% WP (2g/liter)\n• Carbendazim 50% WP (1g/liter)\n• Copper Oxychloride 50% WP\n• Propiconazole 25% EC",
        "prevention_tips": "• Remove infected parts\n• Proper spacing and air circulation\n• Regular monitoring\n• Follow clean farming practices"
    }
}

# --- 6. Database is now handled by DatabaseManager ---
# No need for in-memory storage

# --- 7. Weather API Configuration ---
WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY', '6e4d2aff28174cc1820191846251510')

# Weather API imports
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("⚠️  Requests not available. Weather functionality will be disabled.")
    REQUESTS_AVAILABLE = False
    requests = None

WEATHER_API_AVAILABLE = REQUESTS_AVAILABLE and WEATHERAPI_KEY

if WEATHER_API_AVAILABLE:
    print("✅ Weather API (WeatherAPI.com) configured successfully.")
else:
    print("⚠️  Weather API not configured. Add WEATHERAPI_KEY to .env file.")

# --- 8. Database Configuration ---
# Database is handled by DatabaseManager class



# --- 9. Weather API Functions ---
def get_weather_data(city="Bengaluru", lat=None, lon=None):
    """Get current weather data from WeatherAPI.com"""
    if not WEATHER_API_AVAILABLE:
        return get_default_weather_data(city)
    
    try:
        base_url = "http://api.weatherapi.com/v1/current.json"
        
        # Use coordinates if provided, otherwise use city name
        if lat and lon:
            query = f"{lat},{lon}"
        else:
            query = city
        
        params = {
            'key': WEATHERAPI_KEY,
            'q': query,
            'aqi': 'no'
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            weather_info = {
                'city': data['location']['name'],
                'country': data['location']['country'],
                'temperature': round(data['current']['temp_c']),
                'feels_like': round(data['current']['feelslike_c']),
                'humidity': data['current']['humidity'],
                'pressure': data['current']['pressure_mb'],
                'description': data['current']['condition']['text'],
                'icon': data['current']['condition']['icon'].split('/')[-1].replace('.png', ''),
                'wind_speed': data['current']['wind_kph'] / 3.6,  # Convert to m/s for compatibility
                'wind_direction': data['current']['wind_degree'],
                'visibility': data['current']['vis_km'],
                'sunrise': '06:00',  # WeatherAPI doesn't provide this in current endpoint
                'sunset': '18:00',   # WeatherAPI doesn't provide this in current endpoint
                'status': 'success'
            }
            
            print(f"✅ Weather data retrieved for {weather_info['city']}")
            return weather_info
            
        else:
            print(f"❌ Weather API error: {response.status_code}")
            return get_default_weather_data(city)
            
    except Exception as e:
        print(f"❌ Weather API exception: {e}")
        return get_default_weather_data(city)

def get_weather_forecast(city="Bengaluru", lat=None, lon=None, days=5):
    """Get weather forecast from WeatherAPI.com"""
    if not WEATHER_API_AVAILABLE:
        return get_default_forecast_data(city, days)
    
    try:
        base_url = "http://api.weatherapi.com/v1/forecast.json"
        
        # Use coordinates if provided, otherwise use city name
        if lat and lon:
            query = f"{lat},{lon}"
        else:
            query = city
        
        params = {
            'key': WEATHERAPI_KEY,
            'q': query,
            'days': min(days, 10),  # WeatherAPI supports up to 10 days
            'aqi': 'no',
            'alerts': 'no'
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process forecast data
            forecast_list = []
            
            for day_data in data['forecast']['forecastday']:
                forecast_list.append({
                    'date': day_data['date'],
                    'day': datetime.strptime(day_data['date'], '%Y-%m-%d').strftime('%A'),
                    'temp_min': round(day_data['day']['mintemp_c']),
                    'temp_max': round(day_data['day']['maxtemp_c']),
                    'description': day_data['day']['condition']['text'],
                    'icon': day_data['day']['condition']['icon'].split('/')[-1].replace('.png', ''),
                    'humidity': day_data['day']['avghumidity'],
                    'wind_speed': day_data['day']['maxwind_kph'] / 3.6  # Convert to m/s
                })
            
            print(f"✅ Weather forecast retrieved for {data['location']['name']}")
            return {
                'city': data['location']['name'],
                'forecast': forecast_list[:days],
                'status': 'success'
            }
            
        else:
            print(f"❌ Weather forecast API error: {response.status_code}")
            return get_default_forecast_data(city, days)
            
    except Exception as e:
        print(f"❌ Weather forecast API exception: {e}")
        return get_default_forecast_data(city, days)

def get_default_weather_data(city="Bengaluru"):
    """Default weather data when API is not available"""
    return {
        'city': city,
        'country': 'IN',
        'temperature': 26,
        'feels_like': 28,
        'humidity': 65,
        'pressure': 1013,
        'description': 'Partly Cloudy',
        'icon': '02d',
        'wind_speed': 3.5,
        'wind_direction': 180,
        'visibility': 10,
        'sunrise': '06:30',
        'sunset': '18:45',
        'status': 'demo'
    }

def get_default_forecast_data(city="Bengaluru", days=5):
    """Default forecast data when API is not available"""
    forecast_list = []
    base_date = datetime.now().date()
    
    for i in range(days):
        forecast_date = base_date + timedelta(days=i)
        forecast_list.append({
            'date': forecast_date.strftime('%Y-%m-%d'),
            'day': forecast_date.strftime('%A'),
            'temp_min': 22 + (i % 3),
            'temp_max': 28 + (i % 4),
            'description': ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Clear'][i % 5],
            'icon': ['01d', '02d', '03d', '10d', '01d'][i % 5],
            'humidity': 60 + (i * 5),
            'wind_speed': 2.5 + (i * 0.5)
        })
    
    return {
        'city': city,
        'forecast': forecast_list,
        'status': 'demo'
    }

# --- 10. Gemini Interaction Functions ---
def get_gemini_treatment_details(disease_name, target_language='en'):
    """Get treatment details from Gemini AI with fallback to default data"""
    
    # Language mapping for prompts
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
    
    target_lang_name = language_names.get(target_language, 'English')
    
    # First try Gemini AI with timeout
    if gemini_text_model:
        prompt = f"""You are an expert agricultural advisor for farmers in India. A farmer has identified '{disease_name}'. 

        Provide a detailed action plan in {target_lang_name}. Organize your response into four sections with these exact English headings followed by {target_lang_name} content:

        1. Symptoms: 
        [Write a clear bulleted list of key symptoms in simple {target_lang_name}. Use simple bullet points (•) and avoid asterisks or markdown formatting.]

        2. Organic Treatment: 
        [Write a clear bulleted list of organic remedies in simple {target_lang_name}. Include specific instructions and quantities. Use simple bullet points (•) and avoid asterisks or markdown formatting.]

        3. Chemical Treatment: 
        [Write a clear bulleted list of recommended chemical treatments, including common brand names available in India, in simple {target_lang_name}. Use simple bullet points (•) and avoid asterisks or markdown formatting.]

        4. Prevention Tips: 
        [Write a clear bulleted list of preventive measures in simple {target_lang_name}. Use simple bullet points (•) and avoid asterisks or markdown formatting.]

        IMPORTANT FORMATTING RULES: 
        - Use simple, farmer-friendly language that is easy to understand and implement
        - Do NOT use asterisks (*), markdown formatting, hashtags (#), or complex symbols
        - Use simple bullet points (•) for lists only
        - Write in clear, plain text format without any special formatting
        - Keep sentences short and actionable
        - Use proper spacing between sections
        - Include specific quantities, timings, and brand names where applicable
        - Write as if explaining to a farmer in person"""
        
        try:
            print(f"🤖 Calling Gemini AI for: {disease_name}")
            
            # Add timeout using threading
            import threading
            result = [None]
            error = [None]
            
            def call_gemini():
                try:
                    response = gemini_text_model.generate_content(prompt)
                    result[0] = response
                except Exception as e:
                    error[0] = e
            
            thread = threading.Thread(target=call_gemini)
            thread.daemon = True
            thread.start()
            thread.join(timeout=15)  # 15 second timeout - wait for Gemini response
            
            if thread.is_alive():
                print(f"⏱️ Gemini AI timeout after 15s - using fallback data")
            elif error[0]:
                print(f"❌ Gemini API Error: {error[0]}")
            elif result[0] and result[0].text:
                print(f"✅ Gemini AI response received")
                return parse_gemini_response(result[0].text)
            else:
                print(f"⚠️ Gemini AI returned empty response")
        except Exception as e:
            print(f"❌ Gemini (Text) API Error: {e}")
    
    # Fallback to default treatment data
    print(f"🔄 Using fallback treatment data for: {disease_name}")
    return get_default_treatment_details(disease_name, target_language)

def get_market_prices(crop_name, target_language='en'):
    """Get market prices from Gemini AI with fallback to default data"""
    
    # Language mapping for prompts
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
    
    target_lang_name = language_names.get(target_language, 'English')
    
    # Try Gemini AI first with timeout
    if gemini_search_model:
        prompt = f"""Find today's wholesale market price (APMC mandi rates) for '{crop_name}' in major markets of India, like Bengaluru, Delhi, Mumbai, Chennai. 

        Provide the information in {target_lang_name} using this format:
        • Market Name: Price range per kg/quintal
        • Quality Grade: Price details

        IMPORTANT:
        - Use simple bullet points (•) only
        - Do NOT use asterisks (*), markdown formatting, or complex symbols  
        - Write in clear, plain text format
        - Use farmer-friendly language
        - Include currency symbols (₹) for prices
        - Keep it simple and easy to read"""
        try:
            print(f"💰 Getting market prices from Gemini AI for: {crop_name}")
            
            # Add timeout using threading
            import threading
            result = [None]
            error = [None]
            
            def call_gemini():
                try:
                    response = gemini_search_model.generate_content(prompt)
                    result[0] = response
                except Exception as e:
                    error[0] = e
            
            thread = threading.Thread(target=call_gemini)
            thread.daemon = True
            thread.start()
            thread.join(timeout=15)  # 15 second timeout - wait for Gemini response
            
            if thread.is_alive():
                print(f"⏱️ Gemini AI timeout after 15s for market prices - using fallback data")
            elif error[0]:
                print(f"❌ Gemini API Error: {error[0]}")
            elif result[0] and result[0].text:
                print(f"✅ Market prices received from Gemini AI")
                cleaned_prices = clean_gemini_text(result[0].text)
                return cleaned_prices
            else:
                print(f"⚠️ Gemini AI returned empty response for market prices")
        except Exception as e:
            print(f"❌ Gemini (Search) API Error: {e}")
    
    # Fallback to default market data
    print(f"🔄 Using fallback market data for: {crop_name}")
    return get_default_market_prices(crop_name, target_language)

def get_default_market_prices(crop_name, target_language='en'):
    """Default market prices when Gemini AI is not available - Always in English"""
    default_prices = {
        "Apple": "• Bengaluru: ₹80-120/kg\n• Mysuru: ₹75-110/kg\n• Hubballi: ₹70-105/kg\n• Quality: A Grade - Higher rate, B Grade - Medium rate",
        "Tomato": "• Bengaluru: ₹25-45/kg\n• Mysuru: ₹20-40/kg\n• Hubballi: ₹18-38/kg\n• Quality: Large size - Higher rate",
        "Potato": "• Bengaluru: ₹15-25/kg\n• Mysuru: ₹12-22/kg\n• Hubballi: ₹10-20/kg\n• Quality: Large size - Better rate",
        "Corn": "• Bengaluru: ₹18-28/kg\n• Mysuru: ₹16-26/kg\n• Hubballi: ₹15-25/kg\n• Quality: Dry corn - Better rate",
        "Grape": "• Bengaluru: ₹60-100/kg\n• Mysuru: ₹55-95/kg\n• Hubballi: ₹50-90/kg\n• Quality: Export quality - Higher rate",
        "Cherry": "• Bengaluru: ₹200-350/kg\n• Mysuru: ₹180-320/kg\n• Hubballi: ₹170-300/kg\n• Quality: Fresh and large size - Premium rate"
    }
    
    # Find matching crop
    base_price = None
    for crop in default_prices.keys():
        if crop.lower() in crop_name.lower():
            base_price = default_prices[crop]
            break
    
    if not base_price:
        # Default message in English
        base_price = f"• Market rates for {crop_name}:\n• Check local market\n• Visit APMC mandi\n• Rates vary based on quality"
    
    return base_price

def clean_gemini_text(text):
    """Clean up Gemini AI response text by removing markdown formatting"""
    if not text:
        return text
    
    # Remove excessive asterisks and markdown formatting
    text = re.sub(r'\*{2,}', '', text)  # Remove multiple asterisks
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove single asterisks around text
    text = re.sub(r'#{1,6}\s*', '', text)  # Remove markdown headers
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code formatting
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Remove markdown links
    
    # Clean up bullet points and formatting
    text = re.sub(r'^\s*[-•*]\s*', '• ', text, flags=re.MULTILINE)  # Standardize bullet points
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove excessive line breaks
    text = re.sub(r'^\s+|\s+$', '', text)  # Remove leading/trailing whitespace
    
    # Fix common formatting issues
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n\s*', '\n', text)  # Clean up line breaks
    
    return text.strip()

def parse_gemini_response(text):
    """Parse Gemini AI response into structured format"""
    details = {key: "Information not available." for key in ["symptoms", "organic_treatment", "chemical_treatment", "prevention_tips"]}
    
    # Clean the input text first
    text = clean_gemini_text(text)
    
    patterns = {
        "symptoms": r"Symptoms:(.*?)(Organic Treatment:|Chemical Treatment:|Prevention Tips:|$)",
        "organic_treatment": r"Organic Treatment:(.*?)(Chemical Treatment:|Prevention Tips:|$)",
        "chemical_treatment": r"Chemical Treatment:(.*?)(Prevention Tips:|$)",
        "prevention_tips": r"Prevention Tips:(.*)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match: 
            extracted_text = match.group(1).strip()
            # Clean the extracted text
            cleaned_text = clean_gemini_text(extracted_text)
            details[key] = cleaned_text if cleaned_text else "Information not available."
    
    return details

def get_default_treatment_details(disease_name, target_language='en'):
    """Get default treatment details when Gemini AI is not available"""
    
    # Check if plant is healthy
    if "healthy" in disease_name.lower():
        base_details = default_treatment_db["healthy"]
    else:
        # Try to find exact match first
        if disease_name in default_treatment_db:
            base_details = default_treatment_db[disease_name]
        else:
            # Try to find partial match
            found = False
            for key in default_treatment_db.keys():
                if key != "healthy" and key != "default":  # Skip special keys
                    if key.lower() in disease_name.lower() or disease_name.lower() in key.lower():
                        base_details = default_treatment_db[key]
                        found = True
                        break
            
            if not found:
                # Return default treatment
                base_details = default_treatment_db["default"]
    
    # Translate the details if not English
    if target_language != 'en':
        translated_details = {}
        for key, value in base_details.items():
            if isinstance(value, str):
                translated_details[key] = get_fallback_translation(value, target_language)
            else:
                translated_details[key] = value
        return translated_details
    
    return base_details

# --- 8. Image Preprocessing ---
def preprocess_image(image_data, target_size=(128, 128)):
    """Preprocess image for model prediction with memory optimization"""
    try:
        # Handle data URL format
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 with error handling
        image_bytes = base64.b64decode(image_data)
        
        # Open and process image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to target size
        img = img.resize(target_size, Image.LANCZOS)
        
        # Convert to numpy array and normalize
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        # Clean up
        img.close()
        
        # Add batch dimension
        return np.expand_dims(img_array, axis=0)
    except Exception as e:
        print(f"❌ Image preprocessing error: {e}")
        raise ValueError(f"Failed to preprocess image: {str(e)}")

# --- 9. Authentication Endpoints ---
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        required_fields = ['name', 'email', 'mobile', 'password', 'location']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate mobile format
        if not re.match(r'^[6-9]\d{9}$', data['mobile']):
            return jsonify({'error': 'Invalid mobile number format'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_email_or_mobile(data['email'])
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
            
        existing_user = db.get_user_by_email_or_mobile(data['mobile'])
        if existing_user:
            return jsonify({'error': 'User with this mobile number already exists'}), 409
        
        # Geocode location to get coordinates
        latitude, longitude = geocode_location(data['location'])
        
        # Create user in database (no OTP verification needed)
        user_id = db.create_user(
            name=data['name'],
            email=data['email'],
            mobile=data['mobile'],
            password=data['password'],
            location=data['location']
        )
        
        # Update coordinates if found
        if latitude and longitude:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users
                SET latitude = ?, longitude = ?, location_privacy = ?
                WHERE id = ?
            ''', (latitude, longitude, get_default_privacy_level(), user_id))
            conn.commit()
            conn.close()
            print(f"✅ Coordinates added for {data['name']}: ({latitude}, {longitude})")
        
        print(f"✅ User registered: {data['name']} ({data['email']}, {data['mobile']}) - ID: {user_id}")
        
        # Generate a simple token for auto-login
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Set Flask session for auto-login
        session['user_id'] = user_id
        session['user_name'] = data['name']
        session['user_email'] = data['email']
        
        print(f"✅ Session set for user_id: {user_id}")
        
        return jsonify({
            'message': 'Registration successful! You are now logged in.', 
            'user_id': user_id,
            'user': {
                'id': user_id,
                'name': data['name'],
                'email': data['email'],
                'mobile': data['mobile'],
                'location': data['location'],
                'created_at': datetime.now().isoformat()
            },
            'token': token
        }), 201
        
    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email_or_mobile = data.get('emailOrMobile')
        password = data.get('password')
        
        print(f"🔐 Login attempt: {email_or_mobile}")
        
        if not email_or_mobile or not password:
            return jsonify({'error': 'Email/mobile and password are required'}), 400
        
        # Get user from database
        user_data = db.get_user_by_email_or_mobile(email_or_mobile)
        
        if not user_data:
            print(f"❌ User not found: {email_or_mobile}")
            return jsonify({'error': 'User not found. Please register first.'}), 401
        
        print(f"👤 Found user: {user_data.get('name', 'Unknown')}")
        
        # Verify password
        password_valid = db.verify_password(user_data, password)
        print(f"🔒 Password verification: {password_valid}")
        print(f"🔍 Password hash starts with: {user_data['password_hash'][:20]}...")
        print(f"🔍 Provided password length: {len(password)}")
        
        if password_valid:
            # Generate a simple token (in production, use JWT or similar)
            import secrets
            token = secrets.token_urlsafe(32)
            
            # Set Flask session
            session['user_id'] = user_data['id']
            session['user_name'] = user_data['name']
            session['user_email'] = user_data['email']
            
            # Return user data without password
            response_user = {
                'id': user_data['id'],
                'name': user_data['name'],
                'email': user_data['email'],
                'mobile': user_data['mobile'],
                'location': user_data['location'],
                'created_at': user_data['created_at']
            }
            print(f"✅ Login successful for: {response_user.get('name')}")
            print(f"✅ Session set for user_id: {user_data['id']}")
            return jsonify({
                'message': 'Login successful', 
                'user': response_user,
                'token': token
            }), 200
        else:
            print(f"❌ Invalid password for: {email_or_mobile}")
            return jsonify({'error': 'Invalid password'}), 401
            
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    try:
        user_id = session.get('user_id')
        if user_id:
            print(f"👋 User {user_id} logging out")
            session.clear()
            return jsonify({'message': 'Logged out successfully'}), 200
        else:
            return jsonify({'message': 'No active session'}), 200
    except Exception as e:
        print(f"❌ Logout Error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if user is logged in (for debugging)"""
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_email = session.get('user_email')
    
    if user_id:
        print(f"✅ Session active for user_id: {user_id}")
        return jsonify({
            'logged_in': True,
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email
        }), 200
    else:
        print(f"❌ No active session")
        return jsonify({
            'logged_in': False,
            'message': 'No active session. Please login.'
        }), 200

# OTP endpoints disabled - registration now works without OTP verification
# @app.route('/api/send-otp', methods=['POST'])
# def send_otp():
#     try:
#         data = request.get_json()
#         mobile = data.get('mobile')
#         
#         if not mobile:
#             return jsonify({'error': 'Mobile number is required'}), 400
#         
#         # Validate mobile number format
#         if not re.match(r'^[6-9]\d{9}$', mobile):
#             return jsonify({'error': 'Invalid mobile number format'}), 400
#         
#         # Generate OTP
#         otp = generate_otp()
#         
#         # Store OTP
#         store_otp(mobile, otp)
#         
#         # Send SMS
#         success, message = send_sms_otp(mobile, otp)
#         
#         if success:
#             return jsonify({
#                 'message': message,
#                 'demo_otp': otp if not firebase_app and not twilio_client else None  # Only show OTP in demo mode
#             }), 200
#         else:
#             return jsonify({'error': message}), 500
#         
#     except Exception as e:
#         print(f"❌ OTP Error: {e}")
#         return jsonify({'error': 'Failed to send OTP'}), 500

@app.route('/api/user/<int:user_id>/predictions', methods=['GET'])
def get_user_predictions(user_id):
    """Get user's prediction history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        predictions = db.get_user_predictions(user_id, limit)
        
        return jsonify({
            'predictions': predictions,
            'total': len(predictions)
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting user predictions: {e}")
        return jsonify({'error': 'Failed to get predictions'}), 500

@app.route('/api/predictions/all', methods=['GET'])
def get_all_predictions():
    """Get all predictions for analytics (admin only)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        predictions = db.get_all_predictions(limit)
        
        return jsonify({
            'predictions': predictions,
            'total': len(predictions)
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting all predictions: {e}")
        return jsonify({'error': 'Failed to get predictions'}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset user password (for demo/testing purposes)"""
    try:
        data = request.get_json()
        email_or_mobile = data.get('emailOrMobile')
        new_password = data.get('newPassword', '123456')  # Default to demo password
        
        if not email_or_mobile:
            return jsonify({'error': 'Email or mobile is required'}), 400
        
        # Get user from database
        user_data = db.get_user_by_email_or_mobile(email_or_mobile)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Update password in database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Hash the new password
        from werkzeug.security import generate_password_hash
        new_password_hash = generate_password_hash(new_password)
        
        cursor.execute('''
            UPDATE users 
            SET password_hash = ? 
            WHERE email = ? OR mobile = ?
        ''', (new_password_hash, email_or_mobile, email_or_mobile))
        
        conn.commit()
        conn.close()
        
        print(f"🔄 Password reset for user: {user_data['name']} ({email_or_mobile})")
        
        return jsonify({
            'message': 'Password reset successful',
            'new_password': new_password,
            'user': user_data['name']
        }), 200
        
    except Exception as e:
        print(f"❌ Password reset error: {e}")
        return jsonify({'error': 'Password reset failed'}), 500

# OTP verification endpoint disabled - no longer needed
# @app.route('/api/verify-otp', methods=['POST'])
# def verify_otp_endpoint():
#     try:
#         data = request.get_json()
#         mobile = data.get('mobile')
#         provided_otp = data.get('otp')
#         
#         if not mobile or not provided_otp:
#             return jsonify({'error': 'Mobile number and OTP are required'}), 400
#         
#         # Verify OTP
#         is_valid, message = verify_otp(mobile, provided_otp)
#         
#         if is_valid:
#             return jsonify({'message': message, 'verified': True}), 200
#         else:
#             return jsonify({'error': message, 'verified': False}), 400
#         
#     except Exception as e:
#         print(f"❌ OTP Verification Error: {e}")
#         return jsonify({'error': 'Failed to verify OTP'}), 500

@app.route('/api/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        data = request.get_json()
        current_password = data.get('current_password')  # Updated field name to match JavaScript
        new_password = data.get('new_password')  # Updated field name to match JavaScript
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # For demo purposes, use the demo user
        # In production, you'd decode the token to get the user info
        user = db.get_user_by_email_or_mobile('demo@raithamitra.com')
        if not user:
            print(f"❌ Demo user not found")
            return jsonify({'error': 'User not found'}), 404
        
        email = user['email']
        print(f"🔍 Found user: {email}, verifying password...")
        
        # Verify current password
        if not db.verify_password(user, current_password):
            print(f"❌ Current password verification failed for user: {email}")
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        print(f"✅ Current password verified for user: {email}")
        
        # Hash new password
        new_password_hash = generate_password_hash(new_password)
        
        # Update password in database
        success = db.update_user_password(email, new_password_hash)
        
        if success:
            print(f"✅ Password changed successfully for user: {email}")
            return jsonify({'message': 'Password changed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update password'}), 500
        
    except Exception as e:
        print(f"❌ Change password error: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

# Old prediction history endpoint removed - replaced with new one below

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Translate text to specified language"""
    try:
        data = request.get_json()
        text = data.get('text')
        target_language = data.get('target_language', 'en')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Use Google Translate API if available, otherwise use local translations
        translated_text = translate_with_gemini(text, target_language)
        
        return jsonify({
            'original_text': text,
            'translated_text': translated_text,
            'target_language': target_language
        }), 200
        
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return jsonify({'error': 'Translation failed'}), 500

def translate_with_gemini(text, target_language):
    """Translate text using Gemini AI"""
    try:
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
        
        target_lang_name = language_names.get(target_language, 'English')
        
        if target_language == 'en':
            return text  # No translation needed
        
        # Use Gemini for translation with timeout
        if genai and gemini_text_model:
            prompt = f"""
            Translate the following text to {target_lang_name}. 
            Provide only the translation, no explanations or additional text.
            Keep technical terms related to agriculture and plant diseases accurate.
            
            Text to translate: {text}
            """
            
            # Add timeout using threading
            import threading
            result = [None]
            error = [None]
            
            def call_gemini():
                try:
                    response = gemini_text_model.generate_content(prompt)
                    result[0] = response
                except Exception as e:
                    error[0] = e
            
            thread = threading.Thread(target=call_gemini)
            thread.daemon = True
            thread.start()
            thread.join(timeout=1)  # 1 second timeout for faster translation
            
            if thread.is_alive():
                print(f"⏱️ Translation timeout - using fallback")
                return get_fallback_translation(text, target_language)
            elif error[0]:
                print(f"❌ Translation error: {error[0]}")
                return get_fallback_translation(text, target_language)
            elif result[0] and result[0].text:
                translated = result[0].text.strip()
                print(f"🌐 Translated '{text[:50]}...' to {target_lang_name}")
                return translated
            else:
                return get_fallback_translation(text, target_language)
        else:
            # Fallback to basic translations for common terms
            return get_fallback_translation(text, target_language)
            
    except Exception as e:
        print(f"❌ Gemini translation error: {e}")
        return get_fallback_translation(text, target_language)

def get_fallback_translation(text, target_language):
    """Fallback translations for common agricultural terms"""
    translations = {
        'hi': {  # Hindi
            'Healthy': 'स्वस्थ',
            'Disease': 'रोग',
            'Treatment': 'उपचार',
            'Symptoms': 'लक्षण',
            'Prevention': 'रोकथाम',
            'Organic': 'जैविक',
            'Chemical': 'रासायनिक',
            'Leaf': 'पत्ता',
            'Plant': 'पौधा',
            'Crop': 'फसल',
            'Apply': 'लगाएं',
            'Spray': 'छिड़काव',
            'Remove': 'हटाएं',
            'Water': 'पानी',
            'Soil': 'मिट्टी',
            'Fertilizer': 'उर्वरक',
            'Neem': 'नीम',
            'Oil': 'तेल',
            'Weekly': 'साप्ताहिक',
            'Daily': 'दैनिक'
        },
        'kn': {  # Kannada
            'Healthy': 'ಆರೋಗ್ಯಕರ',
            'Disease': 'ರೋಗ',
            'Treatment': 'ಚಿಕಿತ್ಸೆ',
            'Symptoms': 'ಲಕ್ಷಣಗಳು',
            'Prevention': 'ತಡೆಗಟ್ಟುವಿಕೆ',
            'Organic': 'ಸಾವಯವ',
            'Chemical': 'ರಾಸಾಯನಿಕ',
            'Leaf': 'ಎಲೆ',
            'Plant': 'ಸಸ್ಯ',
            'Crop': 'ಬೆಳೆ',
            'Apply': 'ಅನ್ವಯಿಸಿ',
            'Spray': 'ಸಿಂಪಡಿಸಿ',
            'Remove': 'ತೆಗೆದುಹಾಕಿ',
            'Water': 'ನೀರು',
            'Soil': 'ಮಣ್ಣು',
            'Fertilizer': 'ಗೊಬ್ಬರ',
            'Neem': 'ಬೇವು',
            'Oil': 'ಎಣ್ಣೆ',
            'Weekly': 'ವಾರಕ್ಕೊಮ್ಮೆ',
            'Daily': 'ದೈನಂದಿನ'
        },
        'te': {  # Telugu
            'Healthy': 'ఆరోగ్యకరమైన',
            'Disease': 'వ్యాధి',
            'Treatment': 'చికిత్స',
            'Symptoms': 'లక్షణాలు',
            'Prevention': 'నివారణ',
            'Organic': 'సేంద్రీయ',
            'Chemical': 'రసాయనిక',
            'Leaf': 'ఆకు',
            'Plant': 'మొక్క',
            'Crop': 'పంట',
            'Apply': 'వర్తింపజేయండి',
            'Spray': 'స్ప్రే చేయండి',
            'Remove': 'తొలగించండి',
            'Water': 'నీరు',
            'Soil': 'మట్టి',
            'Fertilizer': 'ఎరువులు',
            'Neem': 'వేప',
            'Oil': 'నూనె',
            'Weekly': 'వారానికి',
            'Daily': 'రోజువారీ'
        },
        'ta': {  # Tamil
            'Healthy': 'ஆரோக்கியமான',
            'Disease': 'நோய்',
            'Treatment': 'சிகிச்சை',
            'Symptoms': 'அறிகுறிகள்',
            'Prevention': 'தடுப்பு',
            'Organic': 'இயற்கை',
            'Chemical': 'இரசாயன',
            'Leaf': 'இலை',
            'Plant': 'செடி',
            'Crop': 'பயிர்',
            'Apply': 'பயன்படுத்தவும்',
            'Spray': 'தெளிக்கவும்',
            'Remove': 'அகற்றவும்',
            'Water': 'நீர்',
            'Soil': 'மண்',
            'Fertilizer': 'உரம்',
            'Neem': 'வேம்பு',
            'Oil': 'எண்ணெய்',
            'Weekly': 'வாராந்திர',
            'Daily': 'தினசரி'
        }
    }
    
    lang_dict = translations.get(target_language, {})
    
    # If no translation dictionary or text is empty, return original
    if not lang_dict or not text:
        return text
    
    # Simple word replacement for fallback
    translated = text
    for english_word, local_word in lang_dict.items():
        # Case-insensitive replacement
        translated = translated.replace(english_word, local_word)
        translated = translated.replace(english_word.lower(), local_word)
    
    # Always return something (original text if no translation happened)
    return translated if translated else text

# --- 10. Prediction API Endpoint ---
@app.route('/predict', methods=['POST'])
def predict():
    if model is None: 
        return jsonify({'error': 'Local model not loaded.'}), 500
    
    try:
        data = request.get_json()
        if 'image' not in data: 
            return jsonify({'error': 'No image data found.'}), 400
        
        # Get user ID and language from request
        user_id = data.get('user_id')  # This should come from session/token
        target_language = data.get('language', 'en')  # Default to English
        
        print(f"🔬 Starting prediction for user: {user_id}")
        print(f"📝 Target language: {target_language}")
        
        # Process image with error handling
        try:
            processed_image = preprocess_image(data['image'])
            print(f"📸 Image processed, shape: {processed_image.shape}")
        except Exception as img_error:
            print(f"❌ Image processing error: {img_error}")
            return jsonify({'error': 'Failed to process image. Please try again with a different image.'}), 400
        
        # Make prediction with error handling
        try:
            prediction = model.predict(processed_image, verbose=0)
            predicted_class_index = np.argmax(prediction[0])
            confidence = float(prediction[0][predicted_class_index])
            predicted_class_name = class_names[predicted_class_index]
            formatted_disease_name = predicted_class_name.replace("___", " - ").replace("_", " ")
            
            print(f"🎯 Prediction: {formatted_disease_name} (confidence: {confidence:.2f})")
        except Exception as pred_error:
            print(f"❌ Model prediction error: {pred_error}")
            return jsonify({'error': 'Failed to analyze image. Please try again.'}), 500

        yield_impact = yield_impact_db.get(predicted_class_name, yield_impact_db['default'])
        
        # Extract crop name for market search
        crop_name = predicted_class_name.split('___')[0].replace("_", " ")
        
        # Get treatment details and market prices in the selected language
        print(f"🤖 Getting treatment details from Gemini AI in {target_language}...")
        try:
            treatment_details = get_gemini_treatment_details(formatted_disease_name, target_language)
            if treatment_details is None:
                print(f"⚠️ Gemini returned None, using fallback")
                treatment_details = get_default_treatment_details(formatted_disease_name, target_language)
        except Exception as treatment_error:
            print(f"❌ Treatment details error: {treatment_error}")
            treatment_details = get_default_treatment_details(formatted_disease_name, target_language)
        
        print(f"💰 Getting market prices for {crop_name} in {target_language}...")
        try:
            if "healthy" not in predicted_class_name:
                market_prices = get_market_prices(crop_name, target_language)
            else:
                # Healthy plant message in different languages
                healthy_messages = {
                    'en': "Plant is healthy, no market rates needed.",
                    'hi': "पौधा स्वस्थ है, बाजार दर की आवश्यकता नहीं।",
                    'kn': "ಸಸ್ಯ ಆರೋಗ್ಯಕರವಾಗಿರುವುದರಿಂದ ಮಾರುಕಟ್ಟೆ ದರ ಅಗತ್ಯವಿಲ್ಲ।",
                    'te': "మొక్క ఆరోగ్యంగా ఉంది, మార్కెట్ రేట్లు అవసరం లేదు।",
                    'ta': "செடி ஆரோக்கியமாக உள்ளது, சந்தை விலைகள் தேவையில்லை।",
                    'ml': "ചെടി ആരോഗ്യകരമാണ്, മാർക്കറ്റ് നിരക്കുകൾ ആവശ്യമില്ല।",
                    'mr': "रोप निरोगी आहे, बाजार दर आवश्यक नाही।",
                    'gu': "છોડ સ્વસ્થ છે, બજાર દરોની જરૂર નથી।",
                    'bn': "গাছ সুস্থ, বাজার দরের প্রয়োজন নেই।",
                    'pa': "ਪੌਧਾ ਸਿਹਤਮੰਦ ਹੈ, ਮਾਰਕੀਟ ਰੇਟ ਦੀ ਲੋੜ ਨਹੀਂ।"
                }
                market_prices = healthy_messages.get(target_language, healthy_messages['en'])
        except Exception as market_error:
            print(f"❌ Market prices error: {market_error}")
            market_prices = get_default_market_prices(crop_name, target_language)

        # Save the uploaded image
        image_path = None
        if user_id:
            try:
                # Create uploads directory if it doesn't exist
                import os
                uploads_dir = 'static/uploads'
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                
                # Save the image with a unique filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"prediction_{user_id}_{timestamp}.jpg"
                image_path = f"{uploads_dir}/{image_filename}"
                
                # Decode and save the base64 image
                import base64
                import io
                from PIL import Image
                
                # Remove data URL prefix if present
                if data['image'].startswith('data:image'):
                    image_data = data['image'].split(',')[1]
                else:
                    image_data = data['image']
                
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                # Convert to RGB if necessary and save
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(image_path, 'JPEG', quality=85)
                
                # Use relative path for database storage
                image_path = f"/static/uploads/{image_filename}"
                print(f"📸 Image saved to: {image_path}")
                
            except Exception as e:
                print(f"❌ Error saving image: {e}")
                image_path = None

        # Save prediction to database if user_id is provided
        if user_id:
            try:
                prediction_id = db.save_prediction(
                    user_id=user_id,
                    disease_name=formatted_disease_name,
                    confidence=confidence,
                    yield_impact=yield_impact,
                    symptoms=treatment_details.get('symptoms', ''),
                    organic_treatment=treatment_details.get('organic_treatment', ''),
                    chemical_treatment=treatment_details.get('chemical_treatment', ''),
                    prevention_tips=treatment_details.get('prevention_tips', ''),
                    market_prices=market_prices,
                    image_path=image_path
                )
                print(f"💾 Prediction saved to database with ID: {prediction_id}")
            except Exception as e:
                print(f"⚠️ Failed to save prediction to database: {e}")

        # Translate disease name and yield impact if not English
        if target_language != 'en':
            print(f"🌐 Translating disease name and yield impact to {target_language}...")
            try:
                translated_disease_name = translate_with_gemini(formatted_disease_name, target_language)
                translated_yield_impact = translate_with_gemini(yield_impact, target_language)
            except Exception as e:
                print(f"⚠️ Translation failed for disease name/yield impact: {e}")
                translated_disease_name = formatted_disease_name
                translated_yield_impact = yield_impact
        else:
            translated_disease_name = formatted_disease_name
            translated_yield_impact = yield_impact
        
        response = {
            'disease': translated_disease_name,
            'original_disease': formatted_disease_name,
            'confidence': confidence,
            'yield_impact': translated_yield_impact,
            'original_yield_impact': yield_impact,  # Store original for language switching
            'details': treatment_details,  # Already in target language from Gemini
            'market_prices': market_prices,  # Already in target language from Gemini
            'language': target_language
        }
        
        print(f"✅ Prediction completed successfully")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Prediction Endpoint Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

# --- 10b. Fast Language Translation Endpoint ---
@app.route('/translate-results', methods=['POST'])
def translate_results():
    """Fast translation endpoint for switching languages on existing results"""
    try:
        data = request.get_json()
        
        disease_name = data.get('disease_name')
        yield_impact = data.get('yield_impact')
        details = data.get('details', {})
        market_prices = data.get('market_prices')
        target_language = data.get('target_language', 'en')
        
        print(f"🌐 Translating results to {target_language}...")
        
        # If English, return as-is
        if target_language == 'en':
            return jsonify({
                'disease': disease_name,
                'yield_impact': yield_impact,
                'details': details,
                'market_prices': market_prices,
                'language': 'en'
            })
        
        # Get translated content from Gemini with timeout (or return original if fails)
        translated_disease = translate_with_gemini(disease_name, target_language) or disease_name
        translated_yield_impact = translate_with_gemini(yield_impact, target_language) or yield_impact
        
        # Translate treatment details (keep original if translation fails)
        translated_details = {
            'symptoms': translate_with_gemini(details.get('symptoms', ''), target_language) or details.get('symptoms', ''),
            'organic_treatment': translate_with_gemini(details.get('organic_treatment', ''), target_language) or details.get('organic_treatment', ''),
            'chemical_treatment': translate_with_gemini(details.get('chemical_treatment', ''), target_language) or details.get('chemical_treatment', ''),
            'prevention_tips': translate_with_gemini(details.get('prevention_tips', ''), target_language) or details.get('prevention_tips', '')
        }
        
        # Translate market prices if not a healthy message
        if isinstance(market_prices, str) and "healthy" in market_prices.lower():
            # It's a healthy plant message
            healthy_messages = {
                'en': "Plant is healthy, no market rates needed.",
                'hi': "पौधा स्वस्थ है, बाजार दर की आवश्यकता नहीं।",
                'kn': "ಸಸ್ಯ ಆರೋಗ್ಯಕರವಾಗಿರುವುದರಿಂದ ಮಾರುಕಟ್ಟೆ ದರ ಅಗತ್ಯವಿಲ್ಲ।",
                'te': "మొక్క ఆరోగ్యంగా ఉంది, మార్కెట్ రేట్లు అవసరం లేదు।",
                'ta': "செடி ஆரோக்கியமாக உள்ளது, சந்தை விலைகள் தேவையில்லை।",
                'ml': "ചെടി ആരോഗ്യകരമാണ്, മാർക്കറ്റ് നിരക്കുകൾ ആവശ്യമില്ല।",
                'mr': "रोप निरोगी आहे, बाजार दर आवश्यक नाही।",
                'gu': "છોડ સ્વસ્થ છે, બજાર દરોની જરૂર નથી।",
                'bn': "গাছ সুস্থ, বাজার দরের প্রয়োজন নেই।",
                'pa': "ਪੌਧਾ ਸਿਹਤਮੰਦ ਹੈ, ਮਾਰਕੀਟ ਰੇਟ ਦੀ ਲੋੜ ਨਹੀਂ।"
            }
            translated_market_prices = healthy_messages.get(target_language, healthy_messages['en'])
        else:
            translated_market_prices = translate_with_gemini(market_prices, target_language) or market_prices
        
        response = {
            'disease': translated_disease,
            'yield_impact': translated_yield_impact,
            'details': translated_details,
            'market_prices': translated_market_prices,
            'language': target_language,
            'note': 'Showing English content due to translation service limits. Please try again in a minute.' if translated_disease == disease_name else None
        }
        
        print(f"✅ Translation completed for {target_language}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Translation Endpoint Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

# --- 10c. Prediction History Endpoint ---
@app.route('/api/predictions/history', methods=['GET'])
def get_user_prediction_history():
    """Get user's prediction history"""
    try:
        # Get user_id from query params or session
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 20))
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        print(f"📋 Fetching prediction history for user: {user_id}")
        
        # Get predictions from database
        predictions = db.get_user_predictions(user_id, limit)
        
        print(f"✅ Found {len(predictions)} predictions")
        return jsonify({
            'predictions': predictions,
            'count': len(predictions)
        })
        
    except Exception as e:
        print(f"❌ Prediction History Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch history: {str(e)}'}), 500

@app.route('/api/predictions/<int:prediction_id>', methods=['GET'])
def get_prediction_detail(prediction_id):
    """Get detailed information about a specific prediction"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM predictions WHERE id = ?', (prediction_id,))
        prediction = cursor.fetchone()
        conn.close()
        
        if not prediction:
            return jsonify({'error': 'Prediction not found'}), 404
        
        return jsonify(dict(prediction))
        
    except Exception as e:
        print(f"❌ Prediction Detail Error: {e}")
        return jsonify({'error': f'Failed to fetch prediction: {str(e)}'}), 500

# --- 11. New Feature API Routes ---

# Import service modules
from chat_service import generate_contextual_response, get_conversation_summary
from farm_service import generate_weekly_schedule, get_task_recommendations, adjust_for_weather, calculate_growth_stage
from yield_service import predict_yield, compare_with_regional_average, generate_preparation_checklist
from finance_service import calculate_health_score, analyze_cost_efficiency, project_profit
from map_service import aggregate_farmer_locations, get_regional_stats, find_nearby_farmers, get_trending_topics
from geocoding_utils import geocode_location, get_default_privacy_level

# --- Chat API Routes ---
@app.route('/chat')
def chat_page():
    """Render chat interface"""
    return render_template('chat.html')

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """Send message and get AI response"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to use chat'}), 401
        
        data = request.get_json()
        
        # Validate input
        if not data or 'message' not in data:
            return jsonify({'error': 'message is required'}), 400
        
        # Check rate limit
        allowed, remaining, reset_time = check_rate_limit(user_id, 'chat')
        if not allowed:
            limit_info = get_rate_limit_info('chat')
            return jsonify({
                'error': f'Rate limit exceeded. You can send {limit_info["calls"]} messages per {limit_info["window_minutes"]} minutes.',
                'rate_limit_exceeded': True,
                'remaining': remaining,
                'reset_time': reset_time
            }), 429
        
        # Sanitize message
        message = sanitize_message(data['message'])
        language = sanitize_text(data.get('language', 'en'), max_length=10)
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Record API call
        record_api_call(user_id, 'chat')
        
        # Generate response
        result = generate_contextual_response(user_id, message, language)
        
        if result.get('success'):
            return jsonify({
                'response': result['response'],
                'context': result.get('context', {}),
                'success': True
            })
        else:
            return jsonify({
                'response': result.get('response', 'Error generating response'),
                'error': result.get('error'),
                'success': False
            }), 500
    
    except Exception as e:
        print(f"Error in send_chat_message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Retrieve chat history for a user"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view chat history'}), 401
        
        limit = request.args.get('limit', 20, type=int)
        
        # Get chat history from database
        messages = db.get_chat_history(user_id, limit)
        
        return jsonify({
            'messages': messages,
            'count': len(messages),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_chat_history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat_history():
    """Clear all chat history for a user"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to clear chat history'}), 401
        
        # Clear chat history from database
        success = db.clear_chat_history(user_id)
        
        if success:
            return jsonify({
                'message': 'Chat history cleared successfully',
                'success': True
            })
        else:
            return jsonify({
                'error': 'Failed to clear chat history',
                'success': False
            }), 500
    
    except Exception as e:
        print(f"Error in clear_chat_history: {e}")
        return jsonify({'error': str(e)}), 500

# --- Farm Planner API Routes ---
@app.route('/farm-planner')
def farm_planner_page():
    """Render farm planner interface"""
    return render_template('farm_planner.html')

@app.route('/api/farm/schedule', methods=['GET'])
def get_farm_schedule():
    """Get weekly farm schedule"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view schedule'}), 401
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get schedule from database
        schedule = db.get_farm_schedule(user_id, start_date, end_date)
        
        return jsonify({
            'schedule': schedule,
            'count': len(schedule),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_farm_schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/farm/activity', methods=['POST'])
def add_farm_activity():
    """Add a new farm activity"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to add activities'}), 401
        
        data = request.get_json()
        
        # Validate input
        required_fields = ['activity_type', 'scheduled_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        activity_type = sanitize_text(data['activity_type'], max_length=100)
        crop_type = sanitize_text(data.get('crop_type', ''), max_length=100)
        description = sanitize_description(data.get('description', ''))
        
        scheduled_date = validate_date(data['scheduled_date'])
        if scheduled_date is None:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Save activity
        activity_id = db.save_farm_activity(
            user_id=user_id,
            activity_type=activity_type,
            crop_type=crop_type if crop_type else None,
            scheduled_date=scheduled_date,
            description=description
        )
        
        return jsonify({
            'activity_id': activity_id,
            'message': 'Activity added successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in add_farm_activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/farm/activity/<int:activity_id>', methods=['PUT'])
def update_farm_activity(activity_id):
    """Update activity status"""
    try:
        data = request.get_json()
        
        status = data.get('status')
        completed_date = data.get('completed_date')
        notes = data.get('notes', '')
        
        if not status:
            return jsonify({'error': 'status is required'}), 400
        
        # Sanitize inputs
        status = validate_enum(status, ['pending', 'completed', 'skipped'])
        if status is None:
            return jsonify({'error': 'Invalid status. Must be pending, completed, or skipped'}), 400
        
        notes = sanitize_description(notes)
        
        if completed_date:
            completed_date = validate_date(completed_date)
            if completed_date is None:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Update activity
        db.update_activity_status(activity_id, status, completed_date, notes)
        
        return jsonify({
            'message': 'Activity updated successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in update_farm_activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/farm/generate-schedule', methods=['POST'])
def generate_farm_schedule():
    """Generate AI-powered weekly schedule"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to generate schedule'}), 401
        
        data = request.get_json()
        
        crop_type = data.get('crop_type')
        growth_stage = data.get('growth_stage')
        
        if not crop_type:
            return jsonify({'error': 'crop_type is required'}), 400
        
        # Check rate limit
        allowed, remaining, reset_time = check_rate_limit(user_id, 'schedule')
        if not allowed:
            limit_info = get_rate_limit_info('schedule')
            return jsonify({
                'error': f'Rate limit exceeded. You can generate {limit_info["calls"]} schedules per {limit_info["window_minutes"]} minutes.',
                'rate_limit_exceeded': True,
                'remaining': remaining,
                'reset_time': reset_time
            }), 429
        
        crop_type = sanitize_text(crop_type, max_length=100)
        growth_stage = sanitize_text(growth_stage, max_length=100) if growth_stage else None
        
        # Record API call
        record_api_call(user_id, 'schedule')
        
        # Generate schedule
        schedule = generate_weekly_schedule(user_id, crop_type, growth_stage)
        
        return jsonify({
            'schedule': schedule,
            'message': 'Schedule generated successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in generate_farm_schedule: {e}")
        return jsonify({'error': str(e)}), 500

# --- Yield Prediction API Routes ---
@app.route('/yield-prediction')
def yield_prediction_page():
    """Render yield prediction interface"""
    return render_template('yield_prediction.html')

@app.route('/api/yield/predict', methods=['POST'])
def predict_crop_yield():
    """Generate yield prediction"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to predict yield'}), 401
        
        data = request.get_json()
        
        # Validate input
        required_fields = ['crop_type', 'planting_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check rate limit
        allowed, remaining, reset_time = check_rate_limit(user_id, 'yield_prediction')
        if not allowed:
            limit_info = get_rate_limit_info('yield_prediction')
            return jsonify({
                'error': f'Rate limit exceeded. You can generate {limit_info["calls"]} predictions per {limit_info["window_minutes"]} minutes.',
                'rate_limit_exceeded': True,
                'remaining': remaining,
                'reset_time': reset_time
            }), 429
        
        crop_type = sanitize_text(data['crop_type'], max_length=100)
        
        planting_date = validate_date(data['planting_date'])
        if planting_date is None:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        farm_data = data.get('farm_data', {})
        
        # Record API call
        record_api_call(user_id, 'yield_prediction')
        
        # Generate prediction
        prediction = predict_yield(user_id, crop_type, planting_date, farm_data)
        
        return jsonify(prediction)
    
    except Exception as e:
        print(f"Error in predict_crop_yield: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/yield/record-actual', methods=['POST'])
def record_actual_yield():
    """Record actual harvest data"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['prediction_id', 'actual_yield']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate and sanitize inputs
        prediction_id = validate_integer(data['prediction_id'], min_value=1)
        if prediction_id is None:
            return jsonify({'error': 'Invalid prediction_id'}), 400
        
        actual_yield = validate_numeric(data['actual_yield'], min_value=0)
        if actual_yield is None:
            return jsonify({'error': 'Invalid actual_yield. Must be a positive number'}), 400
        
        actual_quality = sanitize_text(data.get('actual_quality', 'B'), max_length=10)
        
        # Update prediction with actual data
        db.update_actual_yield(prediction_id, actual_yield, actual_quality)
        
        return jsonify({
            'message': 'Actual yield recorded successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in record_actual_yield: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/yield/history', methods=['GET'])
def get_yield_history():
    """Get prediction accuracy history"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view history'}), 401
        
        # Get predictions from database
        predictions = db.get_yield_predictions(user_id)
        
        # Calculate accuracy for predictions with actual data
        accuracy_data = []
        for pred in predictions:
            if pred.get('actual_yield'):
                predicted = pred.get('predicted_yield', 0)
                actual = pred.get('actual_yield', 0)
                accuracy = (actual / predicted * 100) if predicted > 0 else 0
                
                accuracy_data.append({
                    'crop_type': pred.get('crop_type'),
                    'predicted_yield': predicted,
                    'actual_yield': actual,
                    'accuracy': round(accuracy, 2),
                    'date': pred.get('created_at')
                })
        
        return jsonify({
            'predictions': predictions,
            'accuracy_data': accuracy_data,
            'count': len(predictions),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_yield_history: {e}")
        return jsonify({'error': str(e)}), 500

# --- Financial Health API Routes ---
@app.route('/financial-health')
def financial_health_page():
    """Render financial health dashboard"""
    return render_template('financial_health.html')

@app.route('/api/finance/score', methods=['GET'])
def get_financial_score():
    """Calculate and return financial health score"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view financial score'}), 401
        
        # Check rate limit
        allowed, remaining, reset_time = check_rate_limit(user_id, 'financial_score')
        if not allowed:
            limit_info = get_rate_limit_info('financial_score')
            return jsonify({
                'error': f'Rate limit exceeded. You can calculate {limit_info["calls"]} scores per {limit_info["window_minutes"]} minutes.',
                'rate_limit_exceeded': True,
                'remaining': remaining,
                'reset_time': reset_time
            }), 429
        
        # Record API call
        record_api_call(user_id, 'financial_score')
        
        # Calculate health score
        score_data = calculate_health_score(user_id)
        
        return jsonify(score_data)
    
    except Exception as e:
        print(f"Error in get_financial_score: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/finance/expense', methods=['POST'])
def add_expense():
    """Add expense record"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to add expenses'}), 401
        
        data = request.get_json()
        
        # Validate input
        required_fields = ['category', 'amount', 'expense_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        category = sanitize_text(data['category'], max_length=100)
        
        amount = validate_amount(data['amount'])
        if amount is None:
            return jsonify({'error': 'Invalid amount. Must be a positive number'}), 400
        
        expense_date = validate_date(data['expense_date'])
        if expense_date is None:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        description = sanitize_description(data.get('description', ''))
        
        # Save expense
        expense_id = db.save_expense(
            user_id=user_id,
            category=category,
            amount=amount,
            expense_date=expense_date,
            description=description
        )
        
        return jsonify({
            'expense_id': expense_id,
            'message': 'Expense added successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in add_expense: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/finance/expenses', methods=['GET'])
def get_expenses():
    """Get user expenses with optional filtering"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view expenses'}), 401
        
        # Get filter parameter
        filter_type = request.args.get('filter', 'all')
        
        # Calculate date range based on filter
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        
        if filter_type == 'week':
            start_date = end_date - timedelta(days=7)
        elif filter_type == 'month':
            start_date = end_date - timedelta(days=30)
        elif filter_type == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = None
        
        # Get expenses from database
        expenses = db.get_expenses(user_id, start_date, end_date)
        
        # Calculate totals by category
        category_totals = {}
        total_amount = 0
        
        for expense in expenses:
            category = expense['category']
            amount = expense['amount']
            
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += amount
            total_amount += amount
        
        return jsonify({
            'expenses': expenses,
            'category_totals': category_totals,
            'total_amount': total_amount,
            'count': len(expenses),
            'filter': filter_type,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_expenses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/finance/report', methods=['GET'])
def get_financial_report():
    """Generate detailed financial report"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view report'}), 401
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get expenses
        expenses = db.get_expenses(user_id, start_date, end_date)
        
        # Get yield predictions
        yield_predictions = db.get_yield_predictions(user_id)
        
        # Analyze cost efficiency
        cost_analysis = analyze_cost_efficiency(expenses, yield_predictions)
        
        # Get latest financial score
        latest_score = db.get_latest_financial_score(user_id)
        
        # Calculate totals
        total_expenses = sum(e.get('amount', 0) if e.get('amount') is not None else 0 for e in expenses)
        
        # Group expenses by category
        expense_by_category = {}
        for expense in expenses:
            category = expense.get('category', 'other')
            amount = expense.get('amount', 0) if expense.get('amount') is not None else 0
            expense_by_category[category] = expense_by_category.get(category, 0) + amount
        
        # Estimate revenue from yield predictions
        total_income = 0
        for pred in yield_predictions:
            yield_amount = pred.get('actual_yield') or pred.get('predicted_yield')
            # Ensure yield_amount is a number and not None
            if yield_amount is not None:
                try:
                    yield_amount = float(yield_amount)
                    if yield_amount > 0:
                        # Assume average price of ₹20/kg
                        total_income += yield_amount * 20
                except (ValueError, TypeError):
                    continue
        
        net_profit = total_income - total_expenses
        profit_margin = ((net_profit / total_income) * 100) if total_income > 0 else 0
        
        return jsonify({
            'expenses': expenses,
            'total_expenses': total_expenses,
            'total_income': total_income,
            'net_profit': net_profit,
            'profit_margin': profit_margin,
            'expense_by_category': expense_by_category,
            'cost_analysis': cost_analysis,
            'latest_score': latest_score,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_financial_report: {e}")
        return jsonify({'error': str(e)}), 500

# --- Messaging API Routes ---
@app.route('/messages')
def messages_page():
    """Render messaging interface"""
    return render_template('messages.html')

@app.route('/api/messages/inbox', methods=['GET'])
def get_inbox():
    """Get user's conversations"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        limit = request.args.get('limit', 50, type=int)
        
        # Get inbox messages
        inbox_messages = db.get_inbox(user_id, limit)
        
        # Transform to conversation format
        conversations = []
        for msg in inbox_messages:
            # Determine the other user (not the current user)
            if msg['sender_id'] == user_id:
                other_user_id = msg['receiver_id']
                # Get receiver info
                other_user = db.get_user_by_id(other_user_id)
                other_user_name = other_user['name'] if other_user else 'Unknown User'
                other_user_location = other_user.get('location', '') if other_user else ''
            else:
                other_user_id = msg['sender_id']
                other_user_name = msg.get('sender_name', 'Unknown User')
                # Get sender location
                other_user = db.get_user_by_id(other_user_id)
                other_user_location = other_user.get('location', '') if other_user else ''
            
            conversations.append({
                'other_user_id': other_user_id,
                'other_user_name': other_user_name,
                'other_user_location': other_user_location,
                'last_message': msg['message_text'],
                'last_message_time': msg['created_at'],
                'unread_count': msg.get('unread_count', 0) if msg['sender_id'] != user_id else 0
            })
        
        # Calculate total unread count
        unread_count = sum(conv['unread_count'] for conv in conversations)
        
        return jsonify({
            'conversations': conversations,
            'count': len(conversations),
            'unread_count': unread_count,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_inbox: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/thread/<int:other_user_id>', methods=['GET'])
def get_message_thread(other_user_id):
    """Get conversation with specific user"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get conversation messages
        messages = db.get_conversation(user_id, other_user_id)
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg['id'],
                'message_text': msg['message_text'],
                'created_at': msg['created_at'],
                'is_sent': msg['sender_id'] == user_id,
                'is_read': msg.get('is_read', 0) == 1
            })
        
        return jsonify({
            'messages': formatted_messages,
            'count': len(formatted_messages),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_message_thread: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    """Send message to another user"""
    try:
        # Get user_id from session
        sender_id = session.get('user_id')
        
        if not sender_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        # Validate input
        if 'receiver_id' not in data:
            return jsonify({'error': 'receiver_id is required'}), 400
        
        if 'message_text' not in data:
            return jsonify({'error': 'message_text is required'}), 400
        
        # Validate and sanitize inputs
        receiver_id = validate_user_id(data['receiver_id'])
        if receiver_id is None:
            return jsonify({'error': 'Invalid receiver_id'}), 400
        
        message_text = sanitize_message(data['message_text'])
        
        if not message_text:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Check if blocked
        if db.is_blocked(receiver_id, sender_id):
            return jsonify({'error': 'Cannot send message to this user'}), 403
        
        # Send message
        message_id = db.send_message(sender_id, receiver_id, message_text)
        
        return jsonify({
            'message_id': message_id,
            'message': 'Message sent successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in send_message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/read/<int:message_id>', methods=['PUT'])
def mark_message_as_read(message_id):
    """Mark message as read"""
    try:
        db.mark_message_read(message_id)
        
        return jsonify({
            'message': 'Message marked as read',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in mark_message_as_read: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/block/<int:blocked_user_id>', methods=['POST'])
def block_user(blocked_user_id):
    """Block a user"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Block user
        db.block_user(user_id, blocked_user_id)
        
        return jsonify({
            'message': 'User blocked successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in block_user: {e}")
        return jsonify({'error': str(e)}), 500

# --- Friend Network API Routes ---
@app.route('/friends')
def friends_page():
    """Render friends interface"""
    return render_template('friends.html')

@app.route('/api/friends/list', methods=['GET'])
def get_friends_list():
    """Get user's friends"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get friends
        friends = db.get_friends(user_id)
        
        return jsonify({
            'friends': friends,
            'count': len(friends),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_friends_list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/requests', methods=['GET'])
def get_friend_requests():
    """Get pending friend requests"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get friend requests from database
        raw_requests = db.get_friend_requests(user_id)
        
        # Format for frontend
        formatted_requests = []
        for req in raw_requests:
            formatted_requests.append({
                'request_id': req['id'],
                'requester_id': req['requester_id'],
                'name': req['requester_name'],
                'location': req.get('requester_location', 'Location not set'),
                'created_at': req['created_at']
            })
        
        return jsonify({
            'requests': formatted_requests,
            'count': len(formatted_requests),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_friend_requests: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/request/<int:recipient_id>', methods=['POST'])
def send_friend_request(recipient_id):
    """Send friend request"""
    try:
        # Get user_id from session
        requester_id = session.get('user_id')
        
        if not requester_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Check if already friends
        if db.are_friends(requester_id, recipient_id):
            return jsonify({'error': 'Already friends with this user'}), 400
        
        # Send friend request
        request_id = db.send_friend_request(requester_id, recipient_id)
        
        return jsonify({
            'request_id': request_id,
            'message': 'Friend request sent successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in send_friend_request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/accept/<int:request_id>', methods=['PUT'])
def accept_friend_request(request_id):
    """Accept friend request"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        db.accept_friend_request(request_id)
        
        return jsonify({
            'message': 'Friend request accepted',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in accept_friend_request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/remove/<int:friend_id>', methods=['DELETE'])
def remove_friend(friend_id):
    """Remove friend"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Remove friend
        db.remove_friend(user_id, friend_id)
        
        return jsonify({
            'message': 'Friend removed successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in remove_friend: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/suggestions', methods=['GET'])
def get_friend_suggestions():
    """Get friend suggestions based on location and crops"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user info
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get existing friends to filter out
        friends = db.get_friends(user_id)
        friend_ids = [f['id'] for f in friends]
        
        # Try to find nearby farmers if location data is available
        suggestions = []
        try:
            nearby = find_nearby_farmers(user_id, radius_km=100)
            suggestions = [s for s in nearby if s.get('farmer_id') not in friend_ids]
        except Exception as e:
            print(f"Could not find nearby farmers: {e}")
        
        # If no location-based suggestions, get random users
        if len(suggestions) == 0:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get random users who are not friends
            friend_ids_str = ','.join(['?'] * len(friend_ids)) if friend_ids else '0'
            query = f'''
                SELECT id, name, location
                FROM users
                WHERE id != ?
                AND id NOT IN ({friend_ids_str})
                ORDER BY RANDOM()
                LIMIT 10
            '''
            
            params = [user_id] + friend_ids if friend_ids else [user_id]
            cursor.execute(query, params)
            
            users = cursor.fetchall()
            conn.close()
            
            suggestions = [{
                'id': u['id'],
                'farmer_id': u['id'],  # Keep for backward compatibility
                'name': u['name'],
                'location': u['location'] or 'Location not set',
                'distance': None
            } for u in users]
        else:
            # Normalize location-based suggestions to also have 'id' field
            suggestions = [{
                'id': s.get('farmer_id'),
                'farmer_id': s.get('farmer_id'),
                'name': s.get('name'),
                'location': s.get('location', 'Location not set'),
                'distance': s.get('distance')
            } for s in suggestions]
        
        return jsonify({
            'suggestions': suggestions[:10],
            'count': len(suggestions[:10]),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_friend_suggestions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/search', methods=['GET'])
def search_users():
    """Search for users by name or location"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'users': [], 'count': 0, 'success': True})
        
        # Search users in database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Search by name or location (case-insensitive)
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT id, name, location
            FROM users
            WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(location) LIKE LOWER(?))
            AND id != ?
            LIMIT 20
        """, (search_pattern, search_pattern, user_id))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'location': row[2] or 'Location not set'
            })
        
        conn.close()
        
        return jsonify({
            'users': users,
            'count': len(users),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in search_users: {e}")
        return jsonify({'error': str(e)}), 500

# --- Notification API Routes ---
@app.route('/api/notifications/counts', methods=['GET'])
def get_notification_counts():
    """Get notification counts for unread messages and friend requests"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            # Try to get from session or return zeros
            return jsonify({
                'unread_messages': 0,
                'friend_requests': 0,
                'success': True
            })
        
        # Get unread message count
        inbox = db.get_inbox(user_id, limit=100)
        unread_messages = sum(1 for conv in inbox if not conv.get('is_read', True))
        
        # Get pending friend request count
        friend_requests = db.get_friend_requests(user_id)
        pending_requests = sum(1 for req in friend_requests if req.get('status') == 'pending')
        
        return jsonify({
            'unread_messages': unread_messages,
            'friend_requests': pending_requests,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_notification_counts: {e}")
        # Return zeros on error to not disrupt user experience
        return jsonify({
            'unread_messages': 0,
            'friend_requests': 0,
            'success': False,
            'error': str(e)
        }), 200  # Return 200 to avoid error handling on client

# --- Privacy Settings Routes ---
@app.route('/privacy-settings')
def privacy_settings_page():
    """Render privacy settings page"""
    return render_template('privacy_settings.html')


# --- Privacy Settings API Routes ---
@app.route('/api/privacy/location', methods=['GET'])
def get_location_privacy():
    """Get user's location privacy settings"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Validate user_id
        user_id = validate_user_id(user_id)
        if user_id is None:
            return jsonify({'error': 'Invalid user_id'}), 400
        
        # Get user's privacy settings
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT location_privacy, latitude, longitude, location
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'location_privacy': user['location_privacy'] or 'district',
            'has_location': user['latitude'] is not None and user['longitude'] is not None,
            'location_text': user['location'],
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_location_privacy: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/privacy/location', methods=['PUT'])
def update_location_privacy():
    """Update user's location privacy settings"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Validate and sanitize inputs
        user_id = validate_user_id(data['user_id'])
        if user_id is None:
            return jsonify({'error': 'Invalid user_id'}), 400
        
        # Validate privacy level
        privacy_level = data.get('privacy_level')
        if privacy_level:
            privacy_level = validate_enum(privacy_level, ['exact', 'district', 'state', 'hidden'])
            if privacy_level is None:
                return jsonify({'error': 'Invalid privacy_level. Must be: exact, district, state, or hidden'}), 400
        
        # Validate location coordinates if provided
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is not None:
            latitude = validate_latitude(latitude)
            if latitude is None:
                return jsonify({'error': 'Invalid latitude. Must be between -90 and 90'}), 400
        
        if longitude is not None:
            longitude = validate_longitude(longitude)
            if longitude is None:
                return jsonify({'error': 'Invalid longitude. Must be between -180 and 180'}), 400
        
        # Update user's privacy settings
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        
        if privacy_level:
            update_fields.append('location_privacy = ?')
            update_values.append(privacy_level)
        
        if latitude is not None:
            update_fields.append('latitude = ?')
            update_values.append(latitude)
        
        if longitude is not None:
            update_fields.append('longitude = ?')
            update_values.append(longitude)
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        update_values.append(user_id)
        
        cursor.execute(f'''
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Privacy settings updated successfully',
            'success': True
        })
    
    except Exception as e:
        print(f"Error in update_location_privacy: {e}")
        return jsonify({'error': str(e)}), 500


# --- Community Map API Routes ---
@app.route('/community-map')
def community_map_page():
    """Render community map interface"""
    return render_template('community_map.html')

@app.route('/api/map/farmers', methods=['GET'])
def get_farmers_map_data():
    """Get aggregated farmer location data"""
    try:
        privacy_level = request.args.get('privacy_level', 'district')
        
        # Get aggregated data
        farmers_data = aggregate_farmer_locations(privacy_level)
        
        return jsonify({
            'farmers': farmers_data,
            'count': len(farmers_data),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_farmers_map_data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/region/<region_id>', methods=['GET'])
def get_region_statistics(region_id):
    """Get regional statistics"""
    try:
        # Get regional stats
        stats = get_regional_stats(region_id)
        
        # Get trending topics
        trending = get_trending_topics(region_id)
        
        return jsonify({
            'stats': stats,
            'trending': trending,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_region_statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/nearby', methods=['GET'])
def get_nearby_farmers():
    """Get nearby farmers (privacy-aware)"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to find nearby farmers'}), 401
        
        radius_km = request.args.get('radius', 50, type=int)
        
        # Find nearby farmers
        nearby = find_nearby_farmers(user_id, radius_km)
        
        # Normalize field names for frontend
        formatted_farmers = []
        for farmer in nearby:
            formatted_farmers.append({
                'id': farmer.get('farmer_id'),
                'farmer_id': farmer.get('farmer_id'),  # Keep for backward compatibility
                'name': farmer.get('name'),
                'location': farmer.get('location'),
                'distance': farmer.get('distance_km'),
                'latitude': farmer.get('latitude'),
                'longitude': farmer.get('longitude'),
                'exact_location': farmer.get('exact_location', False)
            })
        
        return jsonify({
            'farmers': formatted_farmers,
            'count': len(nearby),
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_nearby_farmers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/stats', methods=['GET'])
def get_map_stats():
    """Get overall network statistics"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to view stats'}), 401
        
        # Get statistics from database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Count total farmers
        cursor.execute("SELECT COUNT(*) FROM users")
        total_farmers = cursor.fetchone()[0]
        
        # Count farmers with location
        cursor.execute("SELECT COUNT(*) FROM users WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        farmers_with_location = cursor.fetchone()[0]
        
        # Count by state
        cursor.execute("SELECT location, COUNT(*) as count FROM users GROUP BY location ORDER BY count DESC LIMIT 5")
        top_states = [{'state': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_farmers': total_farmers,
            'farmers_with_location': farmers_with_location,
            'top_states': top_states,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in get_map_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/privacy', methods=['PUT'])
def update_user_privacy():
    """Update user privacy settings"""
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login to update privacy'}), 401
        
        data = request.get_json()
        
        # Get privacy level
        privacy_level = data.get('location_privacy', 'district')
        
        # Validate privacy level
        valid_levels = ['exact', 'district', 'state', 'hidden']
        if privacy_level not in valid_levels:
            return jsonify({'error': f'Invalid privacy level. Must be one of: {", ".join(valid_levels)}'}), 400
        
        # Update in database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET location_privacy = ? WHERE id = ?",
            (privacy_level, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Privacy settings updated successfully',
            'location_privacy': privacy_level,
            'success': True
        })
    
    except Exception as e:
        print(f"Error in update_user_privacy: {e}")
        return jsonify({'error': str(e)}), 500

# --- 12. Run the Flask App ---
if __name__ == '__main__':
    print("🌱 AI Raitha Mitra - Smart Farming Solutions")
    print("=" * 50)
    print("🚀 Starting Flask server...")
    
    print("🔐 Authentication: Simple email/password (no OTP required)")
    
    print("💾 Storage: SQLite database (persistent storage)")
    
    print("🔑 Demo login credentials:")
    print("   Email: demo@raithamitra.com")
    print("   Mobile: 9876543210")
    print("   Password: 123456")
    
    # Get port from environment variable (for Render) or use 5001 for local
    port = int(os.getenv('PORT', 5002))
    # Get host from environment variable (0.0.0.0 for production, 127.0.0.1 for local)
    host = os.getenv('HOST', '127.0.0.1')
    # Debug mode from environment variable (False for production)
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(debug=debug, host=host, port=port)