"""
run_cluster.py
--------------
Multi-Core High-Concurrency Cluster Runner for Mist Pond Detection System.

Launches 4 parallel worker application instances on ports 5001, 5002, 5003, 5004
and runs a central Load Balancer Gateway on port 5000.

Author: Pankaj Kashyap
Usage: python3 run_cluster.py
"""

import os
import sys
import time
import subprocess
from cluster_load_balancer import app as load_balancer_app, WORKER_NODES

def main():
    print("======================================================================")
    print("🚀 Starting 4-Worker Multi-Core Cluster Engine")
    print("======================================================================")

    # 1. Update worker nodes to local worker ports
    WORKER_NODES[0]["url"] = "http://127.0.0.1:5001"
    WORKER_NODES[1]["url"] = "http://127.0.0.1:5002"
    WORKER_NODES[2]["url"] = "http://127.0.0.1:5003"
    WORKER_NODES[3]["url"] = "http://127.0.0.1:5004"

    # 2. Launch 4 worker instances in parallel
    worker_processes = []
    ports = [5001, 5002, 5003, 5004]

    for port in ports:
        env = os.environ.copy()
        env["PORT"] = str(port)
        cmd = [sys.executable, "web_app.py"]
        proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(os.path.abspath(__file__)))
        worker_processes.append(proc)
        print(f"[✔] Worker node started on http://127.0.0.1:{port} (PID: {proc.pid})")

    time.sleep(2)

    print("\n======================================================================")
    print("🚀 4 Worker Nodes Online!")
    print("Starting Central Load Balancer Gateway on http://localhost:5000...")
    print("======================================================================\n")

    try:
        load_balancer_app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nStopping cluster worker nodes...")
        for proc in worker_processes:
            proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
