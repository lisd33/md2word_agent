#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from md2word_agent.llm import create_json_client, resolve_provider  # noqa: E402
from md2word_agent.parser import TemplateFileParser  # noqa: E402
from md2word_agent.planner import TemplateUnderstandingPlanner  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a docx template with candidate extraction plus API-based template understanding.")
    parser.add_argument("input", help="Path to a .docx template file")
    parser.add_argument("--document-family", default="unknown", help="Document family label to attach to the parsed requirement")
    parser.add_argument("--rules", help="Optional path to rule text / author guidelines to provide as extra context")
    parser.add_argument("--show-candidates", action="store_true", help="Also print the extracted heading candidates before final filtering")
    parser.add_argument("--env-file", default=str(ROOT / ".env"), help="Path to the .env file containing API settings")
    parser.add_argument("--provider", choices=["moonshot", "minimax"], help="Override the provider in .env for this run")
    args = parser.parse_args()

    provider = resolve_provider(args.env_file, args.provider)
    client = create_json_client(env_path=args.env_file, provider=provider)
    planner = TemplateUnderstandingPlanner(client)
    file_parser = TemplateFileParser(understanding_planner=planner)

    rule_text = None
    if args.rules:
        rule_text = Path(args.rules).read_text(encoding="utf-8")

    result = file_parser.parse(
        Path(args.input).read_bytes(),
        document_family=args.document_family,
        rule_text=rule_text,
    )

    if args.show_candidates:
        print("# Candidates")
        print(json.dumps([candidate.to_dict() for candidate in result.candidates], ensure_ascii=False, indent=2))
        print("\n# Requirement")
    print(f"# Provider: {provider}")
    print(json.dumps(result.requirement.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
