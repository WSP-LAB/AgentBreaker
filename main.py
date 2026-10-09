from framework.composer import Composer
from framework.lmtester import LMTester
from framework.logger import Logger
from framework.deployer.main import Deployer
from framework.evaluator import EvaluatorFactory
from llm.openai_vllm_model import OpenAIVLLMModel
from llm.llama_vllm_model import LlamaVLLMModel
from attack import Agentbreaker

from dotenv import load_dotenv
from pathlib import Path
import json
import os

BASE_DIR = Path(__file__).parent

load_dotenv()
OPENAI_API_KEY = os.getenv("GPT_API_KEY")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
ACTION = os.getenv("ACTION").upper()
AGENT = os.getenv("AGENT").upper()
MODE = os.getenv("MODE").upper()
isDEMO = os.getenv("DEMO").upper()
BREAKER_LLM = os.getenv("BREAKER_LLM").upper()
SECRET_FOR_LEAK_PROMPT = os.getenv("SECRET_FOR_LEAK_PROMPT")

assert ACTION in ["TERMINATE", "CLICK", "INPUT", "PROMPT"], "ACTION must be one of 'TERMINATE', 'CLICK', 'INPUT', or 'PROMPT'."
assert AGENT in ["YURA", "AGENTE", "SKYVERN"], "AGENT must be one of 'YURA', 'AGENTE', or 'SKYVERN'."
assert MODE in ["ATTACK", "DEFENSE"], "MODE must be either 'ATTACK' or 'DEFENSE'."
assert BREAKER_LLM in ["GPT", "LLAMA"], "BREAKER_LLM must be either 'GPT' or 'LLAMA'."
assert isDEMO in ["TRUE", "FALSE"], "DEMO must be either 'TRUE' or 'FALSE'."
isDEMO = True if isDEMO == "TRUE" else False

def main():
    model = None
    helper_model = None
    if BREAKER_LLM == "GPT":
        model = OpenAIVLLMModel(model_name="gpt-4.1", api_key=OPENAI_API_KEY)
        helper_model = OpenAIVLLMModel(model_name="gpt-4.1", api_key=OPENAI_API_KEY)
    elif BREAKER_LLM == "LLAMA":
        model = LlamaVLLMModel(model_name="meta-llama/llama-4-scout-17b-16e-instruct", api_key=LLAMA_API_KEY)
        helper_model = OpenAIVLLMModel(model_name="gpt-4.1", api_key=OPENAI_API_KEY)
    scenario = f"{AGENT}_{ACTION}_{MODE}_{BREAKER_LLM}"
    logger = Logger(scenario)
    logger.info(f"Starting scenario: {scenario}")
    
    # Agentbreaker Components ###
    composer = Composer(model, logger, ACTION, SECRET_FOR_LEAK_PROMPT)
    lmtester = LMTester(model, logger, ACTION, SECRET_FOR_LEAK_PROMPT, helper_model)
    evaluator = EvaluatorFactory().get_evaluator(AGENT, ACTION, MODE, BREAKER_LLM, SECRET_FOR_LEAK_PROMPT)
    #############################
    
    deployer = Deployer(AGENT, ACTION, MODE)
    
    pipeline = Agentbreaker(
        logger=logger,
        composer=composer,
        lmtester=lmtester,
        evaluator=evaluator,
        deployer=deployer
    )

    with open("dataset/htmls.json", 'r', encoding='utf-8') as f:
        html_dataset = json.load(f)
    
    if isDEMO:
        demo_sublist = [0, 1, 2, 3, 4]
        html_dataset = {k: v for k, v in html_dataset.items() if int(k) in demo_sublist}
    
    exp_results = []
    for exp_num, exp_data in html_dataset.items():
        logger.info(f"\n===========================================> {exp_num} START")
        
        result = pipeline.run(exp_num, exp_data)
        exp_results.append(result)
        
        logger.log("result_summary", json.dumps(exp_results, indent=2, ensure_ascii=False), is_result=True)
        
        logger.info(f"\n=========================================== {exp_num} END\n")

    print_summary(scenario, exp_results)

def print_summary(scenario, exp_results):
    total = len(exp_results)
    success_count = sum(1 for r in exp_results if r["success"])
    asr = (success_count / total * 100) if total else 0.0
    avg_time = (sum(r["optimization_time_sec"] for r in exp_results) / total) if total else 0.0

    print("[INFO] Experiment completed.")
    print(f"Scenario: {scenario}")
    print(f"ASR: {asr:.2f}% ({success_count}/{total})")
    print(f"Avg Optimization Time: {avg_time:.2f}s")

if __name__ == "__main__":
    main()