import os
import textwrap


class Logger:
    def __init__(self, scenario):
        self.exp_num = 0
        self.epoch_num = 0
        self.scenario = scenario
        os.makedirs(f"_Agentbreaker_logs/{self.scenario}", exist_ok=True)

    def log(self, filename, data, is_result=False):
        os.makedirs(f"_Agentbreaker_logs/{self.scenario}/{self.exp_num}", exist_ok=True)
        path = f"_Agentbreaker_logs/{self.scenario}/{self.exp_num}/{self.epoch_num}_{filename}.log" if not is_result else f"_Agentbreaker_logs/{self.scenario}/{filename}.log"
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

    def info(self, message, indent=0):
        indent = "\t" * indent
        message = textwrap.indent(message, indent)
        print(message)

    def warning(self, message, indent=0):
        message = f"⚡WARNING⚡: {message}"
        indent = "\t" * indent
        message = textwrap.indent(message, indent)
        print(message)

    def error(self, message, indent=0):
        message = f"💥ERROR💥: {message}"
        indent = "\t" * indent
        message = textwrap.indent(message, indent)
        print(message)