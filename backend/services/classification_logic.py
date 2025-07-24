"""
IFRS 9 classification logic based on SPPI test and business model.
"""
from typing import Dict, Any, List


def classify_instrument(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine measurement category:
    - Amortized Cost: SPPI is True and business_model == 'Hold to collect'
    - FVOCI: SPPI is True and business_model == 'Hold to collect and sell'
    - FVTPL: otherwise
    Returns a dict with 'category' and 'reasons'.
    """
    reasons: List[str] = []

    sppi = bool(form_data.get("sppi"))
    business_model = form_data.get("business_model")

    if sppi:
        reasons.append("SPPI test passed")
        if business_model == "Hold to collect":
            category = "Amortized Cost"
            reasons.append("Business model is hold to collect")
        elif business_model == "Hold to collect and sell":
            category = "FVOCI"
            reasons.append("Business model is hold to collect and sell")
        else:
            category = "FVTPL"
            reasons.append(f"Business model '{business_model}' requires fair value through profit or loss")
    else:
        category = "FVTPL"
        reasons.append("SPPI test failed")

    return {"category": category, "reasons": reasons}