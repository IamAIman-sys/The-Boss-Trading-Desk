"""Official Python SDK connected to Purdue GenAI Studio."""

import json
from pathlib import Path
import time

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI

ROOT = Path(__file__).resolve().parent
PURDUE_URL = "https://genai.rcac.purdue.edu/api"


class ModelError(Exception):
    pass


class ModelClient:
    def __init__(self, env_path=ROOT / ".env"):
        settings = dotenv_values(env_path, interpolate=False)
        key = settings.get("API_KEY")
        if not key or key == "paste-here":
            raise ModelError("Set your Purdue GenAI Studio API_KEY in .env.")
        self.model = settings.get("MODEL") or "gpt-oss:120b"
        self.base_url = (settings.get("API_BASE_URL") or PURDUE_URL).rstrip("/")
        if self.base_url != PURDUE_URL:
            raise ModelError("This client expects Purdue's API_BASE_URL: " + PURDUE_URL)
        self.client = OpenAI(api_key=key, base_url=self.base_url, timeout=180, max_retries=0,
                             default_headers={"User-Agent": settings.get("SEC_USER_AGENT") or "ResearchDesk"})
        self.last_request = 0.0
        self.last_metadata = {}

    def complete(self, instructions, payload, max_tokens=6000):
        """Fresh messages per role; retry only transient transport/service errors."""
        for attempt in range(3):
            time.sleep(max(0, 3.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": instructions},
                              {"role": "user", "content": json.dumps(payload)}],
                    max_tokens=max_tokens, temperature=0,
                    response_format={"type": "json_object"},
                )
            except APIStatusError as exc:
                if exc.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise ModelError(f"Purdue model request failed: HTTP {exc.status_code}.") from None
                time.sleep(10 * (attempt + 1))
                continue
            except APIConnectionError:
                if attempt == 2:
                    raise ModelError("Could not reach Purdue's model service after 3 attempts.") from None
                time.sleep(10 * (attempt + 1))
                continue
            # Purdue documents JSON null responses when rate limited.
            if response is None or not response.choices:
                if attempt < 2:
                    time.sleep(10 * (attempt + 1))
                    continue
                raise ModelError("Purdue returned no completion after 3 attempts.")
            choice = response.choices[0]
            if choice.finish_reason == "length":
                raise ModelError("Model output reached its token limit; no incomplete report was accepted.")
            content = choice.message.content or ""
            try:
                result = json.loads(content)
            except ValueError:
                raise ModelError("Model did not return the requested JSON object.") from None
            if not isinstance(result, dict):
                raise ModelError("Model response must be a JSON object.")
            self.last_metadata = {"requested_model": self.model, "returned_model": response.model,
                                  "usage": response.usage.model_dump() if response.usage else None,
                                  "response_id": response.id}
            return result
        raise ModelError("Model request failed.")


def main():
    try:
        client = ModelClient()
        result = client.complete('Return JSON only: {"status":"ready"}.',
                                 {"task": "Check the connection; do not use tools."}, max_tokens=512)
        if result.get("status") != "ready":
            raise ModelError("Connection returned an unexpected test response.")
        print("Provider: Purdue GenAI Studio")
        print("Requested model:", client.model)
        print("Returned model:", client.last_metadata["returned_model"])
        print("Connection test: passed")
        return 0
    except ModelError as exc:
        print("ERROR:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
