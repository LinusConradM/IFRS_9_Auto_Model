import os
import json
import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Logic modules implementing IFRS 9 staging, classification, and explainability
from .staging_logic import evaluate_staging_logic
from .classification_logic import classify_instrument
from .explainability import generate_explainability_trace


@dataclass
class ValidationResult:
    """
    Represents the result of validating form data, including validity flag and list of errors.
    """
    is_valid: bool
    errors: List[Dict[str, Any]]


class AIAgentInterface(ABC):
    """
    Abstract base class defining the interface for AI agents.
    """

    @abstractmethod
    def parse_form_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize structured data from semi-structured input.
        """
        pass

    @abstractmethod
    def validate_form_fields(self, form_data: Dict[str, Any]) -> ValidationResult:
        """
        Apply validations for IFRS 9 fields and return ValidationResult.
        """
        pass

    @abstractmethod
    def suggest_corrections(self, validation_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Offer fixes or enhancements based on validation errors.
        """
        pass

    @abstractmethod
    def generate_test_cases(self, function_signature: str) -> List[str]:
        """
        Generate unit test case suggestions for a given function signature.
        """
        pass

    @abstractmethod
    def evaluate_staging_logic(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent assessment of IFRS 9 Stage using DPD, SICR, and default flags.
        """
        pass

    @abstractmethod
    def classify_instrument(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine measurement category per SPPI and business model tests.
        """
        pass

    @abstractmethod
    def generate_explainability_trace(self, form_data: Dict[str, Any]) -> str:
        """
        Return interpretable summary explaining staging and classification decisions.
        """
        pass


class ClaudeAgent(AIAgentInterface):
    """
    Concrete AI agent implementation using Anthropic Claude API.
    """

    def __init__(self, api_key: str, model: str = "claude-v1"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/complete"

    def _call_api(self, prompt: str) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
        }
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("Claude API request timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Claude API request failed: {e}")
        return response.json()

    def parse_form_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Extract and normalize structured data from the following semi-structured document input:\n"
            f"{input_data}\nReturn a JSON object."
        )
        result = self._call_api(prompt)
        raw = result.get("completion", "")
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    def validate_form_fields(self, form_data: Dict[str, Any]) -> ValidationResult:
        prompt = (
            f"Validate the following IFRS 9 form data and list missing or incorrect fields:\n"
            f"{form_data}\nReturn a JSON array of error objects with 'field' and 'issue'."
        )
        result = self._call_api(prompt)
        errors_str = result.get("completion", "[]")
        try:
            errors = json.loads(errors_str)
        except (json.JSONDecodeError, TypeError):
            errors = [{"field": None, "issue": "Malformed response"}]
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def suggest_corrections(self, validation_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prompt = (
            f"Suggest corrections for the following validation errors:\n"
            f"{validation_errors}\nReturn a JSON array of suggestions."
        )
        result = self._call_api(prompt)
        suggestions_str = result.get("completion", "[]")
        try:
            suggestions = json.loads(suggestions_str)
        except (json.JSONDecodeError, TypeError):
            suggestions = []
        return suggestions

    def generate_test_cases(self, function_signature: str) -> List[str]:
        prompt = (
            f"Generate unit test cases for the following function signature and behavior:\n"
            f"{function_signature}"
        )
        result = self._call_api(prompt)
        tests = result.get("completion", "")
        return tests.splitlines()

    def evaluate_staging_logic(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        return evaluate_staging_logic(form_data)

    def classify_instrument(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        return classify_instrument(form_data)

    def generate_explainability_trace(self, form_data: Dict[str, Any]) -> str:
        return generate_explainability_trace(form_data)


class CodexAgent(AIAgentInterface):
    """
    Concrete AI agent implementation using OpenAI Codex/GPT API.
    """

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def _call_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise TimeoutError("OpenAI API request timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")
        return response.json()

    def parse_form_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You are an assistant that extracts structured data from semi-structured documents."},
            {"role": "user", "content": f"Extract JSON from this input: {input_data}"},
        ]
        result = self._call_api(messages)
        content = result.get("choices", [])[0].get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {}

    def validate_form_fields(self, form_data: Dict[str, Any]) -> ValidationResult:
        messages = [
            {"role": "system", "content": "You validate IFRS 9 form data. Output JSON array of error objects."},
            {"role": "user", "content": f"Validate this data: {form_data}"},
        ]
        result = self._call_api(messages)
        content = result.get("choices", [])[0].get("message", {}).get("content", "")
        try:
            errors = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            errors = [{"field": None, "issue": "Malformed response"}]
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def suggest_corrections(self, validation_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        messages = [
            {"role": "system", "content": "You suggest corrections for validation errors. Output JSON array."},
            {"role": "user", "content": f"Suggest corrections for these errors: {validation_errors}"},
        ]
        result = self._call_api(messages)
        content = result.get("choices", [])[0].get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return []

    def generate_test_cases(self, function_signature: str) -> List[str]:
        messages = [
            {"role": "system", "content": "You generate unit test cases for Python functions."},
            {"role": "user", "content": f"Generate test cases for this function signature: {function_signature}"},
        ]
        result = self._call_api(messages)
        content = result.get("choices", [])[0].get("message", {}).get("content", "")
        return content.splitlines()

    def evaluate_staging_logic(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        return evaluate_staging_logic(form_data)

    def classify_instrument(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        return classify_instrument(form_data)

    def generate_explainability_trace(self, form_data: Dict[str, Any]) -> str:
        return generate_explainability_trace(form_data)


class AIAgentFactory:
    """
    Factory for creating AI agents based on environment configuration and available API keys.
    """

    @staticmethod
    def create_agent() -> AIAgentInterface:
        requested = os.getenv("AI_AGENT", "").lower()
        claude_key = os.getenv("CLAUDE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if requested == "claude":
            if claude_key:
                return ClaudeAgent(claude_key)
            if openai_key:
                logger.warning("CLAUDE_API_KEY not set, falling back to CodexAgent")
                return CodexAgent(openai_key)
            raise RuntimeError("No API key configured for Claude or OpenAI Codex")

        if requested in ("codex", "openai"):
            if openai_key:
                return CodexAgent(openai_key)
            if claude_key:
                logger.warning("OPENAI_API_KEY not set, falling back to ClaudeAgent")
                return ClaudeAgent(claude_key)
            raise RuntimeError("No API key configured for OpenAI Codex or Claude")

        # Default selection based on available keys
        if openai_key:
            return CodexAgent(openai_key)
        if claude_key:
            return ClaudeAgent(claude_key)

        raise RuntimeError(
            "AI_AGENT not set and no API keys found; cannot create AI agent"
        )