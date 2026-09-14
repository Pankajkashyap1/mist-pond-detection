#!/bin/bash
# ==============================================================================
# 4-Node Cluster Deployment with SSH ControlMaster Sockets
# Minimizes password prompts by reusing a single SSH connection per container.
# ==============================================================================

NODES=(
    "2257:5001"
    "2258:5002"
    "2259:5003"
    "2260:5004"
)

mkdir -p ~/.ssh/sockets

echo "======================================================================"
echo "🚀 Deploying & Tunneling Mist Pond Engine across 4 SSH Systems"
echo "======================================================================"

# 1. Clear local port 5000 (Load Balancer port)
fuser -k 5000/tcp >/dev/null 2>&1 || pkill -f "python3 web_app.py" >/dev/null 2>&1
sleep 1

# 2. Deploy to each SSH worker node reusing multiplexed SSH socket
for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT LOCAL_PORT <<< "$ITEM"
    echo ""
    echo "[+] Connecting to student@10.1.75.51 on SSH Port $SSH_PORT..."
    
    # Common SSH options with socket reuse (only asks password ONCE per container)
    SSH_OPTS="-o StrictHostKeyChecking=no -o ControlMaster=auto -o ControlPath=~/.ssh/sockets/cm_%r@%h_%p -o ControlPersist=10m -p $SSH_PORT"
    
    # Kill any previous tunnel on this local port
    fuser -k ${LOCAL_PORT}/tcp >/dev/null 2>&1
    
    # Send code archive using single multiplexed SSH connection
    tar -cf - --exclude='*.log' --exclude='__pycache__' --exclude='.git' . | ssh $SSH_OPTS student@10.1.75.51 "mkdir -p ~/smart_pond_detection && cd ~/smart_pond_detection && tar -xf -"
    
    # Start worker on remote host using the same socket
    ssh $SSH_OPTS student@10.1.75.51 "fuser -k 5000/tcp 2>/dev/null; cd ~/smart_pond_detection && pip install flask numpy scipy shapely requests 2>/dev/null; PORT=5000 nohup python3 web_app.py > worker_5000.log 2>&1 &"
    
    # Establish SSH Tunnel using the same socket
    ssh -f -N $SSH_OPTS -L ${LOCAL_PORT}:127.0.0.1:5000 student@10.1.75.51
    
    echo "[✔] Tunnel established on http://127.0.0.1:$LOCAL_PORT (SSH Port $SSH_PORT)"
done

echo ""
echo "======================================================================"
echo "🚀 All 4 SSH Worker Nodes Connected!"
echo "Starting Central Load Balancer Gateway on Port 5000..."
echo "======================================================================"

python3 cluster_load_balancer.py
