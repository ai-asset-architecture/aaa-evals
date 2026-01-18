# Asset Promotion Checklist (Evals)

This checklist defines the minimum steps to promote eval assets into the main library.

## 1. Candidate Intake
- Candidate eval exists under `evals/cases/` and `evals/suites/`.
- Clear pass/fail criteria defined in suite metadata.
- Owner: `@aaa/qa` (primary), `@aaa/architect` (approval).

## 2. Baseline & Evidence
- Baseline stored under `evals/baselines/` and referenced by suite.
- Evidence or sample output captured (link in PR description).
- Owner: `@aaa/qa`.

## 3. Review & Approval
- Reviewed by `@aaa/qa`.
- Approved by `@aaa/architect` for policy alignment.

## 4. Versioning & Tag
- Changes are tagged (SemVer) after merge.
- Release notes include eval changes and new baselines.
- Owner: `@aaa/qa` with `@aaa/architect` sign-off.

## 5. Promotion Done
- Suite, cases, baselines, and runner updated.
- Documentation updated in `README.md`.
- Owner: `@aaa/qa`.

## When to Add New Evals
- New governance rules or gates (required files, policy updates).
- New asset types (new templates, new prompt schema).
- Incidents/regressions (codify the failure as an eval).
- Before adding new release gates.
- After bootstrap completion to cover common errors.

## Recommended Process
- Add suite + baseline in `aaa-evals`.
- Run and confirm pass.
- Tag a release (SemVer).
