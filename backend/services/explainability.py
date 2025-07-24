"""
Generate explainability trace combining staging and classification decisions.
"""
from typing import Dict, Any

from .staging_logic import evaluate_staging_logic
from .classification_logic import classify_instrument


def generate_explainability_trace(form_data: Dict[str, Any]) -> str:
    """
    Return a human-readable summary explaining staging and classification reasons.
    """
    staging = evaluate_staging_logic(form_data)
    classification = classify_instrument(form_data)

    lines = [f"Stage Evaluation: Assigned Stage {staging['stage']} because:"]
    for reason in staging['reasons']:
        lines.append(f"- {reason}")
    lines.append(f"Classification: Assigned {classification['category']} category because:")
    for reason in classification['reasons']:
        lines.append(f"- {reason}")

    return "\n".join(lines)