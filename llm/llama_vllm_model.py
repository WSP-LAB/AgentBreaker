from openai import OpenAI
from openai import OpenAIError
import time

class LlamaVLLMModel:
    def __init__(self, model_name="meta-llama/llama-4-scout-17b-16e-instruct", api_key=None):
        self.client = OpenAI(
            base_url="https://api.novita.ai/openai",
            api_key=api_key,
        )
        self.model_name = model_name

    def _truncate_user(self, text, max_words=1500):
        words = text.strip().split()
        return " ".join(words[:max_words]) if len(words) > max_words else text.strip()

    def generate(self, system, user, max_length=8192, **kwargs):
        user = self._truncate_user(user, max_words=1500)
        retries = 0
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    stream=False,
                    extra_body={},
                    max_tokens=min(max_length, 8192),
                    temperature=kwargs.get("temperature", 0.0),
                    top_p=kwargs.get("top_p", 0.1)
                )
                return response.choices[0].message.content
            
            except OpenAIError as e:
                err_msg = str(e)
                if "invalid character 'i' in literal false" in err_msg:
                    print(f"[WARNING] JSON parse error in response: {err_msg}")
                    print("[ACTION] Retrying once after short delay...")
                    retries += 1
                    time.sleep(1) 
                    continue
                else:
                    print(f"[ERROR] InternalServerError occurred: {err_msg}")
                    raise 

            except Exception as e:
                print(f"[ERROR] Unhandled Exception in generate(): {e}")
                raise