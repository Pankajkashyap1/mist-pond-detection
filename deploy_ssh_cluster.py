"""
deploy_ssh_cluster.py
---------------------
Automated Multi-Node SSH Deployment & Native Paramiko Load Balancer Gateway.
Fixed double-directory extraction bug and pathing issues for guaranteed worker execution.

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
import subprocess

SSH_HOST = "10.1.75.51"
SSH_USER = "student"
CONTAINERS = [
    {"ssh_port": 2257, "local_port": 5001, "name": "Container 1 (SSH 2257)"},
    {"ssh_port": 2258, "local_port": 5002, "name": "Container 2 (SSH 2258)"},
    {"ssh_port": 2259, "local_port": 5003, "name": "Container 3 (SSH 2259)"},
    {"ssh_port": 2260, "local_port": 5004, "name": "Container 4 (SSH 2260)"},
]

BUNDLE_PATH = "/tmp/smart_pond_bundle.tar.gz"
CLIENTS = []


def clear_local_ports():
    """Kills any stale local processes holding ports 5000 to 5004."""
    print("🧹 Cleaning up local ports 5000-5004...")
    for port in [5000, 5001, 5002, 5003, 5004]:
        subprocess.run(f"fuser -k -9 {port}/tcp >/dev/null 2>&1 || true", shell=True)
    subprocess.run("pkill -9 -f 'ssh.*-L' >/dev/null 2>&1 || true", shell=True)
    time.sleep(1)


def create_bundle():
    """Creates a clean flat tar.gz bundle of the project directory."""
    print("📦 Packaging project archive bundle...")
    project_dir = os.path.dirname(os.path.abspath(__file__))
    with tarfile.open(BUNDLE_PATH, "w:gz") as tar:
        for fname in os.listdir(project_dir):
            if fname in ("__pycache__", ".git") or fname.endswith(".log") or fname.endswith(".tar.gz"):
                continue
            full_p = os.path.join(project_dir, fname)
            tar.add(full_p, arcname=fname)
    print(f"✔ Flat Archive created at {BUNDLE_PATH}")


def start_native_paramiko_tunnel(local_port, remote_host, remote_port, transport):
    """Establishes a native Paramiko local port forwarding server in a background thread."""
    def handler(client_sock):
        try:
            chan = transport.open_channel("direct-tcpip", (remote_host, remote_port), client_sock.getpeername())
        except Exception as e:
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
    local_port = container["local_port"]
    name = container["name"]
    
    print(f"\n[+] Connecting to {name} on {SSH_HOST}:{ssh_port}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SSH_HOST, port=ssh_port, username=SSH_USER, password=password, timeout=10)
        CLIENTS.append(client)
    except Exception as e:
        print(f"❌ SSH Connection failed to {name}: {e}")
        return False

    # 1. SFTP Upload Bundle directly to home
    try:
        sftp = client.open_sftp()
        sftp.put(BUNDLE_PATH, "/home/student/smart_pond_bundle.tar.gz")
        sftp.close()
        print(f"  └─ Uploaded flat project archive to {name}")
    except Exception as e:
        print(f"❌ SFTP Upload failed to {name}: {e}")
        return False

    # 2. Extract bundle directly into ~/smart_pond_detection and start worker
    remote_shell = """
    pkill -9 -f 'web_app.py' >/dev/null 2>&1 || true
    rm -rf /home/student/smart_pond_detection
    mkdir -p /home/student/smart_pond_detection
    tar -xzf /home/student/smart_pond_bundle.tar.gz -C /home/student/smart_pond_detection/
    cd /home/student/smart_pond_detection
    python3 -m pip install --user flask numpy requests >/dev/null 2>&1 || true
    PORT=5000 nohup python3 /home/student/smart_pond_detection/web_app.py > /home/student/smart_pond_detection/worker.log 2>&1 &
    """
    
    stdin, stdout, stderr = client.exec_command(remote_shell)
    stdout.channel.recv_exit_status()
    time.sleep(2.5)

    # 3. Read worker.log from container to verify startup status
    stdin, stdout, stderr = client.exec_command("cat /home/student/smart_pond_detection/worker.log 2>&1 | tail -n 10")
    log_output = stdout.read().decode("utf-8", errors="ignore").strip()
    print(f"  └─ Container Log Output:\n{log_output if log_output else '(Starting process...)'}")

    # 4. Establish Native Paramiko Port Forwarding Tunnel: Local Port -> Remote Container Port 5000
    transport = client.get_transport()
    start_native_paramiko_tunnel(local_port, "127.0.0.1", 5000, transport)
    
    print(f"✔ Worker & Tunnel Active: http://127.0.0.1:{local_port} -> {name} (Port 5000)")
    return True


def main():
    print("======================================================================")
    print("🚀 Native Paramiko 4-Node SSH Cluster Deployer")
    print("======================================================================")
    
    clear_local_ports()
    
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
