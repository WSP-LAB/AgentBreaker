from pathlib import Path
from dotenv import load_dotenv

import json
import yaml
import sys
import os


BASE_DIR = Path(__file__).parent

load_dotenv()
API_KEY = os.getenv("GPT_API_KEY")
ACTION = os.getenv("ACTION").upper()
AGENT = os.getenv("AGENT").upper()
MODE = os.getenv("MODE").upper()
BREAKER_LLM = os.getenv("BREAKER_LLM").upper()
SECRET_FOR_LEAK_PROMPT = os.getenv("SECRET_FOR_LEAK_PROMPT")

assert ACTION in ["TERMINATE", "CLICK", "INPUT", "PROMPT"], "ACTION must be one of 'TERMINATE', 'CLICK', 'INPUT', or 'PROMPT'."
assert AGENT in ["YURA", "AGENTE", "SKYVERN"], "AGENT must be one of 'YURA', 'AGENTE', or 'SKYVERN'."
assert MODE in ["ATTACK", "DEFENSE"], "MODE must be either 'ATTACK' or 'DEFENSE'."
assert BREAKER_LLM in ["GPT", "LLAMA"], "BREAKER_LLM must be either 'GPT' or 'LLAMA'."

scenario = f"{AGENT}_{ACTION}_{MODE}_{BREAKER_LLM}"

def set_yura():
    is_prompt = (ACTION == "PROMPT")
    is_def = (MODE == "DEFENSE")

    compose = {
        "services": {
            "YURA": {
                "image": "testforsecpaper/yura:orig",
                "container_name": scenario,
                "command": ["python3", "server.py"] if not is_def else ["/bin/sh", "-c", "uvicorn inference_server:app --host 0.0.0.0 --port 5555 & python3 server.py"],
                "ports": [
                    f"50000:8000"
                ] + (["5555:5555"] if is_def else []),
                "extra_hosts": [
                    "host.docker.internal:host-gateway"
                ],
                "volumes": [
                    "../../..:/Agentbreaker",
                    "../edit/form-module.js:/app/src/modules/form-module.js",
                    "../edit/main-module.js:/app/src/modules/main-module.js",
                    "../edit/llm-bridge.js:/app/src/bridge/llm-bridge.js",
                    "../edit/main-template.js:/app/src/prompt-templates/main-template.js",
                    "../edit/server.py:/app/server.py",
                    "../edit/actuators.js:/app/src/sensors-actuators/actuators.js",
                ] + ([
                    "../edit/sensors.js:/app/src/sensors-actuators/sensors.js",
                    "../edit/util.js:/app/src/common-utils/util.js",
                    "../edit/defense_server/infer_classifier.py:/app/infer_classifier.py",
                    "../edit/defense_server/server.py:/app/inference_server.py",
                    "../edit/defense_server/injection_detector.pt:/app/injection_detector.pt",
                ] if is_def else []
                ) + ([
                    "../edit/form-template.js:/app/src/prompt-templates/form-template.js"
                ] if is_prompt else []
                ),
                "environment": [
                    f"SCENARIO={scenario}",
                    f"OPENAI_API_KEY={API_KEY}",
                    f"SECRET_VALUE={SECRET_FOR_LEAK_PROMPT}",
                ],
                **({
                "deploy": {
                    "resources": {
                        "reservations": {
                            "devices": [
                                {
                                    "driver": "nvidia",
                                    "count": 1,
                                    "capabilities": ["gpu"]
                                }
                            ]
                        }
                    }
                }
                } if is_def else {}) 
            }
        }
    }
    return compose

