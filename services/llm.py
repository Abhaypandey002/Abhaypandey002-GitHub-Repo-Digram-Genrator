from __future__ import annotations

import json
import logging
from typing import List

import requests

from core.config import get_settings

LOGGER = logging.getLogger(__name__)


class LocalLLM:
    def __init__(self) -> None:
        settings = get_settings()
        self.endpoint = settings.ollama_endpoint.rstrip("/") + "/api/generate"
        self.model = settings.llm_model

    def _generate(self, prompt: str) -> str | None:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 256
            }
        }
        try:
            response = requests.post(self.endpoint, json=payload, timeout=30)
        except requests.RequestException as exc:
            LOGGER.warning("LLM unavailable: %s", exc)
            return None
        if response.status_code != 200:
            LOGGER.warning("LLM responded with status %s", response.status_code)
            return None
        try:
            data = response.json()
        except json.JSONDecodeError:
            LOGGER.warning("Failed to decode LLM response")
            return None
        return data.get("response")

    def summarize_repo(self, context: str) -> List[str]:
        # prompt = (
        #     "Summarise the following repository context into concise bullet points for a newcomer. "
        #     "Focus on overall purpose, main components, and how to start exploring.\n" + context
        # )

        prompt = (
            "You are a terse technical writer. Output ONLY 3-5 markdown bullets.\n"
            "- Audience: newcomer engineer.\n"
            "- Include: project purpose, main components, and first file(s) to open.\n"
            "- Exclude: moral judgments, refusals, safety warnings, speculation.\n"
            "- Style: factual, neutral, no prefaces, no closing lines.\n\n"
            f"Context:\n{context}\n\nBullets:"
        )


        response = self._generate(prompt)
        if not response:
            return []
        bullets = [line.strip("- ") for line in response.splitlines() if line.strip()]
        return bullets[:5]

    def summarize_module(self, module: str, context: str) -> str | None:
        # prompt = (
        #     f"Given the following context about module {module}, explain briefly why it is important "
        #     "and what responsibilities it has.\n" + context
        # )

        prompt = (
            "You write one-sentence engineering notes.\n"
            f"Task: In 1-2 sentences, say why `{module}` matters and its responsibilities.\n"
            "- Exclude: moral judgments, refusals, safety warnings.\n"
            "- If context is thin, say 'Entry point' or 'Utility module' succinctly.\n\n"
            f"Context:\n{context}\n\nNote:"
        )

        response = self._generate(prompt)
        if not response:
            return None
        return response.strip()
