#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from md2word_agent.api import make_api_server  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local md2word_agent HTTP API server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--env-file", default=str(ROOT / ".env"), help="Path to the .env file containing API settings")
    args = parser.parse_args()

    server = make_api_server(host=args.host, port=args.port, env_file=args.env_file)
    print(f"md2word_agent API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
