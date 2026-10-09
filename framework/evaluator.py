from framework.evaluators.yura import YuraValidator as YURA_VALIDATOR
from framework.evaluators.skyvern import SkyvernValidator as SKYVERN_VALIDATOR
from framework.evaluators.agente import AgenteValidator as AGENTE_VALIDATOR

class EvaluatorFactory():
    def get_evaluator(self, agent, action, mode, breaker_llm, secret_for_leak_prompt=None):
        if agent == "YURA":
            return YURA_VALIDATOR(agent, action, mode, breaker_llm, secret_for_leak_prompt)
        if agent == "SKYVERN":
            return SKYVERN_VALIDATOR(agent, action, mode, breaker_llm, secret_for_leak_prompt)
        if agent == "AGENTE":
            return AGENTE_VALIDATOR(agent, action, mode, breaker_llm, secret_for_leak_prompt)

        raise NotImplementedError(f"Evaluator for {agent} is not implemented.")