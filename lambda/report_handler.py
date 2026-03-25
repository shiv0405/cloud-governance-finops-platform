from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def lambda_handler(event: dict, context: object) -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_bucket": os.environ.get("REPORT_BUCKET", ""),
        "report_prefix": os.environ.get("REPORT_PREFIX", "reports"),
        "athena_workgroup": os.environ.get("ATHENA_WORKGROUP", ""),
        "glue_database": os.environ.get("GLUE_DATABASE", ""),
        "invocation_source": event.get("source", "manual"),
        "status": "ok",
        "note": "Replace this starter with real collection, normalization, and persistence logic.",
    }


if __name__ == "__main__":
    print(json.dumps(lambda_handler({"source": "local"}, None), indent=2))
