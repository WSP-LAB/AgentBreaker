
import openai
import time
from openai import RateLimitError

class OpenAIVLLMModel:
    def __init__(self, model_name="gpt-4.1", api_key=None):
        openai.api_key=api_key
        self.model_name = model_name

    def _truncate_user(self, text, max_words=1500):
        words = text.strip().split()
        return " ".join(words[:max_words]) if len(words) > max_words else text.strip()

    def generate(self, system, user, max_length=4096, **kwargs):
        user = self._truncate_user(user, max_words=1500)

        while True:
            try:
                response = openai.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    max_tokens=min(max_length, 4096),
                    temperature=kwargs.get("temperature", 0.0),
                    top_p=kwargs.get("top_p", 0.1)
                )
                return response.choices[0].message.content

            except RateLimitError:
                time.sleep(0.5)

            except Exception as e:
                print(f"[ERROR] Unhandled Exception in generate(): {e}")
                raise