# API Guide

## Start Server

```bash
cd /root/public/lzh/design-as-code/md2word_agent
python scripts/run_api_server.py --host 127.0.0.1 --port 8000
```

## Health Check

```bash
curl http://127.0.0.1:8000/health
```

## Provider Check

```bash
curl http://127.0.0.1:8000/providers
```

## Rule Text Parsing

Endpoint:

- `POST /api/v1/parse/rules`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/parse/rules \
  -H 'Content-Type: application/json' \
  -d '{
    "document_family": "ieee_cs",
    "text": "The paper must include Abstract, Introduction, Method, Conclusion, and References. Use IEEE citation style.",
    "include_evidence": true
  }'
```

## Template Parsing By Local Path

Endpoint:

- `POST /api/v1/parse/template`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/parse/template \
  -H 'Content-Type: application/json' \
  -d '{
    "document_family": "ieee_cs",
    "provider": "zhipu",
    "docx_path": "/root/public/lzh/design-as-code/md2word_agent/tip.docx",
    "include_candidates": true
  }'
```

## Template Parsing By Base64

Example:

```bash
python - <<'PY'
from pathlib import Path
import base64
import json

data = base64.b64encode(Path('tip.docx').read_bytes()).decode('utf-8')
payload = {
    "document_family": "ieee_cs",
    "provider": "moonshot",
    "docx_base64": data,
    "include_candidates": False,
}
print(json.dumps(payload, ensure_ascii=False))
PY
```

Then send the generated JSON body to `POST /api/v1/parse/template`.

## Merged Template Spec Parsing

Endpoint:

- `POST /api/v1/parse/template/merged`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/parse/template/merged \
  -H 'Content-Type: application/json' \
  -d '{
    "document_family": "ieee_cs",
    "provider": "zhipu",
    "docx_path": "/root/public/lzh/design-as-code/md2word_agent/tip.docx",
    "rule_text": "The paper must include Abstract, Introduction, Method, Conclusion, and References. Use IEEE citation style.",
    "include_candidates": true,
    "include_evidence": true
  }'
```

This endpoint returns:

- merged `requirement`
- raw `rule_requirement`
- raw `file_requirement`
- `conflicts`
- `precedence_rules`
- optional `rule_evidence` and `candidates`

## Notes

- `docx_path` and `docx_base64` are mutually exclusive.
- Template parsing requires a valid provider API key in `.env`.
- Supported providers are `moonshot`, `minimax`, and `zhipu`.
