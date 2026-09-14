#!/bin/bash
# ==============================================================================
# Bulletproof 4-Node Cluster Deployment & Tunneling Script
# Uses standalone tar.gz bundle + scp + disown to guarantee background persistence.
# ==============================================================================

NODES=(
    "2257:5001"
    "2258:5002"
    "2259:5003"
    "2260:5004"
)

BUNDLE="/tmp/smart_pond_bundle.tar.gz"

echo "======================================================================"
echo "🚀 Creating clean project bundle..."
echo "======================================================================"
tar -czf $BUNDLE --exclude='*.log' --exclude='__pycache__' --exclude='.git' -C /home/pankaj/.gemini/antigravity/scratch/smart_pond_detection .
echo "[✔] Bundle created at $BUNDLE"

echo ""
echo "======================================================================"
echo "🚀 Deploying & Tunneling Mist Pond Engine across 4 SSH Systems"
echo "======================================================================"

# 1. Clear local port 5000 (Load Balancer gateway port)
fuser -k 5000/tcp >/dev/null 2>&1 || pkill -f "python3 web_app.py" >/dev/null 2>&1
sleep 1

# 2. Deploy to each SSH worker node
for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT LOCAL_PORT <<< "$ITEM"
    echo ""
    echo "[+] Deploying to student@10.1.75.51 on SSH Port $SSH_PORT..."
    
    # Kill any previous tunnel on this local port
    fuser -k ${LOCAL_PORT}/tcp >/dev/null 2>&1
    
    # Step A: Copy bundle file via scp
    scp -o StrictHostKeyChecking=no -P $SSH_PORT $BUNDLE student@10.1.75.51:~/smart_pond_bundle.tar.gz
    
    # Step B: Unpack, kill old worker, and start fresh persistent worker process with disown
    ssh -o StrictHostKeyChecking=no -p $SSH_PORT student@10.1.75.51 "mkdir -p ~/smart_pond_detection && tar -xzf ~/smart_pond_bundle.tar.gz -C ~/smart_pond_detection/ && cd ~/smart_pond_detection && fuser -k 5000/tcp 2>/dev/null; PORT=5000 nohup python3 web_app.py > worker_5000.log 2>&1 & disown"
    
    sleep 1.5
    
    # Step C: Establish background SSH tunnel for local port
    ssh -o StrictHostKeyChecking=no -f -N -L ${LOCAL_PORT}:127.0.0.1:5000 -p $SSH_PORT student@10.1.75.51
    
    echo "[✔] Worker & Tunnel Active: http://127.0.0.1:$LOCAL_PORT -> SSH Port $SSH_PORT"
done

echo ""
echo "======================================================================"
echo "🚀 All 4 Worker Nodes & SSH Tunnels Connected!"
echo "Starting Central Load Balancer Gateway on Port 5000..."
echo "======================================================================"

python3 cluster_load_balancer.py
