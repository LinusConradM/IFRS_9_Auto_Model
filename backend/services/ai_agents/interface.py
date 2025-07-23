import abc
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """
    Represents the result of validating form fields.
    """
    is_valid: bool
    errors: List[str]


class AIAgentInterface(abc.ABC):
    """
    Abstract interface for AI agents to parse data, validate fields,
    suggest corrections, and generate test cases.
    """

    @abc.abstractmethod
    def parse_form_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw form input data into a structured dictionary.

        :param input_data: Raw input data from a form.
        :return: Parsed form data as a dictionary.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def validate_form_fields(self, form_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate the parsed form data fields.

        :param form_data: Parsed form data.
        :return: ValidationResult indicating if data is valid and any errors.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def suggest_corrections(self, validation_errors: List[str]) -> List[str]:
        """
        Suggest corrections based on validation errors.

        :param validation_errors: List of validation error messages.
        :return: Suggestions to correct the errors.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def generate_test_cases(self, function_signature: str) -> List[str]:
        """
        Generate test cases for a given function signature.

        :param function_signature: The signature of the function to test.
        :return: A list of test case descriptions or inputs.
        """
        raise NotImplementedError