"""
GTM AI Operations Agent — HuggingFace LLM Integration
Supports triage, requirements extraction, blueprint generation, and executive summaries.
Falls back to mock responses when no API token is available.
"""
import os
import json
import time
from typing import Optional, Dict, Any

import requests

from agent.prompts import (
    TRIAGE_SYSTEM_PROMPT, get_triage_prompt,
    REQUIREMENTS_SYSTEM_PROMPT, get_requirements_prompt,
    BLUEPRINT_SYSTEM_PROMPT, get_blueprint_prompt,
    SUMMARY_SYSTEM_PROMPT, get_summary_prompt,
    MOCK_TRIAGE_RESPONSE, MOCK_REQUIREMENTS_RESPONSE, MOCK_BLUEPRINT_RESPONSE,
)


class GTMOpsAgent:
    """
    AI Agent for GTM Operations Hub.
    Uses HuggingFace Inference API (OpenAI-compatible) with graceful mock fallback.
    """

    def __init__(self, hf_token: Optional[str] = None, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.model = model
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else None

    # ─────────── Core LLM Call ───────────

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> Optional[str]:
        """Call HuggingFace Inference API. Returns raw text or None on failure."""
        if not self.hf_token:
            return None

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
        }

        try:
            resp = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0].get("message", {}).get("content", "").strip()
            elif resp.status_code == 503:
                # Model loading — retry once after wait
                time.sleep(10)
                resp = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0].get("message", {}).get("content", "").strip()
            else:
                print(f"[Agent] HF API error {resp.status_code}: {resp.text[:200]}")
            return None
        except Exception as exc:
            print(f"[Agent] HF API exception: {exc}")
            return None

    def _parse_json(self, text: str) -> Optional[dict]:
        """Attempt to parse JSON from LLM output, handling markdown fences."""
        if not text:
            return None
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON object from the text
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass
        return None

    # ─────────── Public Methods ───────────

    def triage_request(self, pain_point: str, workflow_stage: str, manual_time: str,
                       urgency: str, requester_team: str) -> Dict[str, Any]:
        """Classify an intake request using LLM. Returns structured triage result."""
        start = time.time()
        user_prompt = get_triage_prompt(pain_point, workflow_stage, manual_time, urgency, requester_team)
        raw = self._call_llm(TRIAGE_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_json(raw) if raw else None

        if parsed:
            result = parsed
            result["_source"] = "llm"
        else:
            result = dict(MOCK_TRIAGE_RESPONSE)
            result["_source"] = "mock"

        result["_latency_ms"] = round((time.time() - start) * 1000)
        return result

    def generate_requirements(self, pain_point: str, context: str = "") -> Dict[str, Any]:
        """Generate a structured requirements brief from a free-text request."""
        start = time.time()
        user_prompt = get_requirements_prompt(pain_point, context)
        raw = self._call_llm(REQUIREMENTS_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_json(raw) if raw else None

        if parsed:
            result = parsed
            result["_source"] = "llm"
        else:
            result = dict(MOCK_REQUIREMENTS_RESPONSE)
            result["_source"] = "mock"

        result["_latency_ms"] = round((time.time() - start) * 1000)
        return result

    def generate_blueprint(self, title: str, problem: str, requirements: str) -> Dict[str, Any]:
        """Generate a workflow blueprint from requirements."""
        start = time.time()
        user_prompt = get_blueprint_prompt(title, problem, requirements)
        raw = self._call_llm(BLUEPRINT_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_json(raw) if raw else None

        if parsed:
            result = parsed
            result["_source"] = "llm"
        else:
            result = dict(MOCK_BLUEPRINT_RESPONSE)
            result["_source"] = "mock"

        result["_latency_ms"] = round((time.time() - start) * 1000)
        return result

    def generate_executive_summary(self, project_name: str, metrics: str) -> Dict[str, Any]:
        """Generate an executive summary narrative from raw metrics."""
        start = time.time()
        user_prompt = get_summary_prompt(project_name, metrics)
        raw = self._call_llm(SUMMARY_SYSTEM_PROMPT, user_prompt, max_tokens=600)

        if raw:
            result = {"summary": raw, "_source": "llm"}
        else:
            result = {
                "summary": (
                    f"**{project_name}** has been deployed and is delivering measurable impact. "
                    "The automation reduced manual processing time by 75%, freeing up team capacity "
                    "for higher-value activities. Early adoption metrics show strong engagement "
                    "across the target user group.\n\n"
                    "Next steps include expanding to additional teams and refining the AI model "
                    "based on user feedback collected during the pilot phase."
                ),
                "_source": "mock",
            }

        result["_latency_ms"] = round((time.time() - start) * 1000)
        return result

    def check_health(self) -> Dict[str, Any]:
        """Ping HF API with a minimal request to check connection health."""
        if not self.hf_token:
            return {
                "status": "no_token",
                "model": self.model,
                "message": "No HF_TOKEN configured — using mock responses",
                "latency_ms": None,
            }

        try:
            start = time.time()
            resp = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 5,
                },
                timeout=15,
            )
            latency = round((time.time() - start) * 1000)

            if resp.status_code == 200:
                return {"status": "connected", "model": self.model,
                        "message": "LLM is responding", "latency_ms": latency}
            else:
                return {"status": "disconnected", "model": self.model,
                        "message": f"API returned {resp.status_code}: {resp.text[:120]}",
                        "latency_ms": latency}
        except Exception as exc:
            return {"status": "disconnected", "model": self.model,
                    "message": str(exc)[:150], "latency_ms": None}
