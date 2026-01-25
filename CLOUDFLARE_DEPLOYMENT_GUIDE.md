# Deploying FrankScore App with Cloudflare

## ⚠️ Important Note

**Cloudflare doesn't directly support Python/FastAPI applications** like Render does. However, there are several ways to use Cloudflare with your FastAPI app:

## 🎯 Best Options

### Option 1: Cloudflare Tunnel (Recommended) ✅

Expose your app (running on Render/elsewhere) through Cloudflare's network.

**Pros:**
- ✅ Free
- ✅ DDoS protection
- ✅ Fast global network
- ✅ SSL/TLS included
- ✅ Works with existing Render deployment

**Cons:**
- ⚠️ Still need to host app elsewhere (Render, Railway, etc.)

---

### Option 2: Cloudflare Workers with Python (Experimental)

Use Cloudflare Workers Python runtime (newer feature).

**Pros:**
- ✅ Fully serverless
- ✅ Global edge network
- ✅ Free tier available

**Cons:**
- ⚠️ Limited Python support
- ⚠️ May not support all FastAPI features
- ⚠️ ML models may not work (size limits)
- ⚠️ Experimental/limited

---

### Option 3: Hybrid Approach

Deploy FastAPI elsewhere, use Cloudflare as CDN/proxy.

**Pros:**
- ✅ Best of both worlds
- ✅ Fast static asset delivery
- ✅ DDoS protection
- ✅ Full FastAPI support

**Cons:**
- ⚠️ Need two services (hosting + Cloudflare)

---

## 🚀 Option 1: Cloudflare Tunnel (Step-by-Step)

This is the **easiest and most reliable** option. It exposes your Render app through Cloudflare.

### Step 1: Keep Your App on Render

Your app stays deployed on Render as-is:
- `https://frank-score-app.onrender.com`

### Step 2: Install Cloudflared

**On Windows:**
```powershell
# Download from: https://github.com/cloudflare/cloudflared/releases
# Or use Chocolatey:
choco install cloudflared
```

**On Mac:**
```bash
brew install cloudflared
```

**On Linux:**
```bash
# Download binary
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

### Step 3: Login to Cloudflare

```bash
cloudflared tunnel login
```

This opens a browser window. Login with your Cloudflare account.

### Step 4: Create a Tunnel

```bash
cloudflared tunnel create frank-score-tunnel
```

This creates a tunnel and saves credentials.

### Step 5: Create Config File

Create `config.yml` in your project:

```yaml
tunnel: <tunnel-id-from-step-4>
credentials-file: C:\Users\dawit\.cloudflared\<tunnel-id>.json

ingress:
  # Route all traffic to your Render app
  - hostname: frank-score.yourdomain.com
    service: https://frank-score-app.onrender.com
  
  # Catch-all rule (must be last)
  - service: http_status:404
```

**Replace:**
- `<tunnel-id>` with the ID from step 4
- `frank-score.yourdomain.com` with your domain
- Path to credentials file

### Step 6: Run Tunnel

**For testing (temporary):**
```bash
cloudflared tunnel --config config.yml run frank-score-tunnel
```

**For production (as service):**

**Windows (as service):**
```powershell
# Install as Windows service
cloudflared service install
cloudflared service start
```

**Linux (systemd):**
```bash
# Create service file
sudo nano /etc/systemd/system/cloudflared.service
```

```ini
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /path/to/config.yml run frank-score-tunnel
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### Step 7: Configure DNS

1. Go to Cloudflare Dashboard
2. Select your domain
3. Go to DNS → Records
4. Add CNAME record:
   - **Name:** `frank-score` (or `@` for root domain)
   - **Target:** `<tunnel-id>.cfargotunnel.com`
   - **Proxy:** ✅ Proxied (orange cloud)

### Step 8: Access Your App

Your app is now available at:
- `https://frank-score.yourdomain.com`

All traffic goes through Cloudflare's network!

---

## 🔧 Option 2: Cloudflare Workers with Python

**Note:** This is experimental and may have limitations.

### Step 1: Install Wrangler CLI

```bash
npm install -g wrangler
```

### Step 2: Login to Cloudflare

```bash
wrangler login
```

### Step 3: Create Worker Project

```bash
mkdir cloudflare-worker
cd cloudflare-worker
wrangler init
```

### Step 4: Configure for Python

Create `wrangler.toml`:

```toml
name = "frank-score-worker"
main = "worker.py"
compatibility_date = "2024-01-01"

[env.production]
routes = [
  { pattern = "frank-score.yourdomain.com/*", zone_name = "yourdomain.com" }
]
```

### Step 5: Create Worker Script

Create `worker.py`:

```python
from js import Response, Request

async def on_fetch(request):
    # Proxy to your Render app
    render_url = "https://frank-score-app.onrender.com"
    
    # Forward request
    response = await fetch(render_url + request.url.path)
    return response

# Export handler
export = {"fetch": on_fetch}
```

