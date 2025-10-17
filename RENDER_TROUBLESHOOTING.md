# Render Deployment Troubleshooting

## Current Issue: "Failed to get analysis from the server"

This error means the Flask backend isn't responding properly. Here's how to fix it:

## ✅ Fixes Applied (Latest Commit)

1. **Added Health Check Endpoint** (`/health`)
   - Render can now monitor if the app is running
   - Returns status of model, database, and Gemini AI

2. **Created Build Script** (`build.sh`)
   - Ensures Git LFS files are downloaded
   - Verifies model file size
   - Checks all required files exist

3. **Updated render.yaml**
   - Uses build script instead of pip install
   - Added health check path
   - Added proper logging
   - Increased timeout to 120s

4. **Improved Error Handling**
   - Better error messages
   - Graceful fallbacks

## 🚀 Deploy Steps

### 1. Go to Render Dashboard
https://dashboard.render.com

### 2. Manual Deploy
- Click on your service "raitha-mitra"
- Click **"Manual Deploy"** button
- Select **"Deploy latest commit"** (commit: 14a3041)
- Wait for deployment

### 3. Set Environment Variables

**CRITICAL**: Make sure these are set before deploying:

```bash
# Generate a secret key first:
python -c "import secrets; print(secrets.token_hex(32))"
```

Then add in Render Environment Variables:

| Variable | Value | Required |
|----------|-------|----------|
| `FLASK_SECRET_KEY` | (generated above) | ✅ YES |
| `GEMINI_API_KEY` | `AIzaSyBnzoJxxBG4YsrKV-BietpSCRnVI4Hv-Fc` | ✅ YES |
| `WEATHERAPI_KEY` | `6e4d2aff28174cc1820191846251510` | ✅ YES |
| `FLASK_DEBUG` | `False` | ✅ YES |
| `HOST` | `0.0.0.0` | ✅ YES |
| `PYTHON_VERSION` | `3.11.0` | Optional |

### 4. Check Build Logs

Look for these success indicators:

```
✅ Model file exists and has correct size
✅ Build complete!
✅ Installing gunicorn
✅ Successfully installed gunicorn-21.2.0
✅ Build successful
```

### 5. Check Deploy Logs

Look for these success indicators:

```
✅ Gemini AI models configured successfully
✅ Local disease detection model loaded
✅ Weather API configured successfully
[INFO] Booting worker with pid: XXXX
[INFO] Listening at: http://0.0.0.0:10000
```

## 🔍 Common Issues & Solutions

### Issue 1: Model File Not Loading

**Symptoms**: "Model file not found" in logs

**Solution**:
```bash
# In your local terminal:
git lfs pull
git add crop_disease_detection_model.h5
git commit -m "Ensure model file is tracked by LFS"
git push origin main
```

Then redeploy on Render.

### Issue 2: Gunicorn Not Found

**Symptoms**: "bash: gunicorn: command not found"

**Solution**: Already fixed in latest commit. Just redeploy.

### Issue 3: Port Binding Error

**Symptoms**: "No open ports detected"

**Solution**: Already fixed with `--bind 0.0.0.0:$PORT` in Procfile and render.yaml.

### Issue 4: Environment Variables Missing

**Symptoms**: App crashes immediately, "KeyError" in logs

**Solution**: Set all required environment variables (see step 3 above).

### Issue 5: Database Errors

**Symptoms**: "OperationalError: unable to open database"

**Solution**: Database file is included in repo. If still failing:
1. Check if `raitha_mitra.db` exists in repo
2. Verify file permissions
3. Check Render logs for specific error

### Issue 6: Git LFS Files Not Downloaded

**Symptoms**: Model file is very small (< 1MB)

**Solution**: Build script now handles this automatically. Redeploy.

## 📊 Verify Deployment

### Test Health Endpoint

Once deployed, visit:
```
https://raitha-mitra-85ej.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database": "connected",
  "gemini_configured": true
}
```

### Test Home Page

Visit:
```
https://raitha-mitra-85ej.onrender.com/
```

Should load the home page without errors.

### Test Disease Detection

1. Login with demo credentials:
   - Email: `demo@raithamitra.com`
   - Password: `123456`

2. Go to Disease Detection
3. Upload a crop image
4. Should get prediction results

## 🐛 Debug Mode

If still having issues, temporarily enable debug mode:

1. In Render, set `FLASK_DEBUG` = `True`
2. Redeploy
3. Check logs for detailed error messages
4. **IMPORTANT**: Set back to `False` after debugging

## 📞 Get Detailed Logs

### View Live Logs
1. Go to Render dashboard
2. Click on your service
3. Click "Logs" tab
4. Watch real-time logs during deployment

### Download Logs
1. In Logs tab
2. Click "Download" button
3. Share logs if you need help

## 🔄 If All Else Fails

### Nuclear Option: Redeploy from Scratch

1. **Delete Service** on Render
2. **Create New Service**
3. **Connect GitHub repo**
4. **Set all environment variables**
5. **Deploy**

### Alternative: Use Procfile Instead

If render.yaml isn't working, Render will use Procfile automatically:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

This is already in your repo.

## ✅ Success Checklist

- [ ] Latest commit deployed (14a3041 or later)
- [ ] All environment variables set
- [ ] Build logs show success
- [ ] Deploy logs show "Listening at: http://0.0.0.0:10000"
- [ ] Health endpoint returns "healthy"
- [ ] Home page loads
- [ ] Can login
- [ ] Disease detection works

## 📚 Additional Resources

- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Community**: https://community.render.com

## 🆘 Still Need Help?

If you're still stuck:

1. Check the health endpoint: `/health`
2. Download and review the logs
3. Verify all environment variables are set
4. Try clearing build cache and redeploying
5. Check Render status page for outages

---

**Last Updated**: After commit 14a3041
**Status**: Ready to deploy with fixes
