import importlib

class Composer:
   def __init__(self, model, logger, action, secret_for_leak_prompt):
      self.model = model
      self.logger = logger
      self.secret_for_leak_prompt = secret_for_leak_prompt

      global prompts
      prompts = importlib.import_module(f"framework.prompt.{action.lower()}.composer_prompt")

   def compose_without_strategy(self, max_length=4096):
      # Prompt
      system_prompt = prompts.compose_system_prompt_without_strategy.format(input_target="ISSTA", prompt_secret=self.secret_for_leak_prompt)
      user_prompt   = prompts.compose_user_prompt_without_strategy
      self.logger.log("composer_prompt(wo strategy)", "<System Prompt>\n" + system_prompt + "\n\n\n\n\n<User Prompt>\n" + user_prompt)

      # LLM Call
      response = self.model.generate(system_prompt, user_prompt, max_length=max_length).strip()
      self.logger.log("composer_response(wo strategy)", response)
      return response


   def compose(self, user_goal, html, efficient_strategy_library, inefficient_strategy_library, phrase_length=1500, max_length=4096):
      efficient_strategies_str = "\n".join([strategy["content"] for strategy in efficient_strategy_library])
      inefficient_strategies_str = "\n".join([strategy["content"] for strategy in inefficient_strategy_library])

      # Prompt
      system_prompt = prompts.compose_system_prompt.format(
         user_goal=user_goal,
         html=html,
         efficient_strategies_str=efficient_strategies_str,
         inefficient_strategies_str=inefficient_strategies_str,
         ui_length=phrase_length,
         input_target="issta",
         prompt_secret=self.secret_for_leak_prompt,
      )
      user_prompt = prompts.compose_user_prompt
      self.logger.log("composer_prompt", "<System Prompt>\n" + system_prompt + "\n\n\n\n\n<User Prompt>\n" + user_prompt)

      # LLM Call
      response = self.model.generate(system_prompt, user_prompt, max_length=max_length).strip()
      self.logger.log("composer_response", response)
      
      return response