"""Untrusted discovery only. The native Lean frontend checks its own expressions."""
import json
import sys
from .backend import CVC5Backend
from .diagnose import diagnose
from .ir import Unsupported, parse


def main():
    try:
        request = json.load(sys.stdin)
        timeout = request.get("timeout_ms", 2000)
        if type(timeout) is not int or not 1 <= timeout <= 10000:
            raise Unsupported("timeout_ms must be an integer from 1 to 10000")
        result = diagnose(parse(request["problem"]), CVC5Backend(timeout))
    except (Unsupported, ValueError, KeyError, RecursionError) as error:
        result = {"classification": "unsupported", "reason": str(error)}
    except Exception as error:
        result = {"classification": "unknown", "reason": str(error)}
    print(json.dumps(result, default=str, ensure_ascii=True))


if __name__ == "__main__": main()
