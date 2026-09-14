#!/bin/bash
# ==============================================================================
# Automated Deployment Script for 4-Node SSH Cluster
# Handles remote hosts without rsync and frees local port 5000.
# ==============================================================================

NODES=(
    "2257:5001"
    "2258:5002"
    "2259:5003"
    "2260:5004"
)

echo "======================================================================"
echo "🚀 Deploying Mist Pond Detection Engine across 4 SSH Systems"
echo "======================================================================"

# 1. Kill any existing process on port 5000 so the load balancer can bind cleanly
fuser -k 5000/tcp >/dev/null 2>&1 || pkill -f "python3 web_app.py" >/dev/null 2>&1
sleep 1

# 2. Deploy to each remote SSH worker node
for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT WORKER_PORT <<< "$ITEM"
    echo ""
    echo "[+] Deploying to student@10.1.75.51 on SSH Port $SSH_PORT (Worker Port $WORKER_PORT)..."
    
    # Send code archive using tar over SSH (works without rsync and auto-creates directory)
    tar -cf - --exclude='*.log' --exclude='__pycache__' --exclude='.git' . | ssh -o StrictHostKeyChecking=no -p $SSH_PORT student@10.1.75.51 "mkdir -p ~/smart_pond_detection && cd ~/smart_pond_detection && tar -xf -"
    
    # Stop existing worker on that port and start fresh worker
    ssh -o StrictHostKeyChecking=no -p $SSH_PORT student@10.1.75.51 "fuser -k ${WORKER_PORT}/tcp 2>/dev/null; cd ~/smart_pond_detection && pip install flask numpy scipy shapely requests 2>/dev/null; PORT=$WORKER_PORT nohup python3 web_app.py > worker_$WORKER_PORT.log 2>&1 &"
    
    echo "[✔] Worker process started on http://10.1.75.51:$WORKER_PORT"
done

echo ""
echo "======================================================================"
echo "🚀 All 4 Worker Nodes Deployed!"
echo "Starting Central Load Balancer Gateway on Port 5000..."
echo "======================================================================"

python3 cluster_load_balancer.py
