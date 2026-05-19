# 🚀 DEPLOY IN 5 MINUTES - RENDER (FREE)

## Step-by-Step Instructions:

### 1. Open Render
Go to: **https://render.com**

### 2. Sign Up
- Click "Get Started for Free"
- Choose "Sign up with GitHub"
- Authorize Render to access your GitHub

### 3. Create Web Service
- Click "New +" button (top right)
- Select "Web Service"

### 4. Connect Repository
- Find and select: **department_chatbot**
- Click "Connect"

### 5. Configure Service
Fill in these EXACT values:

**Name**: `nbkr-chatbot`

**Region**: Choose closest to you (e.g., Singapore, Frankfurt)

**Branch**: `master`

**Root Directory**: (leave empty)

**Runtime**: `Python 3`

**Build Command**:
```
pip install -r requirements.txt && python -m spacy download en_core_web_sm
```

**Start Command**:
```
uvicorn rag_chatbot:app --host 0.0.0.0 --port $PORT
```

**Instance Type**: `Free`

### 6. Deploy
- Click "Create Web Service" button at bottom
- Wait 5-10 minutes (watch the logs)

### 7. Get Your URL
Once deployed, you'll see:
```
Your service is live at https://nbkr-chatbot.onrender.com
```

### 8. Test Your Chatbot
- Click the URL
- Chat interface should load
- Try: "show timetable", "list faculty", "circulars"

---

## ✅ Success Checklist

- [ ] Signed up on Render
- [ ] Connected GitHub repository
- [ ] Configured build & start commands
- [ ] Deployment started (logs showing)
- [ ] Service is live (green status)
- [ ] Chatbot responds to queries
- [ ] URL copied for submission

---

## 🎯 Your Live URL

After deployment, your chatbot will be at:
```
https://nbkr-chatbot.onrender.com
```

**Use this URL in your project submission!**

---

## 📱 Share This URL

You can share this URL with:
- Your professor
- Project evaluators
- Classmates
- Anyone with internet access

The chatbot is publicly accessible 24/7!

---

## ⚠️ Important Notes

1. **First Load**: May take 30 seconds if service was sleeping
2. **Auto-Deploy**: Any git push will auto-redeploy
3. **Logs**: Check Render dashboard for errors
4. **Free Tier**: Service sleeps after 15 min inactivity
5. **Upgrade**: Can upgrade to paid tier ($7/month) for no sleep

---

## 🔧 If Deployment Fails

**Check Build Logs** in Render dashboard:

**Common Issue 1**: spaCy model download fails
- **Fix**: Build command must include `python -m spacy download en_core_web_sm`

**Common Issue 2**: Port binding error
- **Fix**: Start command must use `--port $PORT` (not `--port 8000`)

**Common Issue 3**: Memory limit
- **Fix**: Free tier has 512MB RAM - should be enough for this project

---

## 🎓 For Your Report

**Deployment Platform**: Render (Cloud Platform)

**Live Demo**: https://nbkr-chatbot.onrender.com

**Deployment Type**: Continuous Deployment (auto-deploys from GitHub)

**Infrastructure**: 
- Python 3.10 runtime
- Uvicorn ASGI server
- WebSocket support
- HTTPS enabled
- Auto-scaling

**Availability**: 24/7 (with cold start on free tier)

---

## 🚨 DEPLOY NOW!

1. Open: https://render.com
2. Sign up with GitHub
3. New Web Service
4. Connect repo
5. Copy build & start commands from above
6. Click Deploy
7. Done! 🎉

**Time Required**: 5 minutes setup + 10 minutes deployment = **15 minutes total**