def set_skyvern():
    is_def = (MODE == "DEFENSE")
    compose = {
        "services": {
            "postgres": {
                "image": "postgres:14-alpine",
                "restart": "always",
                "volumes": [
                    "./postgres-data:/var/lib/postgresql/data"
                ],
                "environment": [
                    "PGDATA=/var/lib/postgresql/data/pgdata",
                    "POSTGRES_USER=skyvern",
                    "POSTGRES_PASSWORD=skyvern",
                    "POSTGRES_DB=postgres"
                ],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U skyvern"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 5
                }
            },

            "SKYVERN": {
                "image": "testforsecpaper/skyvern:orig",
                "container_name": scenario,
                "restart": "on-failure",
                "env_file": ["../.env"],
                "extra_hosts": [
                    "host.docker.internal:host-gateway"
                ],
                "ports": [
                    "50000:8000"
                ] + (["5555:5555"] if is_def else []),
                "volumes": [
                    "../../..:/Agentbreaker",
                    "../edit/agent.py:/app/skyvern/forge/agent.py",
                    "../edit/task_v2_service.py:/app/skyvern/services/task_v2_service.py",
                    f"./.streamlit:/app/.streamlit",
                ] + ([
                    "../edit/entrypoint_for_defense.sh:/app/entrypoint-skyvern.sh",
                    "../edit/scraper.py:/app/skyvern/webeye/scraper/scraper.py",
                    "../edit/defense_server/infer_classifier.py:/app/infer_classifier.py",
                    "../edit/defense_server/server.py:/app/inference_server.py",
                    "../edit/defense_server/injection_detector.pt:/app/injection_detector.pt",
                ] if is_def else []),
                "environment": [
                    f"DATABASE_STRING=postgresql+psycopg://skyvern:skyvern@postgres:5432/postgres",
                    "BROWSER_TYPE=chromium-headless",
                    "ENABLE_CODE_BLOCK=true",
                    f"SCENARIO={scenario}",
                ]
                + (
                    [
                        "ENABLE_OPENAI=true",
                        "ENABLE_OPENAI_COMPATIBLE=false",
                        "OPENAI_COMPATIBLE_SUPPORTS_VISION=false",
                        "LLM_KEY=OPENAI_GPT4_1",
                        "SECONDARY_LLM_KEY=OPENAI_GPT4_1",
                        f"OPENAI_API_KEY={API_KEY}"
                    ]
                ),
                "depends_on": {
                    "postgres": {"condition": "service_healthy"}
                },
                "healthcheck": {
                    "test": ["CMD", "test", "-f", "/app/.streamlit/secrets.toml"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 5
                },
                **({
                    "deploy": {
                        "resources": {
                            "reservations": {
                                "devices": [
                                    {
                                        "driver": "nvidia",
                                        "count": 1,
                                        "capabilities": ["gpu"]
                                    }
                                ]
                            }
                        }
                    }
                } if is_def else {}) 
            }
        }
    }
    return compose

def set_agente():
    is_def = (MODE == "DEFENSE")
    compose = {
        "services": {
            "AGENTE": {
                "image": "testforsecpaper/agente:orig",
                "container_name": scenario,
                "command": ["/bin/sh", "-c", "/root/.local/bin/uv pip install json_repair && /app/.venv/bin/python server.py"] if not is_def else ["/bin/sh", "-c", "/root/.local/bin/uv pip install json_repair && /app/.venv/bin/uvicorn inference_server:app --host 0.0.0.0 --port 5555 & /app/.venv/bin/python server.py"],
                "ports": [
                    f"50000:8000"
                ] + (["5555:5555"] if is_def else []),
                "extra_hosts": [
                    "host.docker.internal:host-gateway"
                ],
                "environment": [
                    f"SCENARIO={scenario}",
                ],
                "volumes": [
                    "../../..:/Agentbreaker",
                    "../edit/server.py:/app/server.py",
                    "../edit/api_routes.py:/app/ae/server/api_routes.py",
                    "../edit/autogen_wrapper.py:/app/ae/core/autogen_wrapper.py",
                    "../agents_llm_config.json:/app/agents_llm_config.json",
                    "../.openai.env:/app/.env"
                ] + ([
                    "../edit/get_dom_with_content_type.py:/app/ae/core/skills/get_dom_with_content_type.py",
                    "../edit/defense_server/infer_classifier.py:/app/infer_classifier.py",
                    "../edit/defense_server/server.py:/app/inference_server.py",
                    "../edit/defense_server/injection_detector.pt:/app/injection_detector.pt",
                ] if is_def else []),
                **({
                    "deploy": {
                        "resources": {
                            "reservations": {
                                "devices": [
                                    {
                                        "driver": "nvidia",
                                        "count": 1,
                                        "capabilities": ["gpu"]
                                    }
                                ]
                            }
                        }
                    }
                } if is_def else {}) 
            }
        }
    }
    return compose


if __name__ == "__main__":
    if AGENT == "YURA":
        compose = set_yura()
    elif AGENT == "AGENTE":
        with open(BASE_DIR / "agents/agente/agents_llm_config.json", "r") as f:
            agents_llm_config = json.load(f)
            agents_llm_config["openai"]["planner_agent"]["model_api_key"] = API_KEY
            agents_llm_config["openai"]["browser_nav_agent"]["model_api_key"] = API_KEY
        with open(BASE_DIR / "agents/agente/agents_llm_config.json", "w") as f:
            json.dump(agents_llm_config, f, indent=4)

        with open(BASE_DIR / "agents/agente/.openai.env", "r", encoding="utf-8") as f:
            lines = f.readlines()
            updated_lines = []
            for line in lines:
                if line.startswith("AUTOGEN_MODEL_API_KEY="):
                    updated_lines.append(f"AUTOGEN_MODEL_API_KEY={API_KEY}")
                else:
                    updated_lines.append(line.strip())
        with open(BASE_DIR / "agents/agente/.openai.env", "w", encoding="utf-8") as f:
            f.write("\n".join(updated_lines) + "\n")

        compose = set_agente()

    elif AGENT == "SKYVERN":
        compose = set_skyvern()
    else:
        print("Invalid AGENT specified in .env file. (AGENT=[yura|agente|skyvern])")
        sys.exit(1)

    with open(BASE_DIR / "agents" / AGENT.lower() / "docker/docker-compose.yml", "w") as f:
        yaml.dump(compose, f, sort_keys=False)