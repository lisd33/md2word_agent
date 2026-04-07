# Codex Handoff

This document summarizes the current state of `md2word_agent` so the next Codex can continue work without re-reading the whole history.

## 1. Project Goal

The project is **not** a plain `md2word` converter.

The current research-oriented goal is:

- normalize heterogeneous academic-template inputs
- extract low-level structural candidates from `.docx`
- use an LLM to understand **template structure intent**
- build a normalized `TemplateRequirement`
- later align template-side constraints with content-side intent

The key correction made during development was:

- **hardcoded heading extraction is not enough**
- Stage 3 must be `candidate extraction + LLM understanding`
- headings like `III. MATH` in IEEE author guides must not be treated as real paper skeleton sections just because they look like headings

## 2. Current Stage Status

### Stage 1: Done

Implemented:

- project skeleton
- shared dataclass contracts
- input router
- JSON schemas

Main files:

- `src/md2word_agent/input/router.py`
- `src/md2word_agent/specs/models.py`
- `schemas/*.json`

### Stage 2: Done

Implemented:

- `rule_text -> TemplateRequirement`
- citation style extraction
- required/optional section extraction
- basic formatting constraint extraction

Main file:

- `src/md2word_agent/parser/rule_parser.py`

### Stage 3: Done at minimum viable level

Implemented:

- `.docx` low-level read
- heading candidate extraction
- LLM-based template structure understanding
- provider-based LLM calling (`moonshot`, `minimax`, `zhipu`)
- final normalized `TemplateRequirement`
- automatic persistence of final model outputs to disk

Main files:

- `src/md2word_agent/parser/docx_reader.py`
- `src/md2word_agent/parser/models.py`
- `src/md2word_agent/parser/template_file_parser.py`
- `src/md2word_agent/planner/template_understanding.py`
- `src/md2word_agent/llm/`

### Stage 4: Not started

Planned next:

- merge rule-derived and file-derived template specifications
- define precedence / conflict resolution
- produce a cleaner merged template-side spec

## 3. Architectural Decisions Already Settled

These decisions should be treated as settled unless there is a strong reason to reopen them.

### 3.1 Template parsing is layered

Current layer split:

1. low-level `.docx` read
2. candidate extraction
3. LLM structure understanding
4. normalized `TemplateRequirement`

### 3.2 Parser is not fully model-based

We intentionally did **not** replace `.docx` reading with an LLM.

Programmatic tasks remain programmatic:

- XML reading
- style extraction
- paragraph extraction
- candidate heading extraction

LLM tasks:

- determine which candidates belong to the real paper skeleton
- filter instructional sections
- normalize final kept section titles where appropriate

### 3.3 Multiple LLM providers are already supported

Current supported providers:

- `moonshot`
- `minimax`
- `zhipu`

Provider selection exists in both:

- CLI
- HTTP API
- `.env`

### 3.4 Stage 3 output persistence is required

The final model response and normalized requirement are now automatically persisted under:

- `intermediate_outputs/template_understanding/`

This should remain, because it is useful for:

- debugging
- auditing model behavior
- later dataset creation / evaluation

## 4. Key Runtime Entry Points

### CLI

Rule parsing:

- `scripts/parse_rule_text.py`

Template parsing:

- `scripts/parse_docx_template.py`

Local HTTP API:

- `scripts/run_api_server.py`

### HTTP API routes

- `GET /health`
- `GET /providers`
- `POST /api/v1/parse/rules`
- `POST /api/v1/parse/template`

API docs:

- `api/README.md`

## 5. Current Important Files

### Planning / documentation

- `PROJECT_PLAN.md`
- `RESEARCH_PROBLEM.md`
- `PROJECT_TREE.md`
- `complete.md`
- `CODEX_HANDOFF.md`

### Core source tree

- `src/md2word_agent/input/router.py`
- `src/md2word_agent/specs/models.py`
- `src/md2word_agent/parser/rule_parser.py`
- `src/md2word_agent/parser/docx_reader.py`
- `src/md2word_agent/parser/models.py`
- `src/md2word_agent/parser/template_file_parser.py`
- `src/md2word_agent/planner/template_understanding.py`
- `src/md2word_agent/llm/config.py`
- `src/md2word_agent/llm/factory.py`
- `src/md2word_agent/llm/kimi_client.py`
- `src/md2word_agent/llm/minimax_client.py`
- `src/md2word_agent/llm/zhipu_client.py`
- `src/md2word_agent/api/service.py`
- `src/md2word_agent/api/server.py`

