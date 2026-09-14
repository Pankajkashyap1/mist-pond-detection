"""
cluster_load_balancer.py
------------------------
High-Concurrency Performance-Based Load Balancer with Automatic Retry & Failover
for 4-Node Distributed Mist Pond Catchment Analysis Cluster.

SSH Worker Nodes:
- System 1 (SSH 2257): http://127.0.0.1:5001
- System 2 (SSH 2258): http://127.0.0.1:5002
- System 3 (SSH 2259): http://127.0.0.1:5003
- System 4 (SSH 2260): http://127.0.0.1:5004

Author: Pankaj Kashyap
"""

import time
import requests
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

WORKER_NODES = [
    {"name": "System 1 (SSH 2257)", "url": "http://127.0.0.1:5001", "healthy": True, "active_reqs": 0},
    {"name": "System 2 (SSH 2258)", "url": "http://127.0.0.1:5002", "healthy": True, "active_reqs": 0},
    {"name": "System 3 (SSH 2259)", "url": "http://127.0.0.1:5003", "healthy": True, "active_reqs": 0},
    {"name": "System 4 (SSH 2260)", "url": "http://127.0.0.1:5004", "healthy": True, "active_reqs": 0},
]


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_to_worker(path):
    """
    Proxies incoming requests across the 4 cluster worker nodes with automatic retry & failover.
    """
    # Sort healthy nodes by active requests (least loaded first)
    available_nodes = [n for n in WORKER_NODES if n["healthy"]]
    if not available_nodes:
        # Reset health status if all marked down
        for n in WORKER_NODES:
            n["healthy"] = True
        available_nodes = WORKER_NODES[:]

    available_nodes.sort(key=lambda n: n["active_reqs"])

    headers = {k: v for k, v in request.headers if k.lower() != "host"}
    req_files = None
    if request.files:
        req_files = {}
        for k, f in request.files.items():
            f_bytes = f.read()
            f.seek(0)
            req_files[k] = (f.filename, f_bytes, f.content_type)

    last_error = "No worker available"

    for target_node in available_nodes:
        target_url = f"{target_node['url']}/{path}"
        target_node["active_reqs"] += 1
        try:
            if req_files:
                # Re-send file bytes for retries
                files_payload = {k: (v[0], v[1], v[2]) for k, v in req_files.items()}
                resp = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=request.form,
                    files=files_payload,
                    params=request.args,
                    timeout=30
                )
            else:
                resp = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=request.get_data(),
                    params=request.args,
                    timeout=30
                )

            target_node["healthy"] = True
            return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))

        except requests.exceptions.RequestException as e:
            target_node["healthy"] = False
            last_error = f"{target_node['name']} ({target_node['url']}): {str(e)}"
            continue
        finally:
            target_node["active_reqs"] = max(0, target_node["active_reqs"] - 1)

    return jsonify({
        "status": "error",
        "message": f"All cluster nodes failed. Last error: {last_error}"
    }), 502


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