**Limitations:**
- ⚠️ Python support is limited
- ⚠️ Can't run full FastAPI app
- ⚠️ ML models won't work (size limits)
- ⚠️ Better as a proxy than full app

---

## 🌐 Option 3: Hybrid Approach (Best Performance)

Deploy FastAPI on a Python-friendly platform, use Cloudflare as CDN.

### Step 1: Deploy FastAPI App

Choose a platform:
- **Railway** (recommended)
- **Fly.io**
- **DigitalOcean App Platform**
- **Heroku**
- **Keep Render** (current)

### Step 2: Add Domain to Cloudflare

1. Add your domain to Cloudflare
2. Update nameservers at your registrar

### Step 3: Configure DNS

In Cloudflare Dashboard → DNS:

**For API endpoints:**
- **Type:** CNAME
- **Name:** `api` (or `app`)
- **Target:** `frank-score-app.onrender.com`
- **Proxy:** ✅ Proxied

**For static assets (optional):**
- Use Cloudflare Pages for static files
- Or serve through FastAPI (current setup)

### Step 4: Configure Cloudflare Settings

**Speed → Optimization:**
- ✅ Auto Minify (JS, CSS, HTML)
- ✅ Brotli compression

**Caching:**
- Cache static assets (`/static/*`)
- Don't cache API endpoints (`/api/*`)

**Security:**
- ✅ SSL/TLS: Full (strict)
- ✅ Always Use HTTPS
- ✅ DDoS protection (automatic)

### Step 5: Page Rules (Optional)

Create rules:
1. **Static files:** Cache everything
   - URL: `yourdomain.com/static/*`
   - Cache Level: Cache Everything
   - Edge Cache TTL: 1 month

2. **API endpoints:** Don't cache
   - URL: `yourdomain.com/api/*`
   - Cache Level: Bypass

---

## 📋 Recommended Setup

### For Your Use Case:

**Best Option: Cloudflare Tunnel**

1. ✅ Keep app on Render (it's working!)
2. ✅ Set up Cloudflare Tunnel
3. ✅ Point your domain through Cloudflare
4. ✅ Get DDoS protection + faster delivery

**Why this works best:**
- No code changes needed
- Free
- Full FastAPI support
- ML models work
- Global CDN benefits

---

## 🔐 Security Configuration

### Cloudflare Settings:

**SSL/TLS:**
- Mode: **Full (strict)**
- Always Use HTTPS: **On**

**Firewall Rules:**
- Block known bad IPs
- Rate limiting (optional)

**WAF (Web Application Firewall):**
- Free tier includes basic WAF
- Protects against common attacks

---

## 📊 Performance Optimization

### Cloudflare Features:

1. **Auto Minify:**
   - Minifies JS, CSS, HTML
   - Reduces file sizes

2. **Brotli Compression:**
   - Better than gzip
   - Smaller file sizes

3. **Caching:**
   - Cache static assets
   - Reduce server load

4. **Argo Smart Routing:**
   - Paid feature
   - Faster routing

---

## 🛠️ Troubleshooting

### Issue: Tunnel not connecting

**Solution:**
- Check credentials file path
- Verify tunnel ID
- Check firewall/ports

### Issue: DNS not resolving

**Solution:**
- Wait 24-48 hours for DNS propagation
- Check CNAME record is correct
- Verify proxy is enabled (orange cloud)

### Issue: SSL errors

**Solution:**
- Set SSL/TLS mode to "Full (strict)"
- Ensure Render app has valid SSL

---

## 📝 Quick Start: Cloudflare Tunnel

**Fastest way to get started:**

```bash
# 1. Install cloudflared
# (Download from GitHub releases)

# 2. Login
cloudflared tunnel login

# 3. Create tunnel
cloudflared tunnel create frank-score

# 4. Run tunnel (temporary, for testing)
cloudflared tunnel --url https://frank-score-app.onrender.com

# This gives you a temporary URL like:
# https://xxxxx.trycloudflare.com
```

**For permanent setup:**
- Follow Step 5-7 above (config file + DNS)

---

## 🎯 Summary

**Recommended Path:**

1. ✅ **Keep your app on Render** (it's working well)
2. ✅ **Set up Cloudflare Tunnel** (free, easy)
3. ✅ **Point your domain through Cloudflare**
4. ✅ **Get all Cloudflare benefits** (DDoS, CDN, SSL)

**Alternative:**
- Deploy to Railway/Fly.io (better Python support)
- Use Cloudflare as CDN/proxy
- More control, but more setup

**Not Recommended:**
- Cloudflare Workers with Python (too limited for FastAPI + ML)

---

## 📚 Resources

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Workers Python](https://developers.cloudflare.com/workers/languages/python/)
- [Cloudflare DNS Setup](https://developers.cloudflare.com/dns/)

---

## 🚀 Next Steps

1. Choose your option (Tunnel recommended)
2. Set up Cloudflare account
3. Install cloudflared
4. Configure tunnel
5. Update DNS
6. Test your app!

Need help with a specific step? Let me know! 🎉

