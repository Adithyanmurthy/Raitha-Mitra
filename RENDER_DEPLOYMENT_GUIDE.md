# Render Deployment Guide for Raitha Mitra

## 📋 Prerequisites

1. **GitHub Account** - Your code needs to be on GitHub
2. **Render Account** - Sign up at https://render.com (free tier available)
3. **API Keys** - Have your API keys ready:
   - Gemini API Key
   - Weather API Key

## 🚀 Step-by-Step Deployment

### Step 1: Push to GitHub

First, push your code to GitHub:

```bash
# Create a new repository on GitHub (don't initialize with README)
# Then run these commands:

git remote add origin https://github.com/YOUR_USERNAME/raitha-mitra.git
git branch -M main
git push -u origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub (recommended)
3. Authorize Render to access your repositories

### Step 3: Create New Web Service

1. Click **"New +"** button
2. Select **"Web Service"**
3. Connect your GitHub repository
4. Select the **raitha-mitra** repository

### Step 4: Configure Service

Fill in the following settings:

**Basic Settings:**
- **Name**: `raitha-mitra` (or your preferred name)
- **Region**: Choose closest to your users (e.g., Oregon, Singapore)
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

**Instance Type:**
- Select **Free** (or paid plan for better performance)

### Step 5: Add Environment Variables

Click **"Advanced"** and add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.11.0` | Python version |
| `FLASK_SECRET_KEY` | `your-secret-key-here` | Generate a random string |
| `FLASK_DEBUG` | `False` | Disable debug in production |
| `HOST` | `0.0.0.0` | Allow external connections |
| `GEMINI_API_KEY` | `your-gemini-api-key` | Your Gemini API key |
| `WEATHERAPI_KEY` | `your-weather-api-key` | Your Weather API key |

**To generate a secret key:**
```python
import secrets
print(secrets.token_hex(32))
```

### Step 6: Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying
3. Wait for deployment to complete (5-10 minutes)
4. Your app will be live at: `https://raitha-mitra.onrender.com`

## 📁 Files Created for Deployment

### 1. `render.yaml`
Blueprint for Render deployment configuration.

### 2. `Procfile`
Tells Render how to start your application.

### 3. `runtime.txt`
Specifies Python version.

### 4. `requirements.txt`
Updated with `gunicorn` for production server.

### 5. `app.py`
Updated to read PORT and HOST from environment variables.

## ⚙️ Configuration Details

### Gunicorn Settings
```
--workers 2          # Number of worker processes
--timeout 120        # Request timeout (2 minutes for AI processing)
--bind 0.0.0.0:$PORT # Bind to all interfaces on Render's port
```

### Environment Variables Explained

**FLASK_SECRET_KEY**: Used for session encryption
- Generate: `python -c "import secrets; print(secrets.token_hex(32))"`

**FLASK_DEBUG**: Should be `False` in production
- Prevents sensitive error messages from showing

**HOST**: Set to `0.0.0.0` to accept external connections
- Local: `127.0.0.1`
- Production: `0.0.0.0`

**PORT**: Automatically set by Render
- Don't set this manually

## 🔍 Monitoring & Logs

### View Logs
1. Go to your service dashboard
2. Click **"Logs"** tab
3. See real-time application logs

### Check Status
- **Live**: Service is running
- **Building**: Deployment in progress
- **Failed**: Check logs for errors

## ⚠️ Important Notes

### Free Tier Limitations
- **Spins down after 15 minutes of inactivity**
- First request after spin-down takes 30-60 seconds
- 750 hours/month free (enough for one service)

### Large Files (Git LFS)
- Model file: `crop_disease_detection_model.h5` (~100MB)
- Video file: `static/videos/demo.mp4` (~173MB)
- These are tracked with Git LFS
- Render supports Git LFS automatically

### Database
- SQLite database is included in the repository
- Data persists across deployments
- For production, consider PostgreSQL (Render offers free tier)

### Performance Tips
1. **Upgrade to paid plan** for:
   - No spin-down
   - More memory/CPU
   - Better performance

2. **Use CDN** for static files:
   - Cloudflare
   - AWS CloudFront

3. **Optimize model loading**:
   - Model loads on startup
   - First prediction is slower

## 🐛 Troubleshooting

### Build Fails
**Error**: `Could not find a version that satisfies the requirement tensorflow`
**Solution**: Check Python version matches requirements

### App Crashes on Start
**Error**: `ModuleNotFoundError`
**Solution**: Ensure all dependencies in requirements.txt

### 502 Bad Gateway
**Error**: App not responding
**Solution**: 
- Check logs for errors
- Increase timeout in Procfile
- Check memory usage

### Model Not Loading
**Error**: `FileNotFoundError: crop_disease_detection_model.h5`
**Solution**: 
- Ensure Git LFS is set up
- Check file is in repository
- Verify .gitattributes includes `*.h5`

### Database Errors
**Error**: `OperationalError: unable to open database file`
**Solution**:
- Ensure database file is in repository
- Check file permissions
- Verify database path in code

## 🔄 Updating Your App

### Deploy New Changes
```bash
# Make changes to your code
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically detect the push and redeploy!

### Manual Deploy
1. Go to service dashboard
2. Click **"Manual Deploy"**
3. Select **"Deploy latest commit"**

## 📊 Post-Deployment Checklist

- [ ] App loads successfully
- [ ] Login works (test with demo credentials)
- [ ] Disease detection works
- [ ] Chat assistant responds
- [ ] Weather data loads
- [ ] All pages accessible
- [ ] Mobile responsive
- [ ] API keys working
- [ ] Database operations work
- [ ] Images upload successfully

## 🌐 Custom Domain (Optional)

1. Go to service **Settings**
2. Click **"Custom Domain"**
3. Add your domain
4. Update DNS records as instructed
5. SSL certificate auto-generated

## 💰 Cost Estimate

### Free Tier
- **Cost**: $0/month
- **Limitations**: Spins down after inactivity
- **Good for**: Testing, demos, low-traffic apps

### Starter Plan ($7/month)
- **Cost**: $7/month
- **Benefits**: No spin-down, 512MB RAM
- **Good for**: Small production apps

### Standard Plan ($25/month)
- **Cost**: $25/month
- **Benefits**: 2GB RAM, better performance
- **Good for**: Production apps with traffic

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Community**: https://community.render.com
- **Status**: https://status.render.com

## 🎉 Success!

Once deployed, your app will be live at:
```
https://raitha-mitra.onrender.com
```

Share this URL with users to access your AI farming assistant!

---

**Need help?** Check the logs first, then refer to Render documentation or community forums.
