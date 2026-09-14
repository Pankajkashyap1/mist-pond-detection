"""
cluster_load_balancer.py
------------------------
High-Concurrency Performance-Based Load Balancer & Health Monitor
for 4-Node Distributed Mist Pond Catchment Analysis Cluster.

Author: Pankaj Kashyap
"""

import time
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

# Define the 4 cluster worker nodes (Update IP addresses as needed)
WORKER_NODES = [
    {"name": "Node 1 (Local/Primary)", "url": "http://127.0.0.1:5001", "healthy": True, "active_reqs": 0},
    {"name": "Node 2 (Worker 2)",     "url": "http://10.1.75.51:5001",  "healthy": True, "active_reqs": 0},
    {"name": "Node 3 (Worker 3)",     "url": "http://10.1.75.53:5001",  "healthy": True, "active_reqs": 0},
    {"name": "Node 4 (Worker 4)",     "url": "http://10.10.3.147:5001", "healthy": True, "active_reqs": 0},
]

rr_index = 0

def select_best_worker():
    """Selects the best available worker node using Least-Connections & Health Checks."""
    global rr_index
    healthy_nodes = [node for node in WORKER_NODES if node["healthy"]]
    if not healthy_nodes:
        # Fallback to local if health checks fail
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
    start_t = time.time()
    
    try:
        # Forward headers & data/files
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
        # Try fallback to local worker node
        if target_node != WORKER_NODES[0]:
            try:
                fallback_url = f"{WORKER_NODES[0]['url']}/{path}"
                resp = requests.request(
                    method=request.method,
                    url=fallback_url,
                    headers={k: v for k, v in request.headers if k.lower() != "host"},
                    data=request.get_data(),
                    params=request.args,
                    timeout=60
                )
                return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
            except Exception:
                pass
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
    print("🚀 Starting 4-Node Load Balancer Gateway on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
