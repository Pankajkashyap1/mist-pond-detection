#!/bin/bash
# ==============================================================================
# Automated Deployment Script for 4-Node SSH Cluster
# Nodes:
#   1. ssh -p 2257 student@10.1.75.51 (Port 5001)
#   2. ssh -p 2258 student@10.1.75.51 (Port 5002)
#   3. ssh -p 2259 student@10.1.75.51 (Port 5003)
#   4. ssh -p 2260 student@10.1.75.51 (Port 5004)
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

for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT WORKER_PORT <<< "$ITEM"
    echo ""
    echo "[+] Deploying to student@10.1.75.51 on SSH Port $SSH_PORT (Worker Port $WORKER_PORT)..."
    
    # Sync code directory over rsync using specific SSH port
    rsync -avz -e "ssh -p $SSH_PORT" --exclude '*.log' --exclude '__pycache__' --exclude '.git' ./ student@10.1.75.51:~/smart_pond_detection/
    
    # Install dependencies & start Flask worker on remote port
    ssh -p $SSH_PORT student@10.1.75.51 "cd ~/smart_pond_detection && pip install flask numpy scipy shapely requests && PORT=$WORKER_PORT nohup python3 web_app.py > worker_$WORKER_PORT.log 2>&1 &"
    
    echo "[✔] Worker on SSH Port $SSH_PORT started on http://10.1.75.51:$WORKER_PORT"
done

echo ""
echo "======================================================================"
echo "🚀 All 4 Worker Nodes Deployed!"
echo "Starting Central Load Balancer Gateway on Port 5000..."
echo "======================================================================"

python3 cluster_load_balancer.py
