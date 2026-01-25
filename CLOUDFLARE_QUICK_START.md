# Cloudflare Quick Start Guide

## 🚀 Fastest Way to Get Started

### Option A: Quick Test (5 minutes)

Test Cloudflare Tunnel without a domain:

```bash
# 1. Install cloudflared (if not installed)
# Download from: https://github.com/cloudflare/cloudflared/releases

# 2. Run tunnel (temporary URL)
cloudflared tunnel --url https://frank-score-app.onrender.com
```

This gives you a temporary URL like:
```
https://xxxxx-xxxxx.trycloudflare.com
```

**Use this URL to test!** It expires when you close the terminal.

---

### Option B: Permanent Setup (15 minutes)

#### Step 1: Install Cloudflared

**Windows:**
1. Download from: https://github.com/cloudflare/cloudflared/releases/latest
2. Extract `cloudflared.exe`
3. Add to PATH or use full path

**Mac:**
```bash
brew install cloudflared
```

**Linux:**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

#### Step 2: Login

```bash
cloudflared tunnel login
```

Opens browser → Login with Cloudflare account → Authorize

#### Step 3: Create Tunnel

```bash
cloudflared tunnel create frank-score
```

Note the Tunnel ID that's displayed.

#### Step 4: Create Config File

Create `cloudflare-tunnel-config.yml`:

```yaml
tunnel: <YOUR_TUNNEL_ID>
credentials-file: C:\Users\dawit\.cloudflared\<TUNNEL_ID>.json

ingress:
  - hostname: frank-score.yourdomain.com
    service: https://frank-score-app.onrender.com
  - service: http_status:404
```

**Replace:**
- `<YOUR_TUNNEL_ID>` with tunnel ID from step 3
- `frank-score.yourdomain.com` with your domain
- Credentials file path (check `~/.cloudflared/` or `C:\Users\dawit\.cloudflared\`)

#### Step 5: Configure DNS

1. Go to: https://dash.cloudflare.com
2. Select your domain
3. Go to **DNS** → **Records**
4. Click **Add record**:
   - **Type:** CNAME
   - **Name:** `frank-score` (or `@` for root domain)
   - **Target:** `<TUNNEL_ID>.cfargotunnel.com`
   - **Proxy status:** ✅ Proxied (orange cloud)
5. Click **Save**

#### Step 6: Run Tunnel

**For testing:**
```bash
cloudflared tunnel --config cloudflare-tunnel-config.yml run frank-score
```

**For production (Windows service):**
```powershell
cloudflared service install
# Edit service config to use your config file
cloudflared service start
```

**For production (Linux systemd):**
```bash
# Create service file
sudo nano /etc/systemd/system/cloudflared.service
```

Paste:
```ini
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /path/to/cloudflare-tunnel-config.yml run frank-score
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

#### Step 7: Test

Visit: `https://frank-score.yourdomain.com`

Should work! 🎉

---

## 🔧 Troubleshooting

### "Tunnel not found"
- Check tunnel ID is correct
- Run `cloudflared tunnel list` to see all tunnels

### "Credentials file not found"
- Check path in config file
- Default location: `~/.cloudflared/<TUNNEL_ID>.json`

### "DNS not resolving"
- Wait 5-10 minutes for DNS propagation
- Check CNAME record is correct
- Ensure proxy is enabled (orange cloud)

### "SSL errors"
- Set SSL/TLS mode to "Full (strict)" in Cloudflare Dashboard
- Ensure Render app has valid SSL

---

## 📋 Checklist

- [ ] Cloudflared installed
- [ ] Logged in to Cloudflare
- [ ] Tunnel created
- [ ] Config file created and updated
- [ ] DNS record added
- [ ] Tunnel running
- [ ] App accessible via domain

---

## 🎯 What You Get

✅ **Free DDoS Protection**
✅ **Global CDN** (faster loading)
✅ **Free SSL/TLS**
✅ **Better Security**
✅ **Analytics** (in Cloudflare Dashboard)

---

## 📞 Need Help?

1. Check Cloudflare Tunnel logs: `cloudflared tunnel info frank-score`
2. Test connection: `cloudflared tunnel test frank-score`
3. View tunnel status: `cloudflared tunnel list`

---

## 🚀 Alternative: Use Script

I've created a setup script! Run:

```bash
chmod +x cloudflare-tunnel-setup.sh
./cloudflare-tunnel-setup.sh
```

This automates most of the setup process.

