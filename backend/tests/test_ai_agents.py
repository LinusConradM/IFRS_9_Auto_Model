import json
import os

import pytest

import anthropic
import openai

from services.ai_agents.interface import AIAgentInterface, ValidationResult
from services.ai_agents.claude_agent import ClaudeAgent
from services.ai_agents.codex_agent import CodexAgent
from services.ai_agents.factory import create_ai_agent


class DummyResponse:
    def __init__(self, completion=None, text=None):
        self.completion = completion
        if text is not None:
            self.choices = [type("Choice", (), {"text": text})]


class DummyCompletions:
    def __init__(self, completion):
        self._completion = completion

    def create(self, *args, **kwargs):
        return DummyResponse(completion=self._completion)


class DummyClient:
    def __init__(self, completion):
        self.completions = DummyCompletions(completion=completion)


def test_ai_agent_interface_is_abstract():
    with pytest.raises(TypeError):
        AIAgentInterface()


def test_claude_agent_parse_form_data(monkeypatch):
    dummy_output = {"key": "value"}
    monkeypatch.setenv("CLAUDE_API_KEY", "test")
    monkeypatch.setattr(anthropic, "Client", lambda api_key: DummyClient(json.dumps(dummy_output)))
    agent = ClaudeAgent()
    result = agent.parse_form_data({"a": 1})
    assert result == dummy_output


def test_claude_agent_validate_form_fields(monkeypatch):
    dummy_errors = ["err1", "err2"]
    monkeypatch.setenv("CLAUDE_API_KEY", "test")
    monkeypatch.setattr(anthropic, "Client", lambda api_key: DummyClient(json.dumps(dummy_errors)))
    agent = ClaudeAgent()
    vr = agent.validate_form_fields({"a": 1})
    assert isinstance(vr, ValidationResult)
    assert not vr.is_valid
    assert vr.errors == dummy_errors


def test_claude_agent_suggest_corrections(monkeypatch):
    dummy_suggestions = ["fix1", "fix2"]
    monkeypatch.setenv("CLAUDE_API_KEY", "test")
    monkeypatch.setattr(anthropic, "Client", lambda api_key: DummyClient(json.dumps(dummy_suggestions)))
    agent = ClaudeAgent()
    suggestions = agent.suggest_corrections(["err"])
    assert suggestions == dummy_suggestions


def test_claude_agent_generate_test_cases(monkeypatch):
    dummy_tests = ["test1", "test2"]
    monkeypatch.setenv("CLAUDE_API_KEY", "test")
    monkeypatch.setattr(anthropic, "Client", lambda api_key: DummyClient(json.dumps(dummy_tests)))
    agent = ClaudeAgent()
    tests_out = agent.generate_test_cases("def foo(): pass")
    assert tests_out == dummy_tests


def test_codex_agent_parse_form_data(monkeypatch):
    dummy_output = {"k": "v"}
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(openai.Completion, "create", lambda **kwargs: DummyResponse(text=json.dumps(dummy_output)))
    agent = CodexAgent()
    result = agent.parse_form_data({"x": 2})
    assert result == dummy_output


def test_codex_agent_validate_form_fields(monkeypatch):
    dummy_errors = ["e1", "e2"]
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(openai.Completion, "create", lambda **kwargs: DummyResponse(text=json.dumps(dummy_errors)))
    agent = CodexAgent()
    vr = agent.validate_form_fields({"x": 2})
    assert isinstance(vr, ValidationResult)
    assert not vr.is_valid
    assert vr.errors == dummy_errors


def test_codex_agent_suggest_corrections(monkeypatch):
    dummy_suggestions = ["s1", "s2"]
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(openai.Completion, "create", lambda **kwargs: DummyResponse(text=json.dumps(dummy_suggestions)))
    agent = CodexAgent()
    suggestions = agent.suggest_corrections(["e"])
    assert suggestions == dummy_suggestions


def test_codex_agent_generate_test_cases(monkeypatch):
    dummy_tests = ["t1", "t2"]
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(openai.Completion, "create", lambda **kwargs: DummyResponse(text=json.dumps(dummy_tests)))
    agent = CodexAgent()
    tests_out = agent.generate_test_cases("def bar(): pass")
    assert tests_out == dummy_tests


def test_create_ai_agent_factory(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    ca = create_ai_agent("claude")
    assert isinstance(ca, ClaudeAgent)
    oa = create_ai_agent("codex")
    assert isinstance(oa, CodexAgent)
    oa2 = create_ai_agent("openai")
    assert isinstance(oa2, CodexAgent)
    with pytest.raises(ValueError):
        create_ai_agent("unknown")