### Data and examples

- `data/rules/sample_author_guidelines.md`
- `tip.docx`

### Output / generated artifacts

- `intermediate_outputs/README.md`
- `intermediate_outputs/template_understanding/README.md`
- generated runtime JSON files under `intermediate_outputs/template_understanding/`

## 6. Current Testing Status

Full local test suite currently passes.

Command:

```bash
cd /root/public/lzh/design-as-code/md2word_agent
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

Current status when last run:

- `23 tests`
- `OK`

Important note:

- unit tests **do not call real external APIs**
- they use fake clients where needed
- real model invocation is tested through CLI or HTTP API, not through the unit-test suite

## 7. How To Run Real Stage 3 Parsing

### CLI example

```bash
cd /root/public/lzh/design-as-code/md2word_agent
python scripts/parse_docx_template.py tip.docx --provider zhipu --document-family ieee_cs --show-candidates
```

or:

```bash
python scripts/parse_docx_template.py tip.docx --provider moonshot --document-family ieee_cs --show-candidates
```

### HTTP API example

Start server:

```bash
cd /root/public/lzh/design-as-code/md2word_agent
python scripts/run_api_server.py --host 127.0.0.1 --port 8000
```

Then call:

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

## 8. Where Model Outputs Are Saved

Every real Stage 3 run now writes a JSON artifact to:

- `intermediate_outputs/template_understanding/`

Each file contains:

- `saved_at_utc`
- `document_family`
- `client_class`
- `system_prompt`
- `user_prompt_payload`
- `model_response`
- `normalized_requirement`

This is currently implemented in:

- `src/md2word_agent/planner/template_understanding.py`

## 9. What Has Not Been Done Yet

These are the main remaining work items.

### 9.1 Template-side merge

Still missing:

- merge `RuleParser` output and file-side Stage 3 output
- decide precedence rules
- handle conflicts between explicit rules and file-derived evidence

### 9.2 Better template normalization

Still missing:

- richer canonical section normalization
- better section type taxonomy
- figure / table slot understanding
- stronger handling of complex or nonstandard templates

### 9.3 Content-side processing

Still missing:

- `ContentIntent` extraction from user input / outline / draft
- alignment between `TemplateRequirement` and `ContentIntent`
- `DocumentIR` generation as an aligned editable structure

### 9.4 Rendering / export

Still missing:

- HTML / Markdown generation
- Word export path
- full end-to-end draft composition

## 10. Important Constraints / Things To Preserve

### 10.1 Do not regress Stage 3 back to pure hardcoding

This was an explicit design correction.

Do not change Stage 3 back into:

- heading detection -> direct final structure

That would reintroduce the core problem we already corrected.

### 10.2 Keep provider abstraction thin

Current provider layer is simple and intentionally isolated under:

- `src/md2word_agent/llm/`

Any future model/provider additions should go through:

- `config.py`
- `factory.py`
- one provider-specific client file

### 10.3 Keep HTTP API thin

The local HTTP API should remain a wrapper over the existing parser/planner pipeline.

Do not move business logic into the HTTP layer.

### 10.4 Keep intermediate outputs inspectable

Do not remove automatic saving of Stage 3 outputs unless replaced by something better.

## 11. Recommended Next Work For The Next Codex

Best next step:

### Stage 4: Merge and normalize template-side specifications

Concrete work items:

1. add a `SpecMerger` or similar module
2. merge:
   - rule-derived `TemplateRequirement`
   - file-derived `TemplateRequirement`
3. record conflict evidence
4. define precedence strategy
5. expose merged output through:
   - CLI
   - HTTP API
6. add tests for merge behavior

A reasonable file layout for that next step would be something like:

- `src/md2word_agent/merger/`
- or `src/md2word_agent/template/merger.py`

## 12. Extra References

Useful orientation files:

- `PROJECT_TREE.md` for file responsibilities
- `complete.md` for detailed historical implementation notes
- `api/README.md` for interface testing

If the next Codex wants a fast orientation path, read in this order:

1. `PROJECT_PLAN.md`
2. `RESEARCH_PROBLEM.md`
3. `PROJECT_TREE.md`
4. `CODEX_HANDOFF.md`
5. `src/md2word_agent/planner/template_understanding.py`
6. `src/md2word_agent/parser/template_file_parser.py`
7. `src/md2word_agent/api/service.py`
