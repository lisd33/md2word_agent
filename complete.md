# Completion Log

## Task Scope

This log records the first implementation pass requested for `md2word_agent`: create the initial project skeleton, define the minimum core schemas, build a lightweight input router, and leave the repository in a state where the next round of parser and planner work can start immediately.

## What Was Added

### 1. Project skeleton

Created the initial directory layout under `md2word_agent/`:

- `src/md2word_agent/`
- `src/md2word_agent/input/`
- `src/md2word_agent/specs/`
- `src/md2word_agent/ir/`
- `schemas/`
- `tests/input/`
- `tests/specs/`
- `data/templates/raw/`
- `data/rules/`
- `docs/`

This establishes separate locations for runtime code, schemas, tests, and future template/rule assets. The layout follows the plan's multi-source input design rather than assuming a single `docx -> word` tool.

### 2. Python packaging scaffold

Added `pyproject.toml` so the directory can behave like a Python package from the start.

Current state:

- package name: `md2word-agent`
- Python target: `>=3.11`
- package root: `src/`
- no runtime dependencies yet

Reasoning:

- avoids ad hoc script sprawl
- makes imports stable for tests
- keeps the project ready for `pip install -e .` later

### 3. Core schema models

Added Python dataclass models in `src/md2word_agent/specs/models.py` and exported them through `src/md2word_agent/specs/__init__.py`.

Implemented objects:

- `TemplateSectionRequirement`
- `TemplateRequirement`
- `ContentIntent`
- `DocumentSectionPlan`
- `DocumentIR`

Why these three top-level schemas were chosen:

- `TemplateRequirement` is the normalized representation of template-side constraints after parsing templates and/or rule text.
- `ContentIntent` is the normalized representation of user-side semantic intent.
- `DocumentIR` is the unified output representation that later planner/composer stages will manipulate.

These three objects are the minimum viable backbone of the architecture described in the plan.

Details of the current fields:

#### `TemplateRequirement`

Includes:

- `document_family`
- `source_kinds`
- `required_sections`
- `optional_sections`
- `citation_style`
- `formatting_constraints`
- `figure_requirements`
- `notes`

This keeps the object broad enough for both template parsing and rule-text extraction, without prematurely baking in very detailed layout logic.

#### `ContentIntent`

Includes:

- `title`
- `domain`
- `paper_type`
- `keywords`
- `has_experiments`
- `has_figures`
- `source_summary`
- `constraints`

This is intentionally minimal and aligned with the plan's intent-parsing stage.

#### `DocumentIR`

Includes:

- document metadata
- source kinds
- section tree
- references
- figures

It currently focuses on structural organization, not final rendering fidelity. That matches the project framing: structure-semantic alignment first, complex layout later.

### 4. JSON Schemas

Added machine-readable JSON schema files:

- `schemas/template_requirement.schema.json`
- `schemas/content_intent.schema.json`
- `schemas/document_ir.schema.json`

Purpose:

- give downstream modules a stable contract
- make it easier to validate LLM outputs later
- reduce ambiguity before alignment-model work starts

Notable design choice:

- section actions in `DocumentIR` are already constrained to: `keep`, `optionalize`, `remove`, `add`, `split`, `merge`

This was done deliberately because the alignment stage will likely use this action space directly, including possible future fine-tuning experiments.

### 5. Lightweight input router

Added `src/md2word_agent/input/router.py` and exported it through `src/md2word_agent/input/__init__.py`.

Implemented objects:

- `InputPayload`
- `RoutedInput`
- `InputRouter`

Current router behavior:

- recognizes template files by suffix (`.docx`, `.dotx`, `.doc`)
- recognizes structured specs by suffix (`.json`, `.yaml`, `.yml`)
- routes markdown through text heuristics instead of assuming it is always content
- distinguishes `rule_text` and `content_draft` using keyword hint sets
- marks a single payload as `mixed_input` if rule and content signals both appear
- marks a batch as `mixed_input` when multiple routed source kinds are present

This implementation is intentionally rule-first.

Why this version was chosen:

- it matches the plan's requirement that input routing is a system module, not the paper's main contribution
- it is deterministic and debuggable
- it leaves room for a model-assisted fallback later if ambiguous natural-language input becomes common

Current supported `InputKind` values:

- `template_file`
- `rule_text`
- `content_draft`
- `structured_spec`
- `mixed_input`
- `unknown`

### 6. Basic tests

Added unit tests:

- `tests/input/test_router.py`
- `tests/specs/test_models.py`

Coverage in this first pass:

- `.docx` routes to `template_file`
- rule-like text routes to `rule_text`
- draft-like text routes to `content_draft`
- mixed batches upgrade to `mixed_input`
- schema dataclasses serialize correctly
- nested section trees serialize correctly

These tests are small but important because they lock the current contracts before parser work starts.

## Design Decisions Made In This Pass

### Decision 1: Keep router simple

I did not implement a model-based router.

Reason:

- not necessary for first-stage progress
- more brittle to debug
- not aligned with the project's main research contribution

If needed later, the current router can be extended with a fallback classifier or LLM call for ambiguous text.

### Decision 2: Separate normalized specs from parser logic

I created normalized spec objects before building the actual parser.

Reason:

- parser implementation should target a stable output contract
- rule parser, template parser, and future intent parser all need a shared destination format
- this reduces drift when later modules are implemented by different passes or people

### Decision 3: Put alignment action space into the IR now

I included `keep / optionalize / remove / add / split / merge` in the section plan schema immediately.

Reason:

- this anticipates the alignment module
- it gives later LLM or fine-tuning work a stable target vocabulary
- it reduces future schema churn

## What Is Not Implemented Yet

This first pass does **not** implement the following:

- actual `.docx` parsing
- rule-text extraction into `TemplateRequirement`
- Markdown parsing into structured content intent
- spec merging across multiple source channels
- alignment logic
- HTML rendering
- Word export

This was intentional. The goal of this pass was to establish the base contracts and repository structure, not to prematurely implement the full pipeline.

## Suggested Next Step

The most logical next implementation step is:

1. build `rule_parser.py`
2. define a first `TemplateRequirement` extraction pipeline from natural-language rules
3. add one or two sample rule documents under `data/rules/`
4. then build a minimal `template parser -> TemplateRequirement` stub so both input channels target the same object

That would create the first real normalization path and make the planner stage much easier to start.

## Verification Performed

### Test discovery fix

During verification, `unittest discover` initially reported `Ran 0 tests` because the nested test directories had not yet been marked as importable test packages.

To fix this, I added:

- `tests/__init__.py`
- `tests/input/__init__.py`
- `tests/specs/__init__.py`

This is a small but important detail because it keeps the project compatible with standard library test discovery before any heavier test tooling is introduced.

### Test command executed

From `md2word_agent/`, I ran:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

### Result

All current tests passed.

- total tests: 7
- status: OK

Covered behaviors confirmed by the passing run:

- template-file routing by suffix
- rule-text routing by keyword hints
- content-draft routing by semantic hints
- mixed-input upgrade in batched routing
- dataclass serialization for `TemplateRequirement`
- dataclass serialization for `ContentIntent`
- nested section serialization for `DocumentIR`
