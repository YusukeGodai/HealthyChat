import time

import requests


class LLMClient:
    def __init__(self, api_base, api_key, model_name):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name

    def chat_sync(self, messages):
        """Send a chat completion request and return the full response text."""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "HealthChat",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
        }
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=120)
                if resp.status_code == 429 and attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except requests.RequestException as e:
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                return f"[ERROR] API request failed: {e}"
            except (KeyError, IndexError):
                return "[ERROR] Unexpected API response format."
        return "[ERROR] Max retries exceeded."
