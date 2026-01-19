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
- `member_bootstrap_prereq` - checks member SOP includes auth/setup and dual-path flow
- `private_download_sanity` - checks SOP uses gh api and JSON sanity checks for private files
- `start_here_sync` - checks org profile Start Here matches member SOP essentials
- `gh_cli_setup` - checks `gh` auth status and git identity setup
- `gh_org_audit` - audits org repos for README/CODEOWNERS/workflow pinning/branch protection

## Asset Promotion Pipeline
See `ASSET_PROMOTION.md` for the checklist and approval flow.

## When to Add New Evals
- New governance rules or gates (required files, policy updates).
- New asset types (new templates, new prompt schema).
- Incidents/regressions (codify the failure as an eval).
- Before adding new release gates.
- After bootstrap completion to cover common errors.

## Ownership
- Primary: `@aaa/qa`
- Approval: `@aaa/architect`

## Automation Hook
- Use `aaa-governance-audit` to run all governance checks and write a report to `aaa-tpl-docs/reports/`.

## Dataset & Baselines
- Datasets live under `datasets/` (TBD structure).
- Baselines live under `baselines/` and are keyed by tag.

## How to Run
```bash
aaa eval run --suite core --source ./aaa-evals
```

Example runner usage:
```bash
pip install -r runner/requirements.txt
python runner/run_repo_checks.py --check readme --repo /path/to/repo
python runner/run_repo_checks.py --check workflow --repo /path/to/repo
python runner/run_repo_checks.py --check skills --repo /path/to/aaa-tools --skills-root skills
python runner/run_repo_checks.py --check prompt --repo /path/to/aaa-prompts --schema-path prompt.schema.json --prompts-dir prompts
python runner/run_gh_cli_setup.py --check gh_cli_setup
python runner/run_github_audit.py
```
