def summarize_member5_results(results):

    total_rules = len(results)

    pass_count = sum(
        1 for result in results
        if result["status"] == "PASS"
    )

    fail_count = sum(
        1 for result in results
        if result["status"] == "FAIL"
    )

    unusual_count = sum(
        1 for result in results
        if result["status"] == "UNUSUAL"
    )

    review_count = sum(
        1 for result in results
        if result["status"] == "REVIEW"
    )

    consistency_results = [
        result for result in results
        if result["category"] == "consistency"
    ]

    prior_year_results = [
        result for result in results
        if result["category"] == "prior_year"
    ]

    return {
        "member": "Member 5",
        "module": "Consistency and Prior-Year Analysis",

        "summary": {
            "total_rules": total_rules,
            "pass": pass_count,
            "fail": fail_count,
            "unusual": unusual_count,
            "review": review_count
        },

        "consistency": {
            "total_rules": len(consistency_results),
            "pass": sum(
                1 for result in consistency_results
                if result["status"] == "PASS"
            ),
            "fail": sum(
                1 for result in consistency_results
                if result["status"] == "FAIL"
            ),
            "unusual": sum(
                1 for result in consistency_results
                if result["status"] == "UNUSUAL"
            ),
            "review": sum(
                1 for result in consistency_results
                if result["status"] == "REVIEW"
            )
        },

        "prior_year": {
            "total_rules": len(prior_year_results),
            "pass": sum(
                1 for result in prior_year_results
                if result["status"] == "PASS"
            ),
            "fail": sum(
                1 for result in prior_year_results
                if result["status"] == "FAIL"
            ),
            "unusual": sum(
                1 for result in prior_year_results
                if result["status"] == "UNUSUAL"
            ),
            "review": sum(
                1 for result in prior_year_results
                if result["status"] == "REVIEW"
            )
        },

        "findings": results
    }