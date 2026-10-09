import subprocess
import re
import html
import sys
from framework.deployer.template import AD, FORM, ATTACK_ELE
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_HTML_DIR = BASE_DIR / "dataset" / "htmls"
ATTACK_HTML_DIR = BASE_DIR / "dataset" / "attack_htmls"
RUN_SERVER_FILE = BASE_DIR / "framework" / "deployer" / "server.py"

class Deployer:
    def __init__(self, agent, action, mode):
        self.action = action
        self.agent = agent
        self.mode = mode

    def sanitize_trigger(self, trigger: str) -> str:
        if trigger is None:
            return ''

        s = str(trigger)
        s = s.replace('\r', ' ').replace('\n', ' ')
        s = re.sub(r'\s+', ' ', s).strip()
        s = html.escape(s, quote=True)
        s = s.replace('</', '<\\/')
        s = s.replace('{', '{{').replace('}', '}}')
        s = s.replace('\\', '\\\\')
        return s

    def inject(self, trigger, exp_num):
        try:
            input_path = INPUT_HTML_DIR / str(exp_num) / "index.html"
            output_path = ATTACK_HTML_DIR / "index.html"
            with open(input_path, "r", encoding="utf-8", errors="replace") as f:
                html_content = f.read()

            ################################
            # First, inject attack payload #
            ################################
            if "</body>" not in html_content or not re.search(r'<body[^>]*?>', html_content):
                raise ValueError("<body></body> tag not found in HTML file")

            trigger = self.sanitize_trigger(trigger)

            # split attack (Adapt to agent's input limit; 50 char for yura)
            if self.mode == "defense" or self.agent == "YURA":
                truncation_limit = 49
                triggers = [trigger[i:i+truncation_limit] for i in range(0, len(trigger), truncation_limit)]
                attack_element = "\n".join([ATTACK_ELE[self.agent].format(trigger=trig) for trig in triggers])
            else:
                attack_element = ATTACK_ELE[self.agent].format(trigger=trigger)

            html_content = html_content.replace("</body>", attack_element + "</body>")

            ###################################################
            # Second, inject target ad button or target input #
            ###################################################
            if self.action == "CLICK":
                ad_injection = AD[self.agent]
                html_content = re.sub(r'(<body[^>]*>)', r'\1' + ad_injection, html_content)

            elif self.agent == "YURA" and self.action in ["INPUT", "PROMPT"]:
                inner_inputs = "\n".join([
                    FORM["YURA_SPLIT_INNER"].format(id=f"{idx}", trigger=trig)
                    for idx, trig in enumerate(triggers)
                ])
                inner_buttons = "\n".join([
                    FORM["YURA_SPLIT_INNER_AD"].format(id=f"btn_{idx}", trigger=trig)
                    for idx, trig in enumerate(triggers)
                ])
                form_injection = FORM[f"YURA_SPLIT_OUTTER"].format(
                    inner_inputs=inner_inputs,
                    inner_buttons=inner_buttons
                )
                html_content = re.sub(r'(<body[^>]*>)', r'\1' + form_injection, html_content)
            elif self.action in ["INPUT", "PROMPT"]:
                form_injection = FORM[self.agent].format()
                html_content = re.sub(r'(<body[^>]*>)', r'\1' + form_injection, html_content)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        except Exception as e:
            print(f"Failed to inject UI text: {str(e)}")


    def deploy(self):
        try:
            p = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "http.server",
                    "3001",
                ],
                cwd=str(ATTACK_HTML_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return p
        except Exception as e:
            print(f"[Error] Failed to launch server: {e}")
