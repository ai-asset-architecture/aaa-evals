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

## Supported Suites (v0.3.1)
- `readme_required` - checks README required sections and CODEOWNERS / 檢查 README 必要章節與 CODEOWNERS
- `workflow_tag_refs` - checks workflows reference aaa-actions by tag / 檢查 workflow 是否以 tag 引用 aaa-actions
- `skills_structure` - checks skills folders contain SKILL.md / 檢查 skills 目錄是否含 SKILL.md
- `prompt_schema` - validates prompts against prompt.schema.json / 驗證 prompts 符合 prompt.schema.json
- `member_bootstrap_prereq` - checks SOP includes auth/setup and dual-path flow / 檢查 SOP 是否包含 auth/setup 與雙路徑流程
- `private_download_sanity` - checks SOP uses gh api and JSON sanity checks / 檢查 SOP 使用 gh api 與 JSON sanity 檢查
- `start_here_sync` - checks org profile Start Here matches SOP essentials / 檢查組織首頁 Start Here 與 SOP 要點一致
- `skill_structure_v2` - checks skills include Routing/Execution/Fallback/IO/Limitations blocks / 檢查技能結構區塊是否完整
- `gh_cli_setup` - checks `gh` auth status and git identity setup / 檢查 gh 登入與 git 身分設定
- `gh_org_audit` - audits org repos for README/CODEOWNERS/workflow pinning/branch protection / 審計 org repo 的 README/CODEOWNERS/workflow pinning/branch protection
- `smoke` - baseline smoke suite / 基線 smoke 驗證
- `onboarding_doc_drift` - checks onboarding version drift across docs / 檢查 onboarding 文件版本漂移
- `onboarding_command_integrity` - checks README/SOP command parity / 檢查 README 與 SOP 指令一致
- `plan_schema_ref_sync` - checks plan/schema tag parity in SOP / 檢查 SOP 中 plan/schema tag 一致
- `cli_contract_sync` - checks SOP/user contract align with CLI contract / 檢查 SOP 與使用者合約對齊 CLI 合約

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
python runner/run_repo_checks.py --check onboarding_command_integrity --repo /path/to/workspace
python runner/run_repo_checks.py --check plan_schema_ref_sync --repo /path/to/workspace
python runner/run_repo_checks.py --check cli_contract_sync --repo /path/to/workspace
python runner/run_gh_cli_setup.py --check gh_cli_setup
python runner/run_github_audit.py
```

## Onboarding Doc Drift

Run:
```bash
python3 runner/run_repo_checks.py --check onboarding_doc_drift --repo /path/to/workspace
```
