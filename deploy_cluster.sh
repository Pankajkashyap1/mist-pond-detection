#!/bin/bash
# ==============================================================================
# Automated Deployment & Tunneling Script for 4-Node Cluster
# Target SSH Hosts:
#   1. ssh -p 2257 student@10.1.75.51 -> Local Port 5001
#   2. ssh -p 2258 student@10.1.75.51 -> Local Port 5002
#   3. ssh -p 2259 student@10.1.75.51 -> Local Port 5003
#   4. ssh -p 2260 student@10.1.75.51 -> Local Port 5004
# ==============================================================================

NODES=(
    "2257:5001"
    "2258:5002"
    "2259:5003"
    "2260:5004"
)

BUNDLE="/tmp/smart_pond_bundle.tar.gz"

echo "======================================================================"
echo "🚀 Step 1: Packaging project code bundle..."
echo "======================================================================"
tar -czf $BUNDLE --exclude='*.log' --exclude='__pycache__' --exclude='.git' -C /home/pankaj/.gemini/antigravity/scratch/smart_pond_detection .
echo "[✔] Bundle created at $BUNDLE"

# Clear local port 5000 (Load Balancer gateway port)
fuser -k 5000/tcp >/dev/null 2>&1 || pkill -f "python3 web_app.py" >/dev/null 2>&1 || true
sleep 1

echo ""
echo "======================================================================"
echo "🚀 Step 2: Deploying & Tunneling across 4 SSH Containers"
echo "======================================================================"

for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT LOCAL_PORT <<< "$ITEM"
    echo ""
    echo "[+] Deploying to student@10.1.75.51 (SSH Port $SSH_PORT -> Local Port $LOCAL_PORT)..."
    
    # Clear local tunnel port
    fuser -k ${LOCAL_PORT}/tcp >/dev/null 2>&1 || true
    
    # 1. Transfer bundle to container
    scp -o StrictHostKeyChecking=no -P $SSH_PORT $BUNDLE student@10.1.75.51:~/smart_pond_bundle.tar.gz
    
    # 2. Extract bundle, install dependencies, and launch worker on remote port 5000
    ssh -o StrictHostKeyChecking=no -p $SSH_PORT student@10.1.75.51 "mkdir -p ~/smart_pond_detection && tar -xzf ~/smart_pond_bundle.tar.gz -C ~/smart_pond_detection/ && cd ~/smart_pond_detection && (pkill -9 -f 'python3 web_app.py' 2>/dev/null || true) && (pip install flask numpy requests 2>/dev/null || true) && PORT=5000 nohup python3 web_app.py > worker_5000.log 2>&1 &"
    
    sleep 1.5
    
    # 3. Establish SSH Port Forwarding Tunnel
    ssh -o StrictHostKeyChecking=no -f -N -L ${LOCAL_PORT}:127.0.0.1:5000 -p $SSH_PORT student@10.1.75.51
    
    echo "[✔] SSH Container Active on http://127.0.0.1:$LOCAL_PORT (SSH Port $SSH_PORT)"
done

echo ""
echo "======================================================================"
echo "🚀 Step 3: Starting Central 4-Node Load Balancer Gateway on Port 5000"
echo "======================================================================"

python3 cluster_load_balancer.py
