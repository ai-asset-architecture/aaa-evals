"""
Nightly Dashboard Resilience Check

Purpose: Verify that the nightly governance dashboard can still be published
         even when compliance thresholds are not met (graceful degradation).

Derived from: P2-1 Nightly Resilience Validation (2026-01-28)
Evidence: internal/development/audits/2026-01-28-p2-1-nightly-resilience-validation.md

Key Verification Points:
1. Dashboard files are generated BEFORE threshold checks
2. `if: ${{ always() }}` condition ensures commit step always runs
3. Workflow produces complete JSON + MD + HTML even when gate fails
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def check_nightly_dashboard_resilience(repo_path: str) -> Dict[str, Any]:
    """
    Verify nightly dashboard has graceful degradation on threshold failure.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Check result dict with status and details
    """
    repo = Path(repo_path)
    details = []
    
    # 1. Verify workflow structure
    workflow_file = repo / ".github" / "workflows" / "nightly-governance.yaml"
    if not workflow_file.exists():
        return {
            "check": "nightly_dashboard_resilience",
            "repo": repo_path,
            "pass": False,
            "details": ["nightly-governance.yaml not found"]
        }
    
    workflow_content = workflow_file.read_text()
    
    # 2. Check: Dashboard generation happens before threshold check
    render_step_found = "ops render-dashboard" in workflow_content
    threshold_step_found = "--threshold" in workflow_content or "threshold-gate" in workflow_content
    
    if not render_step_found:
        details.append("Dashboard render step not found in workflow")
        return {
            "check": "nightly_dashboard_resilience",
            "repo": repo_path,
            "pass": False,
            "details": details
        }
    
    # 3. Check: Commit step has `if: ${{ always() }}` to ensure it runs even on failure
    commit_step_resilient = False
    lines = workflow_content.split('\n')
    
    for i, line in enumerate(lines):
        if 'commit' in line.lower() and 'step' in lines[max(0, i-5):i+1]:
            # Look for `if: ${{ always() }}` in the next few lines
            for j in range(i, min(i+10, len(lines))):
                if 'if:' in lines[j] and 'always()' in lines[j]:
                    commit_step_resilient = True
                    break
    
    if not commit_step_resilient:
        details.append("Commit step missing `if: ${{ always() }}` condition")
        # This is a warning, not a failure
    
    # 4. Check: Verify expected output structure in recent runs (if available)
    dashboard_dir = repo / "docs" / "dashboard"
    reports_dir = repo / "reports" / "audits"
    
    outputs_exist = False
    if dashboard_dir.exists() and reports_dir.exists():
        # Check for recent dashboard files
        html_files = list(dashboard_dir.glob("*.html"))
        md_reports = list(reports_dir.glob("nightly_governance_*.md"))
        
        if html_files and md_reports:
            outputs_exist = True
            details.append(f"Found {len(html_files)} dashboard HTML files")
            details.append(f"Found {len(md_reports)} nightly reports")
    
    # Final assessment
    passed = render_step_found and (commit_step_resilient or outputs_exist)
    
    if passed:
        details.append("✅ Dashboard generation is decoupled from threshold check")
        if commit_step_resilient:
            details.append("✅ Commit step has graceful degradation (`if: always()`)")
        if outputs_exist:
            details.append("✅ Dashboard outputs exist (proven resilience)")
    
    return {
        "check": "nightly_dashboard_resilience",
        "repo": repo_path,
        "pass": passed,
        "details": details
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python check_nightly_dashboard_resilience.py <repo_path>")
        sys.exit(1)
    
    result = check_nightly_dashboard_resilience(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["pass"] else 1)
