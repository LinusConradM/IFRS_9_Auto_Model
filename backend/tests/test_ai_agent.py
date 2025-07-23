import os
import json

import pytest
import requests

from services.ai_agent import (
    AIAgentFactory,
    ClaudeAgent,
    CodexAgent,
    ValidationResult,
)


class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"Status code: {self.status_code}")


def test_factory_claude_preferred(monkeypatch):
    monkeypatch.setenv('AI_AGENT', 'claude')
    monkeypatch.setenv('CLAUDE_API_KEY', 'key_c')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    agent = AIAgentFactory.create_agent()
    assert isinstance(agent, ClaudeAgent)


def test_factory_claude_fallback_to_codex(monkeypatch):
    monkeypatch.setenv('AI_AGENT', 'claude')
    monkeypatch.delenv('CLAUDE_API_KEY', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'key_o')
    agent = AIAgentFactory.create_agent()
    assert isinstance(agent, CodexAgent)


def test_factory_codex_preferred(monkeypatch):
    monkeypatch.setenv('AI_AGENT', 'codex')
    monkeypatch.setenv('OPENAI_API_KEY', 'key_o')
    monkeypatch.delenv('CLAUDE_API_KEY', raising=False)
    agent = AIAgentFactory.create_agent()
    assert isinstance(agent, CodexAgent)


def test_factory_codex_fallback_to_claude(monkeypatch):
    monkeypatch.setenv('AI_AGENT', 'codex')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('CLAUDE_API_KEY', 'key_c')
    agent = AIAgentFactory.create_agent()
    assert isinstance(agent, ClaudeAgent)


def test_factory_default_to_codex(monkeypatch):
    monkeypatch.delenv('AI_AGENT', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'key_o')
    monkeypatch.delenv('CLAUDE_API_KEY', raising=False)
    agent = AIAgentFactory.create_agent()
    assert isinstance(agent, CodexAgent)


def test_factory_default_to_claude(monkeypatch):
    monkeypatch.delenv('AI_AGENT', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('CLAUDE_API_KEY', 'key_c')
    agent = AIAgentFactory.create_agent()
    assert isinstance(agent, ClaudeAgent)


def test_factory_error_when_no_keys(monkeypatch):
    monkeypatch.delenv('AI_AGENT', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('CLAUDE_API_KEY', raising=False)
    with pytest.raises(RuntimeError):
        AIAgentFactory.create_agent()


@pytest.mark.parametrize('agent_cls, api_key_name', [
    (ClaudeAgent, 'CLAUDE_API_KEY'),
    (CodexAgent, 'OPENAI_API_KEY'),
])
def test_timeout_raises(monkeypatch, agent_cls, api_key_name):
    monkeypatch.setenv(api_key_name, 'key')
    def raise_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout

    monkeypatch.setattr(requests, 'post', raise_timeout)
    agent = agent_cls(os.getenv(api_key_name))
    with pytest.raises(TimeoutError):
        agent.parse_form_data({})


def test_claude_parse_and_validate(monkeypatch):
    # Test parse_form_data
    resp_data = {'completion': '{"x":1}'}
    monkeypatch.setenv('CLAUDE_API_KEY', 'key')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyResponse(resp_data))
    agent = ClaudeAgent('key')
    result = agent.parse_form_data({'a': 1})
    assert result == {'x': 1}

    # Test validate_form_fields with valid JSON
    resp_data = {'completion': '[{"field":"a","issue":"error"}]'}
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyResponse(resp_data))
    vr = agent.validate_form_fields({'a': 1})
    assert isinstance(vr, ValidationResult)
    assert not vr.is_valid
    assert vr.errors == [{'field': 'a', 'issue': 'error'}]

    # Test malformed response
    resp_data = {'completion': 'not-json'}
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyResponse(resp_data))
    vr = agent.validate_form_fields({'a': 1})
    assert not vr.is_valid
    assert vr.errors == [{'field': None, 'issue': 'Malformed response'}]


def test_codex_parse_and_validate(monkeypatch):
    # Test parse_form_data
    content = '{"y":2}'
    resp = {'choices': [{'message': {'content': content}}]}
    monkeypatch.setenv('OPENAI_API_KEY', 'key')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyResponse(resp))
    agent = CodexAgent('key')
    result = agent.parse_form_data({'b': 2})
    assert result == {'y': 2}

    # Test validate_form_fields with valid JSON
    valid_json = '[{"field":"b","issue":"issue"}]'
    resp = {'choices': [{'message': {'content': valid_json}}]}
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyResponse(resp))
    vr = agent.validate_form_fields({'b': 2})
    assert isinstance(vr, ValidationResult)
    assert not vr.is_valid
    assert vr.errors == [{'field': 'b', 'issue': 'issue'}]

    # Test malformed response
    resp = {'choices': [{'message': {'content': 'invalid'}}]}
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: DummyResponse(resp))
    vr = agent.validate_form_fields({'b': 2})
    assert not vr.is_valid
    assert vr.errors == [{'field': None, 'issue': 'Malformed response'}]