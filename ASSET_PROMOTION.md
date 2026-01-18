# Asset Promotion Checklist (Evals)

This checklist defines the minimum steps to promote eval assets into the main library.

## 1. Candidate Intake
- Candidate eval exists under `evals/cases/` and `evals/suites/`.
- Clear pass/fail criteria defined in suite metadata.

## 2. Baseline & Evidence
- Baseline stored under `evals/baselines/` and referenced by suite.
- Evidence or sample output captured (link in PR description).

## 3. Review & Approval
- Reviewed by `@aaa/qa`.
- Approved by `@aaa/architect` for policy alignment.

## 4. Versioning & Tag
- Changes are tagged (SemVer) after merge.
- Release notes include eval changes and new baselines.

## 5. Promotion Done
- Suite, cases, baselines, and runner updated.
- Documentation updated in `README.md`.
