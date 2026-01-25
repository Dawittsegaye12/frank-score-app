# Vercel Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

**Or** use the web interface at https://vercel.com

### Step 2: Login

```bash
vercel login
```

Opens browser → Login with GitHub/Email

### Step 3: Deploy

```bash
# From your project directory
vercel
```

**First time prompts:**
- Set up and deploy? → **Y**
- Which scope? → **Your account**
- Link to existing? → **N**
- Project name? → **frank-score-app**
- Directory? → **./**

### Step 4: Production Deploy

```bash
vercel --prod
```

**Done!** Your app is live at: `https://frank-score-app.vercel.app`

---

## 🌐 GitHub Integration (Recommended)

### Automatic Deployments

1. **Go to**: https://vercel.com/new
2. **Import** your GitHub repository
3. **Configure**:
   - Framework: **Other**
   - Root Directory: **./**
   - Build Command: (leave empty)
4. **Add Environment Variables** (if needed)
5. **Deploy**

**Result**: Every push to `main` auto-deploys! 🎉

---

## ⚙️ Environment Variables

Set in Vercel Dashboard → Settings → Environment Variables:

```
PYTHON_VERSION=3.10
RENDER_API_URL=https://frank-score-app.onrender.com
```

---

## 🧪 Test Your Deployment

```bash
# Health check
curl https://your-app.vercel.app/health

# Should return: {"ok": true, "db": "ok"}
```

---

## 📋 Checklist

- [ ] Vercel CLI installed
- [ ] Logged in
- [ ] Project deployed
- [ ] Environment variables set
- [ ] Health endpoint working
- [ ] API endpoints tested

---

## 🐛 Common Issues

### "Module not found"
→ Check `vercel-requirements.txt` has all packages

### "Function timeout"
→ Increase timeout in `vercel.json` or use external API

### "Package too large"
→ Remove large ML packages, use external API

---

## 🎯 Next Steps

1. ✅ Deploy to Vercel
2. ✅ Test endpoints
3. ✅ Set up custom domain (optional)
4. ✅ Configure auto-deployments from GitHub

**That's it!** Your app is on Vercel! 🚀
