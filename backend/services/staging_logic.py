"""
IFRS 9 Stage evaluation logic based on DPD, SICR, and default flags.
"""
from typing import Dict, Any, List


def evaluate_staging_logic(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine IFRS 9 stage:
    - Stage 3: default_flag is True
    - Stage 2: DPD > 30 or SICR flag is True
    - Stage 1: otherwise
    Returns a dict with 'stage' (int) and 'reasons' (List[str]).
    """
    reasons: List[str] = []

    default_flag = bool(form_data.get("default_flag"))
    try:
        dpd_val = int(form_data.get("dpd") or 0)
    except (TypeError, ValueError):
        dpd_val = 0
        reasons.append(f"Invalid DPD value '{form_data.get('dpd')}', defaulted to 0")

    sicr_flag = bool(form_data.get("sicr"))

    if default_flag:
        reasons.append("Default flag is set, asset is credit impaired")
        stage = 3
    elif dpd_val > 30:
        reasons.append(f"DPD of {dpd_val} days exceeds 30-day threshold")
        stage = 2
    elif sicr_flag:
        reasons.append("Significant increase in credit risk detected")
        stage = 2
    else:
        reasons.append("No significant increase in credit risk or default observed")
        stage = 1

    return {"stage": stage, "reasons": reasons}