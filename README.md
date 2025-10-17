# 🌾 AI Raitha Mitra - Smart Farming Solutions

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.20.0-orange.svg)](https://tensorflow.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI Raitha Mitra** is an intelligent agricultural platform that empowers farmers with AI-powered crop disease detection, real-time weather information, and comprehensive treatment recommendations in multiple Indian languages.

## 🌟 Features

### 🤖 AI-Powered Disease Detection
- **95% Accuracy**: Advanced TensorFlow model trained on 38+ crop diseases
- **Instant Results**: Upload crop images and get immediate disease identification
- **Confidence Scoring**: Detailed confidence percentages for each prediction
- **Yield Impact Assessment**: Understand potential crop loss from diseases

### 💬 Smart FAQ Chatbot with Context Memory
- **Intelligent Conversations**: AI-powered chatbot that remembers your farming context
- **Contextual Advice**: Personalized recommendations based on your crop history and location
- **Multi-Language Support**: Chat in 10 Indian languages with natural responses
- **Conversation History**: Access past discussions and build on previous advice
- **24/7 Availability**: Get farming guidance anytime, anywhere

### 🌾 Autonomous Farm Planning Agent
- **AI-Generated Schedules**: Weekly task recommendations based on crop type and growth stage
- **Smart Task Management**: Track irrigation, fertilization, pest control, and harvesting activities
- **Weather-Aware Planning**: Automatic adjustments based on weather forecasts
- **Activity History**: Monitor completed tasks and farming decisions over time
- **Proactive Reminders**: Never miss critical farming activities

### 📊 Predictive Yield Analytics
- **Yield Forecasting**: AI-powered predictions for crop quantity and quality
- **Confidence Scoring**: Understand prediction reliability with confidence levels
- **Harvest Timeline**: Know exactly when to prepare for harvest
- **Regional Benchmarking**: Compare your yields with regional averages
- **Preparation Checklists**: Get actionable steps for optimal harvest preparation
- **Accuracy Tracking**: Record actual yields to improve future predictions

### 💰 AI Financial Health Scoring
- **Farm Performance Score**: Overall financial health rating (0-100)
- **Cost Efficiency Analysis**: Track and optimize operational expenses
- **Profit Projections**: Forecast earnings based on yield predictions and market prices
- **Expense Tracking**: Categorize and monitor farming costs
- **AI Recommendations**: Get personalized advice to improve financial health
- **Detailed Reports**: Comprehensive financial insights and trends

### 👥 Farmer Community Network
- **Direct Messaging**: Connect and chat with fellow farmers
- **Friend Network**: Build your farming community with friend requests
- **Profile Discovery**: Search and find farmers by location, crops, and interests
- **Notification System**: Stay updated on messages and friend requests
- **Privacy Controls**: Manage who can contact you and see your information
- **User Blocking**: Control your community experience

### 🗺️ Interactive Community Map
- **Geographic Visualization**: See farmer distribution across India
- **Regional Statistics**: View farmer counts, active users, and popular crops by region
- **Nearby Farmers**: Discover farmers in your area (privacy-aware)
- **Crop Filtering**: Find farmers growing specific crops
- **Trending Topics**: See what's popular in different regions
- **Privacy Levels**: Control location sharing (exact, district, state, or hidden)

### 🌤️ Real-Time Weather Integration
- **Current Weather**: Live temperature, humidity, wind speed, and pressure
- **5-Day Forecast**: Detailed weather predictions for farming decisions
- **Location Services**: Auto-detect user location or manual city selection
- **Farming-Focused**: Weather data tailored for agricultural planning

### 🌍 Multi-Language Support
- **10 Indian Languages**: Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, Gujarati, Bengali, Punjabi
- **AI Translation**: Gemini AI provides treatment advice in local languages
- **Farmer-Friendly**: Simple, actionable language for rural communities

### 💊 Comprehensive Treatment Recommendations
- **Organic Solutions**: Natural, eco-friendly treatment methods
- **Chemical Options**: Effective chemical treatments with proper dosages
- **Prevention Tips**: Proactive measures to prevent disease recurrence
- **Market Prices**: Real-time crop pricing from major Indian markets

### 👤 User Management
- **Simple Authentication**: Email/mobile + password (no OTP complexity)
- **Prediction History**: Track all disease detections with images
- **Profile Management**: User profiles with prediction analytics
- **Secure Storage**: SQLite database with encrypted passwords

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- 4GB+ RAM (for TensorFlow model)
- Internet connection (for AI services)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/ai-raitha-mitra.git
   cd ai-raitha-mitra
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv myenv
   
   # Windows
   myenv\Scripts\activate
   
   # Linux/Mac
   source myenv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy and edit environment file
   cp .env.example .env
   
   # Add your API keys (see Configuration section)
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Application**
   ```
   Open http://127.0.0.1:5000 in your browser
   ```

## ⚙️ Configuration

### Required API Keys

#### 1. Gemini AI API (Required)
```env
GEMINI_API_KEY="your_gemini_api_key_here"
```
- Get free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Used for treatment recommendations and translations

#### 2. OpenWeatherMap API (Optional)
```env
OPENWEATHER_API_KEY="your_openweather_api_key_here"
```
- Get free API key from [OpenWeatherMap](https://openweathermap.org/api)
- Used for live weather data (falls back to demo data if not configured)

### Environment Variables
```env
# AI Configuration
GEMINI_API_KEY="your_gemini_api_key_here"

# Weather Configuration
OPENWEATHER_API_KEY="your_openweather_api_key_here"

# Flask Configuration
FLASK_SECRET_KEY="your_secret_key_here"
FLASK_DEBUG=True
```

## 📱 Usage

### For Farmers

1. **Register/Login**
   - Create account with email/mobile and password
   - No OTP verification required - instant access

2. **Disease Detection**
   - Upload clear crop images (leaves, fruits, stems)
   - Get instant AI-powered disease identification
   - View detailed treatment recommendations

3. **Smart Chat Assistant**
   - Ask farming questions in your local language
   - Get personalized advice based on your farming context
   - Access conversation history for reference
   - Receive crop-specific and season-appropriate guidance

4. **Farm Planning**
   - View AI-generated weekly schedules
   - Add and track farming activities
   - Mark tasks as complete with notes
   - Get weather-aware recommendations
   - Monitor activity history

5. **Yield Prediction**
   - Get AI-powered yield forecasts for your crops
   - View confidence scores and harvest timelines
   - Compare with regional averages
   - Record actual yields for accuracy improvement
   - Access preparation checklists

6. **Financial Health**
   - Check your farm's financial health score
   - Track expenses by category
   - View cost efficiency analysis
   - Get AI-powered recommendations
   - Generate detailed financial reports

7. **Community Features**
   - Send messages to other farmers
   - Build your friend network
   - Search for farmers by location and crops
   - View notifications for messages and requests
   - Manage privacy settings

8. **Community Map**
   - Explore farmer distribution across India
   - View regional statistics and trends
   - Find nearby farmers (with privacy controls)
   - Filter by crop types
   - See trending topics by region

9. **Weather Information**
   - Check current weather conditions
   - View 5-day forecast for farming decisions
   - Use location services for accurate local weather

10. **Treatment Guidance**
    - Organic and chemical treatment options
    - Step-by-step instructions in local language
    - Prevention tips to avoid future issues

11. **History Tracking**
    - View all past disease predictions
    - Click predictions for detailed treatment info
    - Track farming decisions over time

### Demo Credentials
```
Email: demo@raithamitra.com
Password: 123456
```

## 🏗️ Project Structure

```
AI Raitha Mitra/
├── 📁 static/
│   ├── 📁 css/
│   │   └── main.css              # Main stylesheet with modern design
│   ├── 📁 js/
│   │   ├── auth.js               # Authentication functionality
│   │   ├── chat.js               # Chat interface functionality
│   │   ├── community-map.js      # Interactive map functionality
│   │   ├── disease-detection.js  # Disease detection logic
│   │   ├── farm-planner.js       # Farm planning interface
│   │   ├── financial-health.js   # Financial dashboard
│   │   ├── friends.js            # Friend network functionality
│   │   ├── main.js               # Core JavaScript functionality
│   │   ├── messages.js           # Messaging system
│   │   ├── notifications.js      # Notification system
│   │   ├── privacy-settings.js   # Privacy controls
│   │   ├── weather.js            # Weather widget functionality
│   │   └── yield-prediction.js   # Yield prediction interface
│   └── 📁 uploads/               # User-uploaded images storage
├── 📁 templates/
│   ├── chat.html                 # Chat interface
│   ├── community_map.html        # Community map interface
│   ├── farm_planner.html         # Farm planning interface
│   ├── financial_health.html     # Financial dashboard
│   ├── friends.html              # Friend network interface
│   ├── home.html                 # Landing page with weather widget
│   ├── index.html                # Disease detection interface
│   ├── login.html                # User login interface
│   ├── messages.html             # Messaging interface
│   ├── privacy_settings.html     # Privacy settings page
│   ├── register.html             # User registration interface
│   └── yield_prediction.html     # Yield prediction interface
├── app.py                        # Main Flask application
├── chat_service.py               # Chat AI service module
├── database.py                   # SQLite database management
├── farm_service.py               # Farm planning service module
├── finance_service.py            # Financial analysis service module
├── map_service.py                # Map and location service module
├── rate_limiter.py               # API rate limiting
├── security_utils.py             # Input sanitization and validation
├── yield_service.py              # Yield prediction service module
├── crop_disease_model.py         # AI model training script
├── class_names.json              # Disease classification labels
├── crop_disease_detection_model.h5  # Trained TensorFlow model
├── migrate_database.py           # Database migration script
├── rollback_migration.py         # Migration rollback script
├── raitha_mitra.db              # SQLite database file
├── reset_user_password.py       # Password reset utility
├── requirements.txt              # Python dependencies
├── .env                          # Environment configuration
├── API_ROUTES_REFERENCE.md      # Complete API documentation
├── DATABASE_SCHEMA.md           # Database schema documentation
├── WEATHER_SETUP.md             # Weather API setup guide
└── README.md                     # This file
```

## 🤖 AI Model Details

### Disease Detection Model
- **Architecture**: Convolutional Neural Network (CNN)
- **Framework**: TensorFlow 2.20.0
- **Input Size**: 128x128x3 RGB images
- **Classes**: 38+ crop diseases across multiple crops
- **Accuracy**: 95%+ on validation dataset

### Gemini AI Integration
- **Chat Assistant**: Context-aware conversational AI
- **Farm Planning**: AI-generated task schedules
- **Yield Prediction**: ML-powered yield forecasting
- **Financial Analysis**: Intelligent cost optimization
- **Multi-Language**: Natural language processing in 10 Indian languages

### Service Modules Architecture

**chat_service.py**
- Contextual response generation
- Conversation history management
- Farming context extraction
- Multi-language support

**farm_service.py**
- Weekly schedule generation
- Task recommendations
- Growth stage calculation
- Weather-based adjustments

**yield_service.py**
- Yield prediction algorithms
- Confidence scoring
- Regional benchmarking
- Preparation checklists

**finance_service.py**
- Financial health scoring
- Cost efficiency analysis
- Profit projections
- AI-powered recommendations

**map_service.py**
- Location aggregation (privacy-aware)
- Regional statistics
- Nearby farmer discovery
- Trending topics analysis

### Supported Crops & Diseases
- **Apple**: Apple Scab, Black Rot, Cedar Apple Rust
- **Corn**: Cercospora Leaf Spot, Common Rust, Northern Leaf Blight
- **Grape**: Black Rot, Esca, Leaf Blight
- **Orange**: Huanglongbing (Citrus Greening)
- **Potato**: Early Blight, Late Blight
- **Tomato**: Bacterial Spot, Early Blight, Late Blight, Leaf Mold, Septoria Leaf Spot, Spider Mites, Target Spot, Yellow Leaf Curl Virus, Mosaic Virus
- **Cherry**: Various diseases and healthy detection

## 🌐 API Endpoints

### Authentication
```http
POST /api/register          # User registration
POST /api/login             # User login
POST /api/change-password   # Change password
```

### Disease Detection
```http
POST /predict               # Disease prediction from image
GET /api/prediction-history # User's prediction history
```

### Chat Assistant
```http
GET  /chat                  # Chat interface page
POST /api/chat/send         # Send message and get AI response
GET  /api/chat/history      # Retrieve chat history
```

### Farm Planning
```http
GET  /farm-planner                  # Farm planner interface
GET  /api/farm/schedule             # Get farm schedule
POST /api/farm/activity             # Add farm activity
PUT  /api/farm/activity/<id>        # Update activity status
POST /api/farm/generate-schedule    # AI-generate weekly tasks
```

### Yield Prediction
```http
GET  /yield-prediction          # Yield prediction interface
POST /api/yield/predict         # Generate yield prediction
POST /api/yield/record-actual   # Record actual harvest data
GET  /api/yield/history         # Get prediction history
```

### Financial Health
```http
GET  /financial-health      # Financial dashboard
GET  /api/finance/score     # Calculate health score
POST /api/finance/expense   # Add expense record
GET  /api/finance/report    # Generate financial report
```

### Messaging
```http
GET  /messages                      # Messaging interface
GET  /api/messages/inbox            # Get user's conversations
GET  /api/messages/thread/<user_id> # Get conversation thread
POST /api/messages/send             # Send message
PUT  /api/messages/read/<id>        # Mark message as read
POST /api/messages/block/<user_id>  # Block user
```

### Friend Network
```http
GET    /friends                         # Friends interface
GET    /api/friends/list                # Get friends list
POST   /api/friends/request/<user_id>   # Send friend request
PUT    /api/friends/accept/<request_id> # Accept friend request
DELETE /api/friends/remove/<user_id>    # Remove friend
GET    /api/friends/suggestions         # Get friend suggestions
```

### Community Map
```http
GET /community-map              # Community map interface
GET /api/map/farmers            # Get farmer location data
GET /api/map/region/<region_id> # Get regional statistics
GET /api/map/nearby             # Get nearby farmers
```

### Weather
```http
GET /api/weather           # Current weather data
GET /api/weather/forecast  # Weather forecast
```

### Notifications
```http
GET /api/notifications     # Get user notifications
```

For complete API documentation with request/response examples, see [API_ROUTES_REFERENCE.md](API_ROUTES_REFERENCE.md)

## 🛠️ Development

### Setting Up Development Environment

1. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Enable Debug Mode**
   ```env
   FLASK_DEBUG=True
   ```

3. **Database Management**
   ```bash
   # Reset user password
   python reset_user_password.py
   
   # Train new model (if needed)
   python crop_disease_model.py
   ```

### Code Structure

#### Backend (Python/Flask)
- **app.py**: Main application with routes and business logic
- **database.py**: SQLite database operations and management
- **crop_disease_model.py**: AI model training and evaluation

#### Frontend (HTML/CSS/JavaScript)
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Gradient buttons, animations, and clean layouts
- **Progressive Enhancement**: Works without JavaScript for basic functionality

#### AI Integration
- **TensorFlow**: Local disease detection model
- **Gemini AI**: Treatment recommendations and translations
- **Image Processing**: PIL for image preprocessing and optimization

## 🔧 Troubleshooting

### Common Issues

#### 1. Model Loading Error
```
Error: Local model or class names file not found
```
**Solution**: Ensure `crop_disease_detection_model.h5` and `class_names.json` exist in project root

#### 2. Gemini AI Error
```
Error configuring Gemini AI: Invalid API key
```
**Solution**: Check `GEMINI_API_KEY` in `.env` file and ensure it's valid

#### 3. Weather Not Loading
```
Weather API not configured
```
**Solution**: Add `OPENWEATHER_API_KEY` to `.env` file (optional - falls back to demo data)

#### 4. Database Error
```
Database connection failed
```
**Solution**: Ensure SQLite is installed and `raitha_mitra.db` has proper permissions

### Security & Privacy Features

1. **Input Sanitization**: All user inputs sanitized to prevent XSS/SQL injection
2. **Location Privacy**: Granular controls (exact, district, state, hidden)
3. **User Blocking**: Control who can contact you
4. **Rate Limiting**: Prevent API abuse on AI-powered features
5. **Password Hashing**: Secure password storage with Werkzeug
6. **Session Management**: Secure user authentication
7. **Privacy Settings**: User-controlled visibility and sharing

### Performance Optimization

1. **Image Upload Size**: Limit images to 5MB for faster processing
2. **Model Caching**: TensorFlow model is loaded once at startup
3. **Database Indexing**: Optimized queries with 8 strategic indexes
4. **Static File Caching**: CSS/JS files cached for better performance
5. **AI Response Caching**: Reduce redundant API calls
6. **Lazy Loading**: Progressive map marker loading
7. **Pagination**: Efficient data loading for large datasets

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   ```

2. **Security Configuration**
   ```env
   # Use strong secret key
   FLASK_SECRET_KEY="your-strong-secret-key-here"
   
   # Configure HTTPS for production
   ```

3. **Web Server**
   ```bash
   # Using Gunicorn (recommended)
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   
   # Or using uWSGI
   pip install uwsgi
   uwsgi --http :8000 --wsgi-file app.py --callable app
   ```

4. **Database Backup**
   ```bash
   # Regular backup of SQLite database
   cp raitha_mitra.db raitha_mitra_backup_$(date +%Y%m%d).db
   ```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 📊 Analytics & Monitoring

### Built-in Analytics
- **User Registration Tracking**: Monitor farmer adoption
- **Disease Detection Stats**: Track most common diseases
- **Geographic Distribution**: Understand regional disease patterns
- **Treatment Effectiveness**: Monitor farmer feedback

### Monitoring Endpoints
```http
GET /api/health            # Application health check
GET /api/stats             # Basic usage statistics
```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Areas for Contribution
1. **New Disease Models**: Train models for additional crops
2. **Language Support**: Add more regional languages
3. **UI/UX Improvements**: Enhance farmer experience
4. **Performance Optimization**: Improve speed and efficiency
5. **Documentation**: Improve guides and tutorials

### Development Guidelines
1. **Fork the Repository**: Create your own copy
2. **Create Feature Branch**: `git checkout -b feature/new-feature`
3. **Follow Code Style**: Use Python PEP 8 standards
4. **Add Tests**: Include tests for new functionality
5. **Submit Pull Request**: Describe changes clearly

### Database Migrations

When making database changes:

```bash
# Run migration to add new tables/columns
python migrate_database.py

# Rollback migration if needed (WARNING: deletes data)
python rollback_migration.py
```

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete schema documentation.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TensorFlow Team**: For the machine learning framework
- **Google AI**: For Gemini AI API and translation services
- **OpenWeatherMap**: For weather data API
- **Flask Community**: For the web framework
- **Indian Farmers**: For inspiration and feedback

## 📞 Support

### Getting Help
- **Documentation**: Check this README and `WEATHER_SETUP.md`
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join community discussions
- **Email**: Contact support team

### Community
- **GitHub**: [AI Raitha Mitra Repository](https://github.com/yourusername/ai-raitha-mitra)
- **Discussions**: Share experiences and get help
- **Feedback**: Help improve the platform for farmers

---

## 📚 Additional Documentation

- **[API Routes Reference](API_ROUTES_REFERENCE.md)**: Complete API endpoint documentation
- **[Database Schema](DATABASE_SCHEMA.md)**: Database structure and relationships
- **[Weather Setup Guide](WEATHER_SETUP.md)**: Weather API configuration
- **[Service Modules Summary](SERVICE_MODULES_SUMMARY.md)**: Business logic documentation
- **[Migration Summary](MIGRATION_SUMMARY.md)**: Database migration details

---

## 🔄 Recent Updates

### Version 2.0.0 - Advanced Features Release

**New Features:**
- ✅ Smart FAQ Chatbot with context memory
- ✅ Autonomous Farm Planning Agent
- ✅ Predictive Yield Analytics
- ✅ AI Financial Health Scoring
- ✅ Farmer Community Network
- ✅ Interactive Community Map
- ✅ Privacy Controls and Settings
- ✅ Notification System
- ✅ Rate Limiting for AI APIs

**Technical Improvements:**
- Extended database schema with 11 new tables
- Added 5 new service modules for business logic
- Implemented input sanitization and security utilities
- Added rate limiting for AI-powered features
- Enhanced responsive design for all new interfaces
- Comprehensive API documentation

**Database Changes:**
- Run `python migrate_database.py` to update your database
- See [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) for details

---

## 🌾 Made with ❤️ for Indian Farmers

**AI Raitha Mitra** is dedicated to empowering farmers with technology, helping them make informed decisions, and improving agricultural productivity across India.

*"Technology should serve humanity, and agriculture feeds humanity."*

---

### 📈 Project Status

- ✅ **Core Features**: Complete and tested
- ✅ **Advanced Features**: Fully implemented
- ✅ **AI Model**: Trained and optimized
- ✅ **Multi-language**: 10 Indian languages supported
- ✅ **Weather Integration**: Live data and forecasts
- ✅ **User Management**: Simplified authentication
- ✅ **Community Features**: Messaging, friends, and map
- ✅ **Smart Planning**: AI-powered farm management
- ✅ **Financial Tools**: Health scoring and expense tracking
- ✅ **Production Ready**: Deployed and scalable

**Version**: 2.0.0  
**Last Updated**: October 2025  
**Status**: Active Development