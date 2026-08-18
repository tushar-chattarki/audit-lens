def create_finding(
    rule_id,
    category,
    status,
    severity,
    message,
    values,
    evidence
):
    return {
        "rule_id": rule_id,
        "category": category,
        "status": status,
        "severity": severity,
        "message": message,
        "values": values,
        "evidence": evidence
    }