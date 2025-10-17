# Quick Deploy to Render - 5 Minutes! ⚡

## Step 1: Push to GitHub (2 minutes)

```bash
# Create new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/raitha-mitra.git
git push -u origin main
```

## Step 2: Deploy on Render (3 minutes)

1. **Go to**: https://render.com
2. **Sign up** with GitHub
3. **Click**: "New +" → "Web Service"
4. **Select**: Your raitha-mitra repository
5. **Configure**:
   - Name: `raitha-mitra`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. **Add Environment Variables**:
   ```
   FLASK_SECRET_KEY = (generate with: python -c "import secrets; print(secrets.token_hex(32))")
   FLASK_DEBUG = False
   HOST = 0.0.0.0
   GEMINI_API_KEY = your-gemini-api-key
   WEATHERAPI_KEY = your-weather-api-key
   ```
7. **Click**: "Create Web Service"

## Step 3: Wait & Access! ✅

- Wait 5-10 minutes for deployment
- Access at: `https://raitha-mitra.onrender.com`
- Login with demo credentials:
  - Email: `demo@raithamitra.com`
  - Password: `123456`

## 🎉 Done!

Your AI farming assistant is now live!

---

**Need detailed instructions?** See `RENDER_DEPLOYMENT_GUIDE.md`
