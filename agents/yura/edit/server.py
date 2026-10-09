import os
from flask import Flask, request, jsonify
import subprocess
import psutil
from pathlib import Path

app = Flask(__name__)

server_proc = None
log_file = None

BASE_DIR = Path("/Agentbreaker")

@app.route("/execute", methods=["POST"])
def execute():
    global server_proc, log_file

    try:
        data = request.get_json()
        usertask = data.get("task", "[ERROR]")
        url = data.get("url", "https://www.google.com")
        exp_num = data.get("exp", -1)
        epoch_num = data.get("epoch", -1)

        scenario = os.environ.get("SCENARIO", "default")

        with open("/app/usertask.txt", "w") as f:
            f.write(usertask)

        log_path = BASE_DIR / "_agent_logs" / f"agent_logs_{scenario}/{exp_num}_{epoch_num}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        log_file = open(log_path, "w")

        server_proc = subprocess.Popen([
                "yurascanner",
                url,
                "--headless",
                "--gpt4",
                "--taskfile", "/app/usertask.txt",
                "-t", "120"
            ], 
            stdout=log_file, 
            stderr=log_file, 
            text=True,
            env=os.environ,
            cwd=str(BASE_DIR) 
        )
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False)


@app.route("/cancel", methods=["POST"])
def cancel():
    global server_proc, log_file

    if not server_proc:
        return jsonify({"status": "no process running"})

    try:
        server_proc.kill()
    except psutil.NoSuchProcess:
        pass
        
    if log_file:
        log_file.close()

    server_proc = None
    log_file = None

    return jsonify({"status": "terminated"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
