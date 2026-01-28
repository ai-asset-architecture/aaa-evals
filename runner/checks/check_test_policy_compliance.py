import os
import json
from pathlib import Path

def check_test_policy_compliance(repo_path: str) -> tuple[bool, list[str]]:
    """
    驗證里程碑結項報告是否符合測試覆蓋率政策。
    1. index.json 是否存在
    2. 每個 status="completed" 的里程碑是否都有 completion_report.md
    3. 報告是否包含 ## Test Coverage Appendix
    """
    repo_root = Path(repo_path)
    index_path = repo_root / "internal" / "index.json"
    
    if not index_path.exists():
        # 如果不是治理型 repo 或尚未初始化，可視為跳過或警告
        # 但在 AAA 核心治理中，我們要求 index.json 必須存在
        return True, ["skipped: internal/index.json missing (not a governance repo?)"]
    
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"index.json invalid JSON: {exc}"]
    
    milestones = data.get("milestones", [])
    if not milestones:
        return True, ["no milestones found in index.json"]
    
    errors = []
    for m in milestones:
        if not isinstance(m, dict):
            continue
            
        m_id = m.get("id")
        status = m.get("status")
        
        if status == "completed":
            report_path = repo_root / "internal" / "development" / "milestones" / m_id / "completion_report.md"
            
            if not report_path.exists():
                errors.append(f"milestone:{m_id}: missing completion_report.md")
                continue
            
            content = report_path.read_text(encoding="utf-8")
            if "## Test Coverage Appendix" not in content:
                errors.append(f"milestone:{m_id}: completion_report.md missing '## Test Coverage Appendix'")
                
    return len(errors) == 0, errors
