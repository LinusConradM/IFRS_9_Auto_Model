import json
import os

import openai

from services.ai_agents.interface import AIAgentInterface, ValidationResult


class CodexAgent(AIAgentInterface):
    """
    AI agent implementation using the OpenAI Codex API.
    """

    def __init__(self, model: str = "code-davinci-002"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable not set")
        openai.api_key = api_key
        self.model = model

    def parse_form_data(self, input_data: dict) -> dict:
        prompt = (
            f"Parse the following form data into JSON format without additional commentary:\n{input_data}\n"
        )
        response = openai.Completion.create(
            engine=self.model,
            prompt=prompt,
            max_tokens=500,
            temperature=0,
        )
        text = response.choices[0].text.strip()
        return json.loads(text)

    def validate_form_fields(self, form_data: dict) -> ValidationResult:
        prompt = (
            f"Validate the following form data and return a JSON list of error messages (empty if valid):\n{form_data}\n"
        )
        response = openai.Completion.create(
            engine=self.model,
            prompt=prompt,
            max_tokens=300,
            temperature=0,
        )
        errors = json.loads(response.choices[0].text.strip())
        is_valid = not bool(errors)
        return ValidationResult(is_valid=is_valid, errors=errors)

    def suggest_corrections(self, validation_errors: list) -> list:
        prompt = (
            f"Based on these validation errors, suggest corrections as a JSON list of suggestions:\n{validation_errors}\n"
        )
        response = openai.Completion.create(
            engine=self.model,
            prompt=prompt,
            max_tokens=300,
            temperature=0,
        )
        return json.loads(response.choices[0].text.strip())

    def generate_test_cases(self, function_signature: str) -> list:
        prompt = (
            f"Generate test cases for the following function signature as a JSON list:\n{function_signature}\n"
        )
        response = openai.Completion.create(
            engine=self.model,
            prompt=prompt,
            max_tokens=500,
            temperature=0,
        )
        return json.loads(response.choices[0].text.strip())