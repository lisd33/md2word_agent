# Completion Log

## Stage 1: Initial Scaffolding And Core Contracts

### Stage Goal

Establish the minimum project skeleton and shared contracts required to start real parser and planner work without drifting into ad hoc scripts.

### Work Completed

#### 1. Project structure

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

#### 2. Packaging scaffold

Added `pyproject.toml`.

Current state:

- package name: `md2word-agent`
- Python target: `>=3.11`
- package root: `src/`
- no runtime dependencies yet

#### 3. Core schema models

Added the first set of normalized Python dataclass models in `src/md2word_agent/specs/models.py`:

- `TemplateSectionRequirement`
- `TemplateRequirement`
- `ContentIntent`
- `DocumentSectionPlan`
- `DocumentIR`

Purpose of these objects:

- `TemplateRequirement`: normalized template-side constraints
- `ContentIntent`: normalized user-side semantic intent
- `DocumentIR`: normalized document-side editable structure

#### 4. JSON schema files

Added machine-readable schema definitions:

- `schemas/template_requirement.schema.json`
- `schemas/content_intent.schema.json`
- `schemas/document_ir.schema.json`

These were added so later parser / planner / LLM modules can target stable contracts instead of ad hoc JSON.

#### 5. Lightweight input router

Added `src/md2word_agent/input/router.py`.

Implemented objects:

- `InputPayload`
- `RoutedInput`
- `InputRouter`

Current router behavior:

- recognizes template files by suffix (`.docx`, `.dotx`, `.doc`)
- recognizes structured specs by suffix (`.json`, `.yaml`, `.yml`)
- routes markdown using text heuristics instead of assuming one fixed role
- distinguishes `rule_text` and `content_draft` through keyword hints
- upgrades a batch to `mixed_input` if multiple source kinds are present

#### 6. Stage 1 tests

Added:

- `tests/input/test_router.py`
- `tests/specs/test_models.py`
- `tests/__init__.py`
- `tests/input/__init__.py`
- `tests/specs/__init__.py`

### Design Decisions In Stage 1

#### Decision 1: Router stays rule-first

I did not make the router model-based.

Reason:

- input routing is a systems utility, not the project's main research contribution
- deterministic routing is easier to debug at this stage
- model routing can be added later only for ambiguous cases

#### Decision 2: Contracts before parser logic

I defined normalized specs before implementing real parsing.

Reason:

- future modules need a shared target format
- parser, rule parser, intent parser, and alignment should not invent incompatible structures independently

#### Decision 3: Alignment action space added early

`DocumentIR` already includes section actions:

- `keep`
- `optionalize`
- `remove`
- `add`
- `split`
- `merge`

Reason:

- this is likely the future target vocabulary of the alignment stage
- it reduces schema churn later

### Verification For Stage 1

#### Issue encountered

Initial `unittest discover` found `0 tests` because the nested test directories were not marked as importable test packages.

#### Fix applied

Added:

- `tests/__init__.py`
- `tests/input/__init__.py`
- `tests/specs/__init__.py`

#### Test command

From `md2word_agent/`, ran:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

#### Result

- total tests after Stage 1: 7
- status: OK

Validated behaviors:

- template-file routing by suffix
- rule-text routing by keyword hints
- content-draft routing by semantic hints
- mixed-input upgrade in batch routing
- dataclass serialization for `TemplateRequirement`
- dataclass serialization for `ContentIntent`
- nested serialization for `DocumentIR`

### Files Added In Stage 1

- `pyproject.toml`
- `src/md2word_agent/__init__.py`
- `src/md2word_agent/input/__init__.py`
- `src/md2word_agent/input/router.py`
- `src/md2word_agent/specs/__init__.py`
- `src/md2word_agent/specs/models.py`
- `src/md2word_agent/ir/__init__.py`
- `schemas/template_requirement.schema.json`
- `schemas/content_intent.schema.json`
- `schemas/document_ir.schema.json`
- `tests/__init__.py`
- `tests/input/__init__.py`
- `tests/input/test_router.py`
- `tests/specs/__init__.py`
- `tests/specs/test_models.py`

### Stage 1 Exit Status

Stage 1 is complete.

What changed in project state:

- the project moved from plan-only to code-backed scaffolding
- stable contracts now exist for template constraints, content intent, and document IR
- a first multi-source input entry point now exists

What was intentionally not done yet:

- `.docx` parsing
- rule-text extraction into `TemplateRequirement`
- content-intent extraction
- alignment logic
- rendering and export

---

## Stage 2: Rule Text To TemplateRequirement

### Stage Goal

Build the first real normalization path that converts natural-language template guidance into a structured template-side representation.

### Drift Check Before Starting Stage 2

I re-checked the implementation against:

- `md2word_agent/PROJECT_PLAN.md`
- `md2word_agent/RESEARCH_PROBLEM.md`

Conclusion:

- no major goal drift was found
- Stage 1 remained aligned with the plan and research framing
- the implementation had not collapsed into a narrow `md2word` converter
- the abstractions were still centered on multi-source normalization and structure-semantic alignment

The only mild shift was that Stage 1 was infrastructure-heavy, but that was acceptable because stable interfaces were required before parser work.

### Work Completed

#### 1. Parser package

Added:

- `src/md2word_agent/parser/__init__.py`
- `src/md2word_agent/parser/rule_parser.py`
- `tests/parser/__init__.py`
- `tests/parser/test_rule_parser.py`

#### 2. First rule parser

Implemented `RuleParser` as a conservative extractor from rule text into `TemplateRequirement`.

Currently extracted signal types:

- citation style
- required sections
- optional sections
- basic formatting constraints

#### 3. Citation style extraction

Currently recognized:

- `IEEE`
- `ACM`
- `Springer`
- `APA`

These are extracted only from explicit signals in the rule text.

#### 4. Section extraction

Currently supported academic-paper section types:

- `Abstract`
- `Introduction`
- `Related Work`
- `Method`
- `Experiments`
- `Results`
- `Discussion`
- `Conclusion`
- `References`

Current extraction behavior supports:

- explicit list extraction from prose
- fallback inference from strong section mentions

#### 5. Formatting constraint extraction

Currently extracted formatting fields:

- `title_font_family`
- `title_font_size`
- `body_font_family`
- `body_font_size`
- `body_line_spacing`

This is still intentionally narrow. The goal here was not full style reconstruction, only a first working rule normalization path.

#### 6. Evidence tracking

`RuleParseResult` stores:

- the extracted `TemplateRequirement`
- an `evidence` dictionary that records which patterns triggered extraction

This makes later debugging and research reporting easier.

#### 7. Sample rule input

Added:

- `data/rules/sample_author_guidelines.md`

This file serves as:

- a parser fixture
- an example of expected author-guideline input
- a future integration-test seed

### Debugging Notes From Stage 2

Stage 2 did not pass on the first run. Two real extraction bugs were found and fixed.

#### Bug 1: weak section-list extraction

Observed behavior:

- in `The paper must include Abstract, Introduction, Method, Conclusion, and References.`
- only `Abstract` was recovered reliably at first

Cause:

- list parsing was too weak
- `and` was not normalized properly as a list separator

Fix:

- tightened section-list patterns
- added `_split_section_candidates()`
- normalized `and` to comma before splitting

Result:

- all expected required sections are now extracted in the test case

#### Bug 2: `font` vs `font size` collision

Observed behavior:

- `Title font size is 14pt.` was being partially misread as if the font family were `size is 14pt`

Cause:

- the font-family regex matched `font` too broadly and accidentally overlapped with `font size`

Fix:

- tightened the font-family regex with a negative lookahead so `font` does not match `font size`

Result:

- font family and font size now extract separately and correctly

### Verification For Stage 2

#### Test command

