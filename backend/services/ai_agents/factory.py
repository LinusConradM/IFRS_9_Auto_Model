from services.ai_agents.claude_agent import ClaudeAgent
from services.ai_agents.codex_agent import CodexAgent
from services.ai_agents.interface import AIAgentInterface


def create_ai_agent(agent_type: str) -> AIAgentInterface:
    """
    Factory for creating AI agent instances based on the given type.

    :param agent_type: Identifier for the agent ('claude' or 'codex').
    :return: Instance of AIAgentInterface.
    :raises ValueError: If an unsupported agent_type is provided.
    """
    key = agent_type.strip().lower()
    if key == "claude":
        return ClaudeAgent()
    if key in ("codex", "openai"):  # alias for Codex
        return CodexAgent()
    raise ValueError(f"Unsupported AI agent type: {agent_type}")