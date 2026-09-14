"""
deploy_ssh_cluster.py
---------------------
Automated Multi-Node SSH Deployment & Native Paramiko Load Balancer Gateway.
Assigns UNIQUE ports (5001, 5002, 5003, 5004) to each container node to eliminate port conflicts.

Author: Pankaj Kashyap
Usage: python3 deploy_ssh_cluster.py
"""

import os
import sys
import time
import socket
import select
import tarfile
import getpass
import paramiko
import threading

SSH_HOST = "10.1.75.51"
SSH_USER = "student"
CONTAINERS = [
    {"ssh_port": 2257, "worker_port": 5001, "name": "Container 1 (SSH 2257)"},
    {"ssh_port": 2258, "worker_port": 5002, "name": "Container 2 (SSH 2258)"},
    {"ssh_port": 2259, "worker_port": 5003, "name": "Container 3 (SSH 2259)"},
    {"ssh_port": 2260, "worker_port": 5004, "name": "Container 4 (SSH 2260)"},
]

BUNDLE_PATH = "/tmp/smart_pond_bundle.tar.gz"
CLIENTS = []


def create_bundle():
    """Creates a clean tar.gz bundle of the project directory."""
    print("📦 Packaging project archive bundle...")
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


def start_native_paramiko_tunnel(local_port, remote_host, remote_port, transport):
    """Establishes a native Paramiko local port forwarding server in a background thread."""
    def handler(client_sock):
        try:
            chan = transport.open_channel("direct-tcpip", (remote_host, remote_port), client_sock.getpeername())
        except Exception:
            client_sock.close()
            return

        while True:
            r, _, _ = select.select([client_sock, chan], [], [], 1.0)
            if client_sock in r:
                data = client_sock.recv(4096)
                if not data:
                    break
                chan.sendall(data)
            if chan in r:
                data = chan.recv(4096)
                if not data:
                    break
                client_sock.sendall(data)
        chan.close()
        client_sock.close()

    def listen_loop():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", local_port))
            sock.listen(100)
            while True:
                client_sock, _ = sock.accept()
                t = threading.Thread(target=handler, args=(client_sock,), daemon=True)
                t.start()
        except Exception as e:
            print(f"⚠️ Port forward error on port {local_port}: {e}")

    t = threading.Thread(target=listen_loop, daemon=True)
    t.start()


def deploy_to_container(container, password):
    ssh_port = container["ssh_port"]
    worker_port = container["worker_port"]
    name = container["name"]
    
    print(f"\n[+] Connecting to {name} on {SSH_HOST}:{ssh_port} (Worker Port: {worker_port})...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SSH_HOST, port=ssh_port, username=SSH_USER, password=password, timeout=10)
        CLIENTS.append(client)
    except Exception as e:
        print(f"❌ SSH Connection failed to {name}: {e}")
        return False

    # 1. SFTP Upload Bundle
    try:
        sftp = client.open_sftp()
        sftp.put(BUNDLE_PATH, "/tmp/smart_pond_bundle.tar.gz")
        sftp.close()
        print(f"  └─ Uploaded project code bundle to {name}")
    except Exception as e:
        print(f"❌ SFTP Upload failed to {name}: {e}")
        return False

    # 2. Extract bundle & launch web_app worker on UNIQUE worker port (5001, 5002, 5003, 5004)
    commands = [
        "mkdir -p ~/smart_pond_detection",
        "tar -xzf /tmp/smart_pond_bundle.tar.gz -C ~/smart_pond_detection/",
        "pkill -9 -f 'python3 web_app.py' 2>/dev/null || true",
        "cd ~/smart_pond_detection && (python3 -m pip install --user flask numpy requests 2>/dev/null || true)",
        f"cd ~/smart_pond_detection && PORT={worker_port} nohup python3 web_app.py > worker_{worker_port}.log 2>&1 &"
    ]
    
    stdin, stdout, stderr = client.exec_command(" && ".join(commands))
    stdout.channel.recv_exit_status()
    time.sleep(1.5)

    # 3. Establish Native Paramiko Port Forwarding Tunnel to UNIQUE worker port
    transport = client.get_transport()
    start_native_paramiko_tunnel(worker_port, "127.0.0.1", worker_port, transport)
    
    print(f"✔ Worker & Tunnel Active: http://127.0.0.1:{worker_port} -> {name}")
    return True


def main():
    print("======================================================================")
    print("🚀 Native Paramiko 4-Node SSH Cluster Deployer")
    print("======================================================================")
    
    password = getpass.getpass(prompt="Enter SSH password for student@10.1.75.51: ")
    
    create_bundle()
    
    success_count = 0
    for container in CONTAINERS:
        if deploy_to_container(container, password):
            success_count += 1
            
    print(f"\n======================================================================")
    print(f"🚀 {success_count}/{len(CONTAINERS)} SSH Worker Containers Active!")
    print("Starting Central Load Balancer Gateway on http://localhost:5000...")
    print("======================================================================\n")
    
    # Import and launch Load Balancer Gateway
    from cluster_load_balancer import app as load_balancer_app
    load_balancer_app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
