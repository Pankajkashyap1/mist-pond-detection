"""
expose_public_url.py
--------------------
Automated SSH reverse tunneling script to make the Mist Pond Detection platform
publicly accessible over HTTPS from any device anywhere in the world.

Author: Pankaj Kashyap
Usage: python3 expose_public_url.py [port]
"""

import sys
import time
import subprocess
import re

def expose(port=5000):
    print(f"\n🌐 Establishing Public HTTPS Tunnel for Port {port} via SSH...")
    cmd = f"ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:{port} nokey@localhost.run"
    
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    public_url = None
    start_t = time.time()
    
    while time.time() - start_t < 15:
        line = proc.stdout.readline()
        if not line:
            break
        txt = line.strip()
        print(txt)
        # Match actual tunnel domains (e.g. https://xxxx.lhr.life or https://xxxx.lhrtunnel.link)
        match = re.search(r"https://[a-zA-Z0-9\-]+\.(?:lhr\.life|lhrtunnel\.link|serveo\.net)", txt)
        if match and "admin." not in match.group(0):
            public_url = match.group(0)
            break

    if public_url:
        print("\n======================================================================")
        print("🎉 YOUR PUBLIC ACCESSIBLE URL IS LIVE!")
        print(f"👉 PUBLIC LINK: {public_url}")
        print("Anyone anywhere in the world can open this link on mobile or desktop!")
        print("======================================================================\n")
    else:
        print("\n⚠️ Tunnel connected. Keep this process running for public access.")

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    expose(port)
