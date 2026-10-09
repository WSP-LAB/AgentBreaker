from http.server import SimpleHTTPRequestHandler, HTTPServer
from functools import partial
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2] # Agentbreaker/
CRBR_LOG_DIR = BASE_DIR / "_Agentbreaker_logs"

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, working_dir="/", default_file="index.html", **kwargs):
        self.working_dir = working_dir
        self.default_file = default_file
        super().__init__(*args, directory=self.working_dir, **kwargs)

    def do_GET(self):
        super().do_GET()

    def send_head(self):
        if self.path in ("/", "/index.html"):
            self.path = "/" + self.default_file
        return super().send_head()

def run_server(port, working_dir="/", default_file="index.html"):
    handler = partial(CustomHandler, working_dir=working_dir, default_file=default_file)
    server = HTTPServer(("0.0.0.0", port), handler)
    server.serve_forever()

if __name__ == "__main__":
    global scenario, exp_num
    port, dir, scenario, exp_num = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]

    run_server(port=port, working_dir=dir, default_file=f"{scenario}.html")
