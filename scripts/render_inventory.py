from __future__ import annotations

import json
from datetime import datetime, timezone


def main() -> None:
    payload = {
        "project": "infra-reporting-starter",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resources": [
            {
                "type": "aws_s3_bucket",
                "name": "project_artifacts",
                "purpose": "placeholder for analytics or reporting artifacts",
            }
        ],
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

