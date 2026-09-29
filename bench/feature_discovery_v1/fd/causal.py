"""Evidence-class assignment. CAUSAL_IDENTIFIED is unreachable without an explicit identified-design object."""
DESIGNS = {"randomised_intervention", "natural_experiment", "valid_instrument"}


def classify(stable, inv_p, inv_sign_agree, icp_includes, mechanism_documented=False, design=None, alpha=0.05):
    """stable: held-out stable (predictive). inv_p/inv_sign_agree: Cochran-Q p and share of environments with the pooled sign.
    icp_includes: variable(s) survive ICP-lite intersection. design: dict(kind=..., effect_p=..., checks_passed=bool, replicated=bool) or None.
    A design claim needs p<0.01 AND replication across independent environments (same sign in >=7/8)."""
    if design is not None:
        if (design.get("kind") in DESIGNS and design.get("checks_passed") and design.get("effect_p", 1.0) < 0.01
                and design.get("replicated", False)):
            return "CAUSAL_IDENTIFIED"
    if not stable:
        return "NONE"
    if inv_p < alpha or inv_sign_agree < 1.0:
        return "PREDICTIVE"
    if icp_includes and mechanism_documented:
        return "CAUSAL_HYPOTHESIS"
    return "INVARIANT_ASSOCIATION"
