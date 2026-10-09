import json
import importlib
from json_repair import repair_json

class LMTester:
    def __init__(self, model, logger, action, secret_for_leak_prompt, helper_model):
        self.model = model
        self.helper_model = helper_model
        self.logger = logger
        self.secret_for_leak_prompt = secret_for_leak_prompt

        global prompts
        prompts = importlib.import_module(f"framework.prompt.{action.lower()}.lmtester_prompt")


    def lmtest(self, ui_text, html, usertask, max_length=4096):
        # Prompt
        system_prompt = prompts.lmtest_system_prompt.format(
            usertask=usertask, 
            elements=html, 
            ui_text=ui_text,
            input_target="ISSTA", 
            prompt_secret=self.secret_for_leak_prompt,
        )
        user_prompt   = prompts.lmtest_user_prompt
        self.logger.log("lmtester_lmtest_prompt", "<System Prompt>\n" + system_prompt + "\n\n\n\n\n<User Prompt>\n" + user_prompt)

        # LLM Call
        response = self.model.generate(system=system_prompt, user=user_prompt, max_length=max_length).strip()
        self.logger.log("lmtester_lmtest_response", response)

        
        try:
            target_rank, rank1_reason, rank1_sentence = None, None, None
            target_rank, rank1_sentence = self.extract_rank1_sentence_and_target_rank(response)
            rank1_reason = self.extract_rank1_reason(response)
        except Exception as e:
            target_rank, rank1_sentence, rank1_reason = 10, rank1_sentence or "Top-1 action is unknown", rank1_reason or "Top-1 reason is unknown"
            self.logger.error(f"[LM Tester Parsing Error]: {str(e)}", indent=2)
            
        return int(target_rank), str(rank1_sentence), str(rank1_reason)
    
    def extract_rank1_reason(self, llm_response):
        return llm_response.split("Reason:")[-1].strip().replace("`", "").replace("```", "").strip()
    
    def extract_rank1_sentence_and_target_rank(self, llm_response, max_length=4096):
        system_prompt = prompts.ranking_system_prompt.format(llm_response=llm_response,input_target="ISSTA", prompt_secret=self.secret_for_leak_prompt)
        user_prompt   = prompts.ranking_user_prompt

        self.logger.log("lmtester_ranking_prompt", "<System Prompt>\n" + system_prompt + "\n\n\n\n\n<User Prompt>\n" + user_prompt)
        
        response = self.helper_model.generate(system=system_prompt, user=user_prompt, max_length=max_length).strip()
        self.logger.log("lmtester_ranking_response", response.strip())

        try:
            response = repair_json(response.replace("`", ""))
            result = json.loads(response)
        except Exception:
            raise ValueError(f"Failed to parse [target_rank, rank1_sentence]: {response}")
        
        return result
    
    def makeup_new_strategy(self, user_goal, html, top1_action, top1_reason, existing_strategies=[], max_length=4096):
        existing_strategies_str = "\n".join([strategy["content"] for strategy in existing_strategies])

        # Prompt
        system_prompt = prompts.makeup_system_prompt.format(
            user_goal=user_goal, 
            html=html, 
            top1_action=top1_action, 
            top1_reason=top1_reason, 
            existing_strategies=existing_strategies_str,
            input_target="ISSTA",
            prompt_secret=self.secret_for_leak_prompt,
        )
        user_prompt   = prompts.makeup_user_prompt
        self.logger.log("new_strategy_prompt", "<System Prompt>\n" + system_prompt + "\n\n\n\n\n<User Prompt>\n" + user_prompt)

        # LLM Call
        response = self.model.generate(system=system_prompt, user=user_prompt, max_length=max_length).strip()
        self.logger.log("new_strategy_response", response)

        return {
            "content": response
        }
    