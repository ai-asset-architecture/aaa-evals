# aaa-evals

## Purpose / Scope
Evaluation assets: suites, datasets, and baselines used to gate releases and verify quality across aaa projects.

## Ownership / CODEOWNERS
Owned by the evals/QA maintainers. See `CODEOWNERS` (to be added).

## Versioning / Release
Eval suites and datasets are versioned by git tags. Baselines should be stored with the tag they were generated from.

## How to Consume / Use
Run evals via `aaa-tools` and pin to a specific tag for reproducibility.

## Contribution / Promotion Rules
New eval suites must include clear pass/fail criteria and a baseline. Dataset updates require a new tag.

## Eval Suites
- `core` (TBD)
- `agents` (TBD)

## Example Suites (v0.1)
- `readme_required` - checks README required sections and CODEOWNERS
- `workflow_tag_refs` - checks workflows reference aaa-actions by tag
- `skills_structure` - checks skills folders contain SKILL.md
- `prompt_schema` - validates prompts against prompt.schema.json

## Asset Promotion Pipeline
See `ASSET_PROMOTION.md` for the checklist and approval flow.

## Dataset & Baselines
- Datasets live under `datasets/` (TBD structure).
- Baselines live under `baselines/` and are keyed by tag.

## How to Run
```bash
aaa eval run --suite core --source ./aaa-evals
```

Example runner usage:
```bash
python runner/run_repo_checks.py --check readme --repo /path/to/repo
python runner/run_repo_checks.py --check workflow --repo /path/to/repo
python runner/run_repo_checks.py --check skills --repo /path/to/aaa-tools --skills-root skills
python runner/run_repo_checks.py --check prompt --repo /path/to/aaa-prompts --schema-path prompt.schema.json --prompts-dir prompts
```
