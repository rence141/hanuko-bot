# 🚀 Render Deployment Guide (Recommended for Filipino Devs)

## Why Render?
- ✅ **750 hours/month free** (more than Railway!)
- ✅ **No credit card required**
- ✅ **Easy GitHub integration**
- ✅ **Good performance**
- ✅ **Auto-deploy on push**

## 📋 Prerequisites
1. **GitHub account** with your bot repository
2. **Discord bot token** ready
3. **5 minutes** of setup time

## 🚀 Step-by-Step Deployment

### **Step 1: Create Render Account**
1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with your **GitHub account**
4. Verify your email

### **Step 2: Deploy Your Bot**
1. **Click "New +"** in your Render dashboard
2. **Select "Web Service"**
3. **Connect your GitHub repository**
   - Click "Connect a repository"
   - Select your bot repository
   - Click "Connect"

### **Step 3: Configure Your Service**
Fill in these settings:

**Basic Settings:**
- **Name**: `hanuko-discord-bot` 
- **Environment**: `Python 3`
- **Region**: `Singapore` 
- **Branch**: `main` 
- **Root Directory**: (empty)

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python hanuko_bot.py`

**Plan:**
- **Free** (750 hours/month)

### **Step 4: Add Environment Variables**
1. **Click "Environment"** tab
2. **Add these variables:**

```
DISCORD_BOT_TOKEN = your_actual_bot_token_here
PORT = 8080
```

**Important:** Replace `your_actual_bot_token_here` with your real Discord bot token!

### **Step 5: Deploy**
1. **Click "Create Web Service"**
2. **Wait for build** (2-5 minutes)
3. **Check logs** for any errors

## 🌐 Keep Your Bot Awake (Free)

### **Option 1: UptimeRobot (Recommended)**
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. **Create free account**
3. **Add new monitor:**
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://your-app-name.onrender.com/ping`
   - **Check Interval**: 5 minutes
   - **Alert When Down**: Yes

### **Option 2: Cron-job.org**
1. Go to [cron-job.org](https://cron-job.org)
2. **Create free account**
3. **Add new cronjob:**
   - **URL**: `https://your-app-name.onrender.com/ping`
   - **Schedule**: Every 10 minutes

## 📊 Monitor Your Bot

### **Render Dashboard:**
- **Logs**: Check for errors
- **Metrics**: Monitor performance
- **Deployments**: See build status

### **Bot Status Endpoints:**
- **Ping**: `https://your-app-name.onrender.com/ping`
- **Status**: `https://your-app-name.onrender.com/status`

## ⏰ Render Free Tier Limits

### **What You Get:**
- **750 hours/month** (31 days = 744 hours)
- **Sleeps after 15 minutes** of inactivity
- **Auto-wake** when pinged
- **No data loss** when sleeping

### **Monthly Usage:**
- **Full month (31 days)**: 744 hours
- **Render limit**: 750 hours
- **Result**: ✅ **True 24/7 operation possible!**

## 🆘 Troubleshooting

### **Build Fails:**
- Check `requirements.txt` is correct
- Verify Python version compatibility
- Check build logs for errors

### **Bot Won't Start:**
- Verify `DISCORD_BOT_TOKEN` is set correctly
- Check start command is correct
- Look at runtime logs

### **Bot Goes Offline:**
- Set up UptimeRobot ping service
- Check if Render service is running
- Verify environment variables

### **High Latency:**
- Choose Singapore region
- Check your internet connection
- Monitor Render performance

## 💰 Cost Breakdown

### **Free Tier:**
- **Monthly cost**: ₱0
- **Hours**: 750/month
- **Uptime**: ~24/7 (with ping service)
- **Perfect for**: Students, beginners, small projects

### **Paid Tier (if needed):**
- **Starter**: $7/month (₱390)
- **Professional**: $25/month (₱1,400)
- **Only needed for**: High-traffic bots, multiple projects

## 🎯 Filipino Developer Tips

### **Best Practices:**
1. **Use Singapore region** for lowest latency
2. **Set up UptimeRobot** immediately after deployment
3. **Monitor logs** regularly
4. **Backup your data** (JSON files)
5. **Test commands** after deployment

### **Common Issues:**
- **PLDT/Globe connection issues** - Use mobile data for testing
- **Token security** - Never share your bot token
- **Environment variables** - Double-check spelling

## ✅ Success Checklist

- [ ] Render account created
- [ ] GitHub repository connected
- [ ] Web service created
- [ ] Environment variables set
- [ ] Bot deployed successfully
- [ ] UptimeRobot ping service set up
- [ ] Bot responds to commands
- [ ] Logs show no errors

## 🎉 You're Done!

Your bot should now be running 24/7 on Render! 

**Your bot URL**: `https://your-app-name.onrender.com`
**Ping URL**: `https://your-app-name.onrender.com/ping`

**Total cost**: ₱0 (completely free!)

---

*Need help? Check the troubleshooting section or ask in Filipino developer communities! 🇵🇭* 