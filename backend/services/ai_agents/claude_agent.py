import json
import os

import anthropic

from services.ai_agents.interface import AIAgentInterface, ValidationResult


class ClaudeAgent(AIAgentInterface):
    """
    AI agent implementation using the Anthropic Claude API.
    """

    def __init__(self, model: str = "claude-2"):
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise EnvironmentError("CLAUDE_API_KEY environment variable not set")
        self.client = anthropic.Client(api_key=api_key)
        self.model = model

    def parse_form_data(self, input_data: dict) -> dict:
        prompt = (
            anthropic.HUMAN_PROMPT
            + f"Parse the following form data into JSON format without additional commentary:\n{input_data}\n"
            + anthropic.AI_PROMPT
        )
        response = self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens_to_sample=500,
        )
        return json.loads(response.completion)

    def validate_form_fields(self, form_data: dict) -> ValidationResult:
        prompt = (
            anthropic.HUMAN_PROMPT
            + f"Validate the following form data and return a JSON list of error messages (empty if valid):\n{form_data}\n"
            + anthropic.AI_PROMPT
        )
        response = self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens_to_sample=300,
        )
        errors = json.loads(response.completion)
        is_valid = not bool(errors)
        return ValidationResult(is_valid=is_valid, errors=errors)

    def suggest_corrections(self, validation_errors: list) -> list:
        prompt = (
            anthropic.HUMAN_PROMPT
            + f"Based on these validation errors, suggest corrections as a JSON list of suggestions:\n{validation_errors}\n"
            + anthropic.AI_PROMPT
        )
        response = self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens_to_sample=300,
        )
        return json.loads(response.completion)

    def generate_test_cases(self, function_signature: str) -> list:
        prompt = (
            anthropic.HUMAN_PROMPT
            + f"Generate test cases for the following function signature as a JSON list:\n{function_signature}\n"
            + anthropic.AI_PROMPT
        )
        response = self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens_to_sample=500,
        )
        return json.loads(response.completion)