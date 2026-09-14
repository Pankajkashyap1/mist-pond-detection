#!/bin/bash
# ==============================================================================
# 4-Node SSH Cluster Deployment Script for Mist Pond Detection System
# ==============================================================================

NODES=(
    "127.0.0.1:5001"
    "student@10.1.75.51"
    "student@10.1.75.53"
    "umesh@10.10.3.147"
)

echo "======================================================================"
echo "🚀 Deploying Mist Pond Detection Engine to 4 Cluster Systems"
echo "======================================================================"

# 1. Start Local Worker Node on Port 5001
echo "[+] Starting Local Worker Process on 127.0.0.1:5001..."
PORT=5001 nohup python3 web_app.py > worker_local.log 2>&1 &
echo "[✔] Local Worker Started."

# 2. Deploy to Remote Systems over SSH
for NODE in "${NODES[@]}"; do
    if [ "$NODE" != "127.0.0.1:5001" ]; then
        echo "[+] Syncing codebase & starting worker on $NODE..."
        rsync -avz --exclude '*.log' --exclude '__pycache__' ./ $NODE:~/smart_pond_detection/
        ssh $NODE "cd ~/smart_pond_detection && pip install flask numpy scipy shapely requests && PORT=5001 nohup python3 web_app.py > worker.log 2>&1 &"
    fi
done

# 3. Start Central Load Balancer on Port 5000
echo "[+] Starting Central Load Balancer on Port 5000..."
python3 cluster_load_balancer.py
