#!/bin/bash
# ==============================================================================
# Automated Deployment & SSH Tunneling Script for 4-Node Cluster
# Nodes:
#   1. SSH Port 2257 -> Tunnel to Local Port 5001
#   2. SSH Port 2258 -> Tunnel to Local Port 5002
#   3. SSH Port 2259 -> Tunnel to Local Port 5003
#   4. SSH Port 2260 -> Tunnel to Local Port 5004
# ==============================================================================

NODES=(
    "2257:5001"
    "2258:5002"
    "2259:5003"
    "2260:5004"
)

echo "======================================================================"
echo "🚀 Deploying & Tunneling Mist Pond Engine across 4 SSH Systems"
echo "======================================================================"

# 1. Kill any existing process on local port 5000 (Load Balancer port)
fuser -k 5000/tcp >/dev/null 2>&1 || pkill -f "python3 web_app.py" >/dev/null 2>&1
sleep 1

# 2. Deploy to each SSH worker node & establish SSH tunnels
for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT LOCAL_PORT <<< "$ITEM"
    echo ""
    echo "[+] Deploying to student@10.1.75.51 on SSH Port $SSH_PORT..."
    
    # Kill any previous tunnel on this local port
    fuser -k ${LOCAL_PORT}/tcp >/dev/null 2>&1
    
    # Send code archive using tar over SSH
    tar -cf - --exclude='*.log' --exclude='__pycache__' --exclude='.git' . | ssh -o StrictHostKeyChecking=no -p $SSH_PORT student@10.1.75.51 "mkdir -p ~/smart_pond_detection && cd ~/smart_pond_detection && tar -xf -"
    
    # Start worker on port 5000 inside the remote node
    ssh -o StrictHostKeyChecking=no -p $SSH_PORT student@10.1.75.51 "fuser -k 5000/tcp 2>/dev/null; cd ~/smart_pond_detection && pip install flask numpy scipy shapely requests 2>/dev/null; PORT=5000 nohup python3 web_app.py > worker_5000.log 2>&1 &"
    
    # Establish SSH Tunnel from local port to remote worker port 5000
    ssh -f -N -o StrictHostKeyChecking=no -L ${LOCAL_PORT}:127.0.0.1:5000 -p $SSH_PORT student@10.1.75.51
    
    echo "[✔] SSH Tunnel Active: http://127.0.0.1:$LOCAL_PORT -> System (SSH Port $SSH_PORT)"
done

echo ""
echo "======================================================================"
echo "🚀 All 4 SSH Tunnels & Worker Nodes Connected!"
echo "Starting Central Load Balancer Gateway on Port 5000..."
echo "======================================================================"

python3 cluster_load_balancer.py