From `md2word_agent/`, ran:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

#### Result

- total tests after Stage 2: 10
- status: OK

Newly validated behaviors:

- extraction of `IEEE` citation style from rule text
- extraction of required sections from author-guideline prose
- extraction of optional sections
- extraction of title/body font families
- extraction of title/body font sizes
- extraction of line spacing constraints

### Files Added In Stage 2

- `src/md2word_agent/parser/__init__.py`
- `src/md2word_agent/parser/rule_parser.py`
- `tests/parser/__init__.py`
- `tests/parser/test_rule_parser.py`
- `data/rules/sample_author_guidelines.md`

### Stage 2 Exit Status

Stage 2 is complete.

What changed in project state:

- the project now has its first real parser path
- natural-language rule text can now be normalized into `TemplateRequirement`
- the repository is no longer just scaffolding; it now contains a working template-side extraction flow

What is still not done:

- `.docx` template parsing
- template-file to `TemplateRequirement` mapping
- merger between file-derived and rule-derived constraints
- `ContentIntent` extraction
- alignment logic
- rendering and export

---

## Recommended Next Stage

The next natural stage is:

`template_file -> TemplateRequirement`

That means the next implementation step should focus on:

- a minimal `.docx` template parser stub
- first paragraph/style extraction objects
- mapping file-side structure into the same normalized requirement object already produced by `RuleParser`
- preparing for future merging of file-derived and rule-derived constraints

---

## Stage 3: Template Candidate Extraction And LLM-Based Template Understanding (Restarted)

### Stage Goal

Restart Stage 3 so that `.docx` template ingestion no longer treats low-level heading extraction as final template understanding.

The corrected Stage 3 goal is:

- programmatically extract candidate structural signals from `.docx`
- send those candidates to an LLM-based structure-understanding layer
- build `TemplateRequirement` only after semantic filtering and normalization
- keep Stage 1 and Stage 2 contracts unchanged so the repository stays stable

### Drift Check And Compatibility Review Before Restarting Stage 3

Before rewriting this stage, I re-checked the implementation against:

- `md2word_agent/PROJECT_PLAN.md`
- `md2word_agent/RESEARCH_PROBLEM.md`
- Stage 1 outputs
- Stage 2 outputs

Conclusion:

- the original Stage 3 implementation had a real conceptual drift
- the drift was not in low-level `.docx` reading itself
- the drift was in directly mapping heading-like paragraphs into final `TemplateRequirement`
- this conflicted with the project's research framing, which requires template-structure understanding rather than pattern-only extraction

Why the earlier Stage 3 was insufficient:

- it could detect candidate headings such as `III. MATH`
- but it could not determine whether such headings were true paper skeleton sections or author-guideline sections
- in real journal templates, this distinction requires semantic understanding, not only hardcoded heading rules

Compatibility conclusion after redesign:

- Stage 1 remains valid because the core contracts and router still fit the revised architecture
- Stage 2 remains valid because `RuleParser` still produces `TemplateRequirement` from rule text
- the restarted Stage 3 now complements Stage 2 instead of conflicting with it
- no schema reset was needed
- no broad repository cleanup was needed

### Work Completed

#### 1. Preserved the low-level `.docx` reader as the candidate-extraction layer

Kept the parser split so low-level document reading remains programmatic.

Relevant files:

- `src/md2word_agent/parser/models.py`
- `src/md2word_agent/parser/docx_reader.py`

Current responsibilities of this layer:

- read `document.xml` and `styles.xml` from `.docx`
- extract paragraph text
- resolve style ids and style names
- preserve numbering level when available
- construct `TemplateCandidate` objects with local context

This keeps the parser deterministic at the document-reading level while avoiding the earlier mistake of letting hardcoded heading extraction decide final structure.

#### 2. Reworked template file parsing around candidate extraction plus semantic understanding

Updated:

- `src/md2word_agent/parser/template_file_parser.py`

