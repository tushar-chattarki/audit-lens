from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.extraction.extraction_router import extract_document


def main() -> None:

    if len(sys.argv) not in {2, 3}:
        print(
            "Usage:\n"
            "python -m backend.extraction.run_extr "
            "<document> [job_id]"
        )
        raise SystemExit(1)

    input_file = Path(sys.argv[1])

    # Use a simple default for local testing.
    job_id = (
        sys.argv[2]
        if len(sys.argv) == 3
        else "local_test"
    )

    try:
        result = extract_document(
            input_file,
            job_id=job_id,
        )

    except Exception as exc:
        print("\n=== EXTRACTION FAILED ===")
        print(f"File: {input_file}")
        print(f"Error: {exc}")
        raise SystemExit(1)

    output_file = (
        input_file.parent
        / f"{input_file.stem}_canonical.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result["canonical"],
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    print("\n=== EXTRACTION SUCCESSFUL ===")
    print(f"Input:       {input_file}")
    print(f"Source type: {result['source_type']}")
    print(f"Job ID:      {job_id}")
    print(f"Output:      {output_file}")


if __name__ == "__main__":
    main()