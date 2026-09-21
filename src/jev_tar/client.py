# Purpose: Hardened stdlib Jev HTTP client and contract-compatible offline fake.
from __future__ import annotations
import json, os, random, time, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass

MODEL = "jev-1.13.0"
PRICE = 0.042

def estimate_tokens(value: object) -> int:
    return (len(value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))) + 3) // 4

def _validate(endpoint: str, api_key: str | None) -> None:
    if not api_key:
        raise ValueError("Set TYPESAFE_API_KEY")
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}):
        raise ValueError("Jev endpoint must use HTTPS (localhost is allowed in tests)")

@dataclass
class JevClient:
    """Small validated client; retries only transient network, 429 and 529 failures."""
    api_key: str | None = None
    endpoint: str = "https://api.typesafe.ai/v1/systemone"
    model: str = MODEL
    timeout: float = 30.0
    max_retries: int = 2
    state_token_budget: int = 24_000

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("TYPESAFE_API_KEY")
        _validate(self.endpoint, self.api_key)

    def judge(self, state: dict, questions: dict) -> dict:
        if estimate_tokens(state) > self.state_token_budget:
            raise ValueError("State exceeds the 24000-token default budget; chunk the document")
        body = json.dumps({"model": self.model, "state": state, "questions": questions}).encode()
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(self.endpoint, body, {"authorization": f"Bearer {self.api_key}", "content-type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    result = json.load(response)
                return self._checked(result, questions)
            except urllib.error.HTTPError as error:
                if error.code not in {429, 529} or attempt == self.max_retries:
                    raise RuntimeError(f"Jev HTTP {error.code}") from None
                retry = error.headers.get("retry-after")
                time.sleep(float(retry) if retry else (2 ** attempt + random.random()) / 10)
            except (urllib.error.URLError, TimeoutError) as error:
                if attempt == self.max_retries:
                    raise RuntimeError("Jev network request failed") from error
                time.sleep((2 ** attempt + random.random()) / 10)
        raise AssertionError("unreachable")

    def _checked(self, result: dict, questions: dict) -> dict:
        if result.get("model") != self.model:
            raise ValueError("Jev response model mismatch")
        answers = result.get("answers", {})
        for key, question in questions.items():
            answer = answers.get(key)
            if not isinstance(answer, dict) or answer.get("type") != question.get("type"):
                raise ValueError(f"Missing or invalid answer for {key}")
            probabilities = answer.get("probabilities", {"true": answer.get("noul")})
            if any(not isinstance(p, (int, float)) or not 0 <= p <= 1 for p in probabilities.values()):
                raise ValueError(f"Invalid probability for {key}")
        usage = result.get("usage", {})
        result["estimated_cost_usd"] = usage.get("input_tokens", 0) * PRICE / 1_000_000
        return result

class FakeJev:
    """Deterministic fixture provider with call capture and the production method shape."""
    def __init__(self, fixtures: dict | None = None):
        self.fixtures, self.calls = fixtures or {}, []

    def judge(self, state: dict, questions: dict) -> dict:
        self.calls.append((state, questions))
        answers = {}
        for key in questions:
            probability = self.fixtures.get(state.get("id"), {}).get(key, 0.9 if "responsive" in state.get("text", "").lower() else 0.1)
            answers[key] = {"type": "noul", "noul": probability, "probabilities": {"true": probability, "false": 1-probability}}
        return {"model": MODEL, "answers": answers, "usage": {"input_tokens": estimate_tokens(state)}}