The parser no longer treats heading detection as final structure extraction.

New Stage 3 flow:

1. `DocxReader` reads the `.docx`
2. `TemplateFileParser.extract_candidates()` builds `TemplateCandidate` objects
3. `TemplateUnderstandingPlanner` sends candidates to the LLM layer
4. only the LLM-filtered result becomes final `TemplateRequirement`

Each candidate now carries:

- title text
- inferred level
- style id
- style name
- numbering level
- previous paragraph text
- next paragraph text

That context is important because journal author-guide templates often contain instructional headings that are visually similar to real paper sections.

#### 3. Added a dedicated LLM initialization layer for Kimi API

Added a new module group under:

- `src/md2word_agent/llm/`

Files added:

- `src/md2word_agent/llm/__init__.py`
- `src/md2word_agent/llm/config.py`
- `src/md2word_agent/llm/kimi_client.py`
- `src/md2word_agent/llm/minimax_client.py`
- `src/md2word_agent/llm/factory.py`
- `src/md2word_agent/llm/zhipu_client.py`

Purpose of this folder:

- centralize API initialization logic
- keep model configuration separate from parser logic
- make later model swaps easier without rewriting the parser

Implemented capabilities:

- load Kimi-related environment variables from `.env`
- provide a typed `KimiConfig`
- call Moonshot-compatible chat completions API using standard library HTTP
- enforce strict JSON parsing for downstream planner consumption

Current `.env` file added at project root:

- `MOONSHOT_API_KEY`
- `MOONSHOT_BASE_URL`
- `MOONSHOT_MODEL`
- `MOONSHOT_TEMPERATURE`

Default model currently recorded as:

- `kimi-k2.5`

This matches the user's current decision to use API first instead of local fine-tuned models.

#### 4. Added the Stage 3 template-understanding planner

Added:

- `src/md2word_agent/planner/__init__.py`
- `src/md2word_agent/planner/template_understanding.py`

This planner is the new semantic bridge between low-level candidate extraction and high-level template requirement construction.

Current planner responsibilities:

- package candidate headings and optional rule text into a JSON prompt payload
- instruct the model to distinguish true paper skeleton sections from instructional or policy sections
- request normalized section names where appropriate
- build final `TemplateRequirement` objects from strict JSON responses

The planner now encodes the corrected research assumption:

- hardcoded extraction finds possible structure
- the LLM decides what the structure actually means

#### 5. Updated the script entry points to match the restarted Stage 3 architecture

Kept and synchronized the scripts folder.

Current script state:

- `scripts/parse_rule_text.py`
- `scripts/parse_docx_template.py`

`parse_rule_text.py` remains the Stage 2 CLI entry point for rule-text normalization.

`parse_docx_template.py` was rewritten for the restarted Stage 3 and now:

- loads Kimi API config from `.env`
- initializes `KimiClient`
- initializes `TemplateUnderstandingPlanner`
- runs `.docx -> candidates -> LLM understanding -> TemplateRequirement`
- optionally prints extracted candidates before final filtering
- accepts optional rule text as extra context

This keeps the user-facing script surface aligned with the new architecture instead of exposing the earlier hardcoded-only path.

#### 6. Updated tests around the restarted Stage 3 path

Current test coverage now includes:

- low-level `.docx` reading still works
- candidate extraction still works
- the parser can defer final structure decisions to a planner abstraction
- Kimi `.env` loading works
- planner-level template understanding conversion works without network access

Files involved:

- `tests/parser/test_docx_reader.py`
- `tests/test_llm_config.py`
- `tests/test_llm_factory.py`
- `tests/planner/test_template_understanding.py`
- `.ignore`

The synthetic `.docx` parser test now validates the new contract:

- candidate extraction may include visually heading-like author-guideline sections
- the planner layer is responsible for dropping those sections before final requirement construction

That is the correct Stage 3 behavior for this project.

### Design Decisions In Restarted Stage 3

#### Decision 1: Do not discard the parser, narrow its role

