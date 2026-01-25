#!/bin/bash
# Cloudflare Tunnel Setup Script for FrankScore App
# This script helps set up Cloudflare Tunnel to expose your Render app

echo "🚀 Cloudflare Tunnel Setup for FrankScore App"
echo "=============================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared is not installed"
    echo ""
    echo "Please install cloudflared first:"
    echo "  Windows: Download from https://github.com/cloudflare/cloudflared/releases"
    echo "  Mac:     brew install cloudflared"
    echo "  Linux:   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    exit 1
fi

echo "✅ cloudflared is installed"
echo ""

# Step 1: Login
echo "Step 1: Login to Cloudflare"
echo "A browser window will open for authentication..."
cloudflared tunnel login

if [ $? -ne 0 ]; then
    echo "❌ Login failed"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Create tunnel
echo "Step 2: Creating tunnel..."
TUNNEL_NAME="frank-score-tunnel"
cloudflared tunnel create $TUNNEL_NAME

if [ $? -ne 0 ]; then
    echo "❌ Tunnel creation failed"
    exit 1
fi

echo "✅ Tunnel created: $TUNNEL_NAME"
echo ""

# Step 3: Get tunnel ID
echo "Step 3: Getting tunnel information..."
TUNNEL_LIST=$(cloudflared tunnel list)
TUNNEL_ID=$(echo "$TUNNEL_LIST" | grep "$TUNNEL_NAME" | awk '{print $1}')

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Could not find tunnel ID"
    exit 1
fi

echo "✅ Tunnel ID: $TUNNEL_ID"
echo ""

# Step 4: Create config file
echo "Step 4: Creating config file..."
CONFIG_FILE="cloudflare-tunnel-config.yml"

cat > $CONFIG_FILE << EOF
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/$TUNNEL_ID.json

ingress:
  # Route to your Render app
  - hostname: frank-score.yourdomain.com
    service: https://frank-score-app.onrender.com
  
  # Catch-all rule (must be last)
  - service: http_status:404
EOF

echo "✅ Config file created: $CONFIG_FILE"
echo ""
echo "⚠️  IMPORTANT: Edit $CONFIG_FILE and replace:"
echo "   - 'frank-score.yourdomain.com' with your actual domain"
echo "   - Update credentials-file path if needed"
echo ""

# Step 5: Instructions
echo "=============================================="
echo "Next Steps:"
echo "=============================================="
echo ""
echo "1. Edit $CONFIG_FILE with your domain"
echo ""
echo "2. Configure DNS in Cloudflare Dashboard:"
echo "   - Go to: https://dash.cloudflare.com"
echo "   - Select your domain"
echo "   - DNS → Records → Add CNAME:"
echo "     Name: frank-score (or @ for root)"
echo "     Target: $TUNNEL_ID.cfargotunnel.com"
echo "     Proxy: ✅ Proxied (orange cloud)"
echo ""
echo "3. Run the tunnel:"
echo "   cloudflared tunnel --config $CONFIG_FILE run $TUNNEL_NAME"
echo ""
echo "4. For production (run as service):"
echo "   - Windows: cloudflared service install"
echo "   - Linux:   Create systemd service"
echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo "=============================================="

