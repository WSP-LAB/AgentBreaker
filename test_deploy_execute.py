from dotenv import load_dotenv
from pathlib import Path
import os
import time
import signal
import requests

from framework.evaluator import EvaluatorFactory
from framework.deployer.main import Deployer

BASE_DIR = Path(__file__).parent

ATTACK_HTML_DIR = BASE_DIR / "dataset" / "attack_htmls"

load_dotenv()
ACTION = os.getenv("ACTION").upper()
AGENT = os.getenv("AGENT").upper()
MODE = os.getenv("MODE").upper()
BREAKER_LLM = os.getenv("BREAKER_LLM").upper()
isDEMO = os.getenv("DEMO").upper()
SECRET_FOR_LEAK_PROMPT = os.getenv("SECRET_FOR_LEAK_PROMPT")

assert ACTION in ["TERMINATE", "CLICK", "INPUT", "PROMPT"], "ACTION must be one of 'TERMINATE', 'CLICK', 'INPUT', or 'PROMPT'."
assert AGENT in ["YURA", "AGENTE", "SKYVERN"], "AGENT must be one of 'YURA', 'AGENTE', or 'SKYVERN'."
assert MODE in ["ATTACK", "DEFENSE"], "MODE must be either 'ATTACK' or 'DEFENSE'."
assert BREAKER_LLM in ["GPT", "LLAMA"], "BREAKER_LLM must be either 'GPT' or 'LLAMA'."
assert isDEMO in ["TRUE", "FALSE"], "DEMO must be either 'TRUE' or 'FALSE'."


def main():
    usertask = "Click the button on the screen!"

    html = """
<!DOCTYPE html>
<html>
<body>
    <h1>Welcome to the Test Page</h1>
    <button id="target-button">Click Me!</button>
</body>
</html>
    """
    
    with open(ATTACK_HTML_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[INFO] Checking status of agent '{AGENT}'")
    print("[INFO] Test webpage:")
    print(html)

    deployer = Deployer(AGENT, ACTION, MODE)
    html_p = deployer.deploy()

    def _timeout_handler(_signum, _frame):
        print("[INFO] Evaluation timed out after 10 minutes. Please retry smoke test.")
        exit(0)

    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(600)

    if MODE == "DEFENSE":
        while True:
            try:
                resp = requests.get("http://host.docker.internal:5555/health", timeout=5)
                if resp.status_code == 200:
                    break
            except requests.RequestException:
                pass
            print("[INFO] Defense server is not ready yet, please wait...")
            time.sleep(10)
        
    print("[INFO] Agent is executing the task... (It can take up to 10 minutes)")

    try:
        evaluator = EvaluatorFactory().get_evaluator(AGENT, ACTION, MODE, BREAKER_LLM, SECRET_FOR_LEAK_PROMPT)
        success = evaluator.validate(usertask=usertask, exp_num=100, epoch_num=0, is_test=True)
    except FileNotFoundError as e:
        print("[IMPORTANT] Container is not ready. Please retry the smoke test after 1 minute. (It can take up to 5 minutes)")
        exit(0)
    except Exception as e:
        if str(e) == "AGENT_NOT_FOUND":
            print("[IMPORTANT] Container is not ready. Please retry the smoke test after 1 minute. (It can take up to 5 minutes)")
            exit(0)
        else:
            raise e
    finally:
        signal.alarm(0)
        html_p.kill()

    if success:
        print(f"[OK] Agent '{AGENT}' clicked the button. Status: Healthy")
    else:
        print(f"[FAIL] Agent '{AGENT}' failed to click the button. Something might be wrong.")

if __name__ == "__main__":
    main()
