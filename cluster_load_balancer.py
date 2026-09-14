"""
cluster_load_balancer.py
------------------------
High-Concurrency Performance-Based Load Balancer & Health Monitor
for 4-Node Distributed Mist Pond Catchment Analysis Cluster.

Target Cluster Nodes:
- Node 1: student@10.1.75.51 (SSH Port 2257) -> http://10.1.75.51:5001
- Node 2: student@10.1.75.51 (SSH Port 2258) -> http://10.1.75.51:5002
- Node 3: student@10.1.75.51 (SSH Port 2259) -> http://10.1.75.51:5003
- Node 4: student@10.1.75.51 (SSH Port 2260) -> http://10.1.75.51:5004

Author: Pankaj Kashyap
"""

import time
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

# Define the 4 cluster worker nodes
WORKER_NODES = [
    {"name": "System 1 (SSH 2257)", "url": "http://10.1.75.51:5001", "healthy": True, "active_reqs": 0},
    {"name": "System 2 (SSH 2258)", "url": "http://10.1.75.51:5002", "healthy": True, "active_reqs": 0},
    {"name": "System 3 (SSH 2259)", "url": "http://10.1.75.51:5003", "healthy": True, "active_reqs": 0},
    {"name": "System 4 (SSH 2260)", "url": "http://10.1.75.51:5004", "healthy": True, "active_reqs": 0},
]

def select_best_worker():
    """Selects the best available worker node using Least-Connections & Health Checks."""
    healthy_nodes = [node for node in WORKER_NODES if node["healthy"]]
    if not healthy_nodes:
        # Fallback to Node 1 if health check status fails
        return WORKER_NODES[0]
    
    # Sort by active requests (least loaded first)
    healthy_nodes.sort(key=lambda n: n["active_reqs"])
    return healthy_nodes[0]


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_to_worker(path):
    """Proxies incoming API & web traffic to the least loaded cluster worker node."""
    target_node = select_best_worker()
    target_url = f"{target_node['url']}/{path}"
    
    target_node["active_reqs"] += 1
    
    try:
        headers = {k: v for k, v in request.headers if k.lower() != "host"}
        
        if request.files:
            files_dict = {}
            for k, f in request.files.items():
                files_dict[k] = (f.filename, f.read(), f.content_type)
            resp = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=request.form,
                files=files_dict,
                params=request.args,
                timeout=60
            )
        else:
            resp = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=request.get_data(),
                params=request.args,
                timeout=60
            )
            
        target_node["healthy"] = True
        response = Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
        return response

    except requests.exceptions.RequestException as e:
        target_node["healthy"] = False
        return jsonify({"status": "error", "message": f"Cluster node {target_node['name']} unreachable: {str(e)}"}), 502
    finally:
        target_node["active_reqs"] = max(0, target_node["active_reqs"] - 1)


@app.route("/cluster/status", methods=["GET"])
def cluster_status():
    """Returns real-time health and load metrics for all 4 cluster nodes."""
    status_list = []
    for n in WORKER_NODES:
        status_list.append({
            "name": n["name"],
            "url": n["url"],
            "healthy": n["healthy"],
            "active_requests": n["active_reqs"]
        })
    return jsonify({
        "status": "active",
        "total_nodes": len(WORKER_NODES),
        "nodes": status_list
    })


if __name__ == "__main__":
    print("🚀 Starting 4-Node Load Balancer Gateway on http://0.0.0.0:5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
