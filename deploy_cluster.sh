#!/bin/bash
# ==============================================================================
# Single-Connection 4-Node Cluster Deployment Script
# Merges file extraction, worker startup, and SSH tunneling into ONE single SSH call
# per container (Exactly 1 password prompt per container!).
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

# 1. Clear local port 5000 (Load Balancer gateway port)
fuser -k 5000/tcp >/dev/null 2>&1 || pkill -f "python3 web_app.py" >/dev/null 2>&1
sleep 1

# 2. Single-shot SSH command per container
for ITEM in "${NODES[@]}"; do
    IFS=":" read -r SSH_PORT LOCAL_PORT <<< "$ITEM"
    echo ""
    echo "[+] Connecting to student@10.1.75.51 on SSH Port $SSH_PORT..."
    
    # Kill any previous tunnel on this local port
    fuser -k ${LOCAL_PORT}/tcp >/dev/null 2>&1
    
    # ONE SINGLE SSH COMMAND: Copies code, starts worker, & sets up tunnel in 1 step!
    tar -cf - --exclude='*.log' --exclude='__pycache__' --exclude='.git' . | ssh -o StrictHostKeyChecking=no -f -N -L ${LOCAL_PORT}:127.0.0.1:5000 -p $SSH_PORT student@10.1.75.51 "mkdir -p ~/smart_pond_detection && cd ~/smart_pond_detection && tar -xf - && fuser -k 5000/tcp 2>/dev/null; PORT=5000 nohup python3 web_app.py > worker_5000.log 2>&1 &"
    
    echo "[✔] Worker & Tunnel Active: http://127.0.0.1:$LOCAL_PORT -> SSH Port $SSH_PORT"
done

echo ""
echo "======================================================================"
echo "🚀 All 4 Worker Nodes & SSH Tunnels Connected!"
echo "Starting Central Load Balancer Gateway on Port 5000..."
echo "======================================================================"

python3 cluster_load_balancer.py