I did not replace the entire template parser with a pure LLM call.

Reason:

- `.docx` reading, XML access, style extraction, and heading-candidate collection are deterministic tasks
- these tasks are easier to test and debug programmatically
- the real semantic uncertainty starts after candidate extraction

So the new division is:

- parser for low-level extraction
- LLM for structural intent understanding

#### Decision 2: Retire direct heading-to-requirement mapping

The earlier direct mapping path is no longer the intended Stage 3 design.

Reason:

- it falsely treated all heading-like paragraphs as required sections
- it could not distinguish author instructions from real paper skeleton sections
- that behavior conflicted with the project's research problem definition

#### Decision 3: Put model initialization in its own folder

I created `src/md2word_agent/llm/` instead of scattering API setup across scripts.

Reason:

- scripts should stay thin
- parser code should not own HTTP initialization
- later replacement of Kimi with another API or a local model should be localized

#### Decision 4: Keep Stage 1 and Stage 2 contracts stable

I did not rewrite the core `TemplateRequirement` schema.

Reason:

- Stage 1 and Stage 2 are still conceptually correct
- only the path that produces template-file requirements needed to be corrected
- keeping the contract stable avoids repository churn and preserves downstream compatibility

### Verification For Restarted Stage 3

#### Test command

From `md2word_agent/`, ran:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

#### Result

- total tests after restarted Stage 3: 21
- status: OK

Validated behaviors now include:

- input routing still works after the Stage 3 restart
- schema serialization still works after the Stage 3 restart
- rule-text parsing still works after the Stage 3 restart
- low-level `.docx` reading still works after the Stage 3 restart
- `.docx` candidate extraction now routes through a planner layer before final requirement construction
- Kimi `.env` loading is now covered by default test discovery
- planner response-to-requirement conversion is now covered by a local fake-client unit test
- provider selection and MiniMax client construction are covered by local unit tests
- Zhipu config loading, provider alias resolution, and client construction are covered by local unit tests

### Files Added Or Updated In Restarted Stage 3

Added:

- `.env`
- `src/md2word_agent/llm/__init__.py`
- `src/md2word_agent/llm/config.py`
- `src/md2word_agent/llm/kimi_client.py`
- `src/md2word_agent/llm/minimax_client.py`
- `src/md2word_agent/llm/factory.py`
- `src/md2word_agent/llm/zhipu_client.py`
- `src/md2word_agent/planner/__init__.py`
- `src/md2word_agent/planner/template_understanding.py`
- `tests/test_llm_config.py`
- `tests/test_llm_factory.py`
- `tests/planner/test_template_understanding.py`
- `.ignore`

Updated:

- `src/md2word_agent/parser/models.py`
- `src/md2word_agent/parser/template_file_parser.py`
- `src/md2word_agent/parser/__init__.py`
- `scripts/parse_docx_template.py`
- `scripts/parse_rule_text.py`
- `tests/parser/test_docx_reader.py`

### Stage 3 Exit Status

Restarted Stage 3 is complete at the current minimum viable level.

What changed in project state:

- `.docx` parsing no longer ends at hardcoded heading extraction
- the project now has an explicit LLM-based template-understanding layer
- API-based Kimi initialization is now part of the repository structure
- the LLM layer now supports Moonshot/Kimi, MiniMax, and Zhipu as selectable providers
- the scripts folder now reflects the revised architecture
- Stage 1 and Stage 2 remain usable without rework

What is still intentionally not done:

- file-side and rule-side template spec merging
- conflict resolution between `.docx` evidence and rule-text evidence
- richer section canonicalization policies
- figure/table slot understanding
- content-intent extraction
- structure-semantic alignment against user content
- rendering and export

## Recommended Next Stage

The next natural stage is:

`merge and normalize template-side specifications`

That means the next implementation step should focus on:

