import json
from flask import Flask, request, jsonify
import subprocess
import psutil
import time
import os
from pathlib import Path

app = Flask(__name__)

server_proc = None
req_proc = None
log_file = None

BASE_DIR = Path("/Agentbreaker")
AGENTE_DIR = Path("/app")
AGENTE_PYTHON = AGENTE_DIR / ".venv/bin/python"
AGENTE_PORT = int(os.getenv("AGENTE_PORT", 7777))


@app.route("/execute", methods=["POST"])
def execute():
    global server_proc, req_proc, log_file

    data = request.get_json()
    usertask = data.get("task", "[ERROR]")
    
    exp_num = data.get("exp", -1)
    epoch_num = data.get("epoch", -1)

    scenario = os.environ["SCENARIO"]

    log_path = BASE_DIR / "_agent_logs" / f"agent_logs_{scenario}/{exp_num}_{epoch_num}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = open(log_path, "w")


    server_proc = subprocess.Popen(
        [
            AGENTE_PYTHON, "-m", "uvicorn",
            "ae.server.api_routes:app",
            "--loop", "asyncio",
            "--port", str(AGENTE_PORT)
        ],
        cwd=AGENTE_DIR,
        stdout=log_file,
        stderr=log_file,
        env=os.environ,
    )

    with open(log_path, "r") as f:
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            if "Application startup complete." in line:
                break
    
    try:
        payload = payload = {"command": usertask}

        curl_cmd = [
            "curl", "-X", "POST",
            f"http://localhost:{AGENTE_PORT}/execute_task",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload)
        ]

        req_proc = subprocess.Popen(
            curl_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False)



@app.route("/cancel", methods=["POST"])
def cancel():
    global server_proc, log_file
    message = "abc"
    if not server_proc:
        return jsonify({"status": "no process running"})

    isfail = False
    try:
        proc = psutil.Process(server_proc.pid)
        for child in proc.children(recursive=True):
            child.terminate()
        proc.terminate()
        proc.wait(timeout=5)
    except psutil.NoSuchProcess:
        isfail = True
        messege = "NoSuchProcess"
        pass
    except psutil.TimeoutExpired:
        isfail= True
        messege = "TimeoutExpired"
        proc.kill()
    except Exception as e:
        isfail = True
        messege = str(e)
        pass

    if log_file:
        log_file.close()

    server_proc = None
    log_file = None

    if isfail:
        return jsonify({"status": f"{message}"})
    else:
        return jsonify({"status": "killed"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)