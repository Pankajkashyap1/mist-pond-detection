"""
deploy_ssh_cluster.py
---------------------
Automated Multi-Node SSH Deployment & Load Balancer for Mist Pond Detection System.
Uses Paramiko for SSH authentication, SFTP file transfer, remote health checks,
and reliable SSH port forwarding tunnels.

Author: Pankaj Kashyap
Usage: python3 deploy_ssh_cluster.py
"""

import os
import sys
import time
import tarfile
import getpass
import paramiko
import threading
from subprocess import Popen

SSH_HOST = "10.1.75.51"
SSH_USER = "student"
CONTAINERS = [
    {"ssh_port": 2257, "local_port": 5001, "name": "Container 1 (SSH 2257)"},
    {"ssh_port": 2258, "local_port": 5002, "name": "Container 2 (SSH 2258)"},
    {"ssh_port": 2259, "local_port": 5003, "name": "Container 3 (SSH 2259)"},
    {"ssh_port": 2260, "local_port": 5004, "name": "Container 4 (SSH 2260)"},
]

BUNDLE_PATH = "/tmp/smart_pond_bundle.tar.gz"

def create_bundle():
    """Creates a clean tar.gz bundle of the project directory."""
    print("📦 Creating project archive bundle...")
    project_dir = os.path.dirname(os.path.abspath(__file__))
    with tarfile.open(BUNDLE_PATH, "w:gz") as tar:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
            for file in files:
                if not file.endswith(".log") and not file.endswith(".tar.gz"):
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, project_dir)
                    tar.add(full_path, arcname=arcname)
    print(f"✔ Archive created at {BUNDLE_PATH}")

def deploy_to_container(container, password):
    ssh_port = container["ssh_port"]
    local_port = container["local_port"]
    name = container["name"]
    
    print(f"\n[+] Connecting to {name} on {SSH_HOST}:{ssh_port}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SSH_HOST, port=ssh_port, username=SSH_USER, password=password, timeout=10)
    except Exception as e:
        print(f"❌ SSH Connection failed to {name}: {e}")
        return False

    # 1. SFTP Upload Bundle
    try:
        sftp = client.open_sftp()
        remote_bundle = "/tmp/smart_pond_bundle.tar.gz"
        sftp.put(BUNDLE_PATH, remote_bundle)
        sftp.close()
        print(f"  └─ Uploaded project bundle to {name}")
    except Exception as e:
        print(f"❌ SFTP Upload failed to {name}: {e}")
        client.close()
        return False

    # 2. Extract bundle & kill old worker
    commands = [
        "mkdir -p ~/smart_pond_detection",
        "tar -xzf /tmp/smart_pond_bundle.tar.gz -C ~/smart_pond_detection/",
        "pkill -9 -f 'python3 web_app.py' 2>/dev/null || true",
        "cd ~/smart_pond_detection && (python3 -m pip install --user flask numpy requests 2>/dev/null || true)",
        "cd ~/smart_pond_detection && PORT=5000 nohup python3 web_app.py > worker.log 2>&1 &"
    ]
    
    full_cmd = " && ".join(commands)
    stdin, stdout, stderr = client.exec_command(full_cmd)
    stdout.channel.recv_exit_status()
    
    time.sleep(2)
    
    # 3. Verify worker is running on remote port 5000
    stdin, stdout, stderr = client.exec_command("curl -s http://127.0.0.1:5000/ || ps aux | grep python3")
    output = stdout.read().decode("utf-8", errors="ignore")
    print(f"  └─ Remote worker verification output: {output[:100].strip()}")
    
    client.close()
    
    # 4. Establish SSH Tunnel via background ssh command
    tunnel_cmd = f"fuser -k {local_port}/tcp 2>/dev/null || true; sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -f -N -L {local_port}:127.0.0.1:5000 -p {ssh_port} {SSH_USER}@{SSH_HOST} 2>/dev/null || ssh -o StrictHostKeyChecking=no -f -N -L {local_port}:127.0.0.1:5000 -p {ssh_port} {SSH_USER}@{SSH_HOST}"
    os.system(tunnel_cmd)
    
    print(f"✔ Container {name} active on local port http://127.0.0.1:{local_port}")
    return True

def main():
    print("======================================================================")
    print("🚀 Paramiko SSH Cluster Deployer & Load Balancer")
    print("======================================================================")
    
    password = getpass.getpass(prompt="Enter SSH password for student@10.1.75.51: ")
    
    create_bundle()
    
    success_count = 0
    for container in CONTAINERS:
        if deploy_to_container(container, password):
            success_count += 1
            
    print(f"\n======================================================================")
    print(f"🚀 {success_count}/{len(CONTAINERS)} SSH Containers Deployed & Connected!")
    print("Starting Central Load Balancer Gateway on http://localhost:5000...")
    print("======================================================================\n")
    
    # Start Load Balancer
    from cluster_load_balancer import app as load_balancer_app
    load_balancer_app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()
