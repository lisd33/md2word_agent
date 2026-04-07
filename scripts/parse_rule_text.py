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

from md2word_agent.parser import RuleParser  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse natural-language template rules into TemplateRequirement JSON.")
    parser.add_argument("input", help="Path to a rule text or markdown file")
    parser.add_argument("--document-family", default="unknown", help="Document family label to attach to the parsed requirement")
    parser.add_argument("--show-evidence", action="store_true", help="Also print extraction evidence")
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    result = RuleParser().parse(text, document_family=args.document_family)
    print(json.dumps(result.requirement.to_dict(), ensure_ascii=False, indent=2))
    if args.show_evidence:
        print("\n# Evidence")
        print(json.dumps(result.evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
