import argparse
import json
from pathlib import Path
import sys
from .backend import CVC5Backend
from .certificates import LeanVerifier
from .diagnose import diagnose
from .ir import Unsupported, parse


def main():
    parser = argparse.ArgumentParser(description="Diagnose an exact real polynomial claim and check Lean certificates")
    parser.add_argument("input", help="JSON problem, or '-' for stdin")
    parser.add_argument("--out", default="artifacts", help="Certificate directory")
    parser.add_argument("--lake", default="lake", help="Lake executable")
    parser.add_argument("--project", default=str(Path.cwd()), help="Lean project directory (default: current directory)")
    parser.add_argument("--solver-only", action="store_true", help="Explicitly skip Lean verification")
    parser.add_argument("--timeout-ms", type=int, default=5000)
    args = parser.parse_args()
    if args.timeout_ms <= 0: parser.error("--timeout-ms must be positive")
    try:
        data = json.loads(sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8"))
        p = parse(data)
        verifier = None if args.solver_only else LeanVerifier(args.project, args.out, args.lake)
        result = diagnose(p, CVC5Backend(args.timeout_ms), verifier)
    except (Unsupported, json.JSONDecodeError, RecursionError) as e:
        result = {"schema_version": 1, "classification": "unsupported", "reason": str(e)}
    except (OSError, ImportError) as e:
        result = {"schema_version": 1, "classification": "unknown", "reason": str(e)}
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    return 2 if result["classification"] in {"unsupported", "unknown"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
