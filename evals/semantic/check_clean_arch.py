#!/usr/bin/env python3
import sys
from pathlib import Path

# Add aaa-tools to path if running standalone
try:
    from aaa.engine.semantic import SemanticChecker
except ImportError:
    import site
    site.addsitedir(str(Path(__file__).resolve().parents[4] / "aaa-tools"))
    from aaa.engine.semantic import SemanticChecker

def main():
    """
    Semantic Check: Clean Architecture Violation (Network/DB calls in UI).
    """
    checker = SemanticChecker()
    found_violations = False
    
    print("🔍 Scanning for Clean Architecture violations...")
    
    # Heuristic: Identify "UI layers" by directory name
    ui_indicators = ["ui", "frontend", "view", "pages", "components"]
    
    # In a real workspace, we'd scan multiple repos. 
    # For this check, we'll scan the current working directory recursively.
    # We exclude common virtualenvs or hidden folders.
    
    for py_file in Path.cwd().rglob("*.py"):
        if any(part.startswith(".") for part in py_file.parts):
            continue
        if "venv" in str(py_file):
            continue
            
        # Determine if file is in a "UI Layer"
        is_ui = any(indicator in part.lower() for part in py_file.parts for indicator in ui_indicators)
        
        if not is_ui:
            continue
            
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        
        # Rule: UI should not import database or network directly
        # Keywords to filter first (Hybrid Strategy)
        forbidden_keywords = ["sqlalchemy", "psycopg2", "sqlite3", "requests", "boto3", "pymongo"]
        
        result = checker.check(
            content, 
            "UI layer must not access database or network directly. Use Service Layer instead.", 
            keywords=forbidden_keywords
        )
        
        if not result.passed:
            rel_path = py_file.relative_to(Path.cwd())
            print(f"❌ Violation in {rel_path}: {result.reason} (Cost: {result.cost})")
            found_violations = True

    if found_violations:
        print("Result: FAIL")
        sys.exit(1)
    else:
        print("Result: PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