- merging Stage 2 rule-derived constraints with restarted Stage 3 file-derived constraints
- defining precedence and conflict-resolution rules
- preserving both raw evidence and normalized template requirements
- preparing the cleaned template-side result for later content-intent alignment

---

## Stage 3 Tooling Update: Local HTTP API Interface

### Update Goal

Add a local HTTP interface on top of the existing parser and planner pipeline so Stage 2 and Stage 3 can be tested through API calls instead of only through Python scripts.

### Work Completed

#### 1. Added API service layer

Added:

- `src/md2word_agent/api/__init__.py`
- `src/md2word_agent/api/service.py`
- `src/md2word_agent/api/server.py`

Current service responsibilities:

- expose `parse_rule_text()` for Stage 2 rule normalization
- expose `parse_docx_template()` for Stage 3 template parsing
- support local `.docx` path input
- support base64 `.docx` input
- preserve provider selection through the existing LLM factory

#### 2. Added local HTTP server entry point

Added:

- `scripts/run_api_server.py`

This script starts a local HTTP server without introducing an external web framework dependency.

Current routes:

- `GET /health`
- `GET /providers`
- `POST /api/v1/parse/rules`
- `POST /api/v1/parse/template`

#### 3. Added API documentation directory

Added:

- `api/README.md`

This document now serves as the API usage guide and includes:

- startup instructions
- health-check example
- provider-check example
- rule parsing request example
- template parsing request example
- base64 upload example

#### 4. Added API-layer unit tests

Added:

- `tests/api/__init__.py`
- `tests/api/test_service.py`

Current API-layer test coverage includes:

- Stage 2 parsing through `ParseAPIService`
- Stage 3 template parsing through `ParseAPIService`
- `.docx` path input handling
- fake-client injection for non-network planner validation

### Verification For API Update

#### Test command

From `md2word_agent/`, ran:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

#### Result

- total tests after API update: 23
- status: OK

Also verified startup script help:

```bash
python scripts/run_api_server.py --help
```

### Current Testing Entry Points

You can now test the project in three ways:

- CLI: `scripts/parse_rule_text.py`
- CLI: `scripts/parse_docx_template.py`
- HTTP API: `scripts/run_api_server.py`

### Current Interface Boundary

The local API is intentionally thin.

It does not add new parsing logic. It only wraps existing Stage 2 and Stage 3 capabilities so they are easier to test and automate.

---

## Stage 3 Tooling Update: Intermediate Outputs And Project Tree

### Update Goal

Make Stage 3 outputs easier to inspect by persisting the final model result to disk, and add a dedicated project-tree document so the current repository structure is easier to understand.

### Work Completed

#### 1. Added automatic intermediate output persistence

Updated:

- `src/md2word_agent/planner/template_understanding.py`

Current behavior:

- every Stage 3 planner run now saves a JSON artifact under `intermediate_outputs/template_understanding/`
- each artifact contains the prompt payload, the final model response, and the normalized `TemplateRequirement`
- the output directory is created automatically when needed

#### 2. Added intermediate output documentation

Added:

- `intermediate_outputs/README.md`
- `intermediate_outputs/template_understanding/README.md`

These files explain what is stored in the new output directory and what fields appear in each generated JSON artifact.

#### 3. Added project tree documentation

Added:

- `PROJECT_TREE.md`

This file documents:

- the current repository tree
- the role of each major source file
- the current runtime flow
- the mapping between repository modules and project stages

#### 4. Extended planner tests

Updated:

- `tests/planner/test_template_understanding.py`

The planner test now verifies not only the normalized requirement but also that a JSON artifact is actually written to disk.

### Verification For Output And Tree Update

#### Test command

From `md2word_agent/`, ran:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

#### Result

- total tests after output/tree update: 23
- status: OK

### Practical Result

After this update, a real Stage 3 run through either the CLI or the HTTP API will leave an inspectable JSON file in:

- `intermediate_outputs/template_understanding/`

This makes it easier to audit the model output without relying only on terminal logs.
