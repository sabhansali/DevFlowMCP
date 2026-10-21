from __future__ import annotations

import ast
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .security import (
    DISALLOWED,
    EXCLUDED,
    SecurityError,
    project_root,
    relative,
    safe_file,
)

mcp = FastMCP("DevFlow MCP Server")


def _files(root: Path, max_depth: int = 6, limit: int = 500) -> list[Path]:
    output: list[Path] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED for part in path.parts):
            continue
        if len(path.relative_to(root).parts) > max_depth:
            continue
        try:
            resolved = path.resolve()
            if resolved != root and root not in resolved.parents:
                continue
        except OSError:
            continue
        if path.is_file() and path.name not in DISALLOWED and path.suffix.lower() not in {".pem", ".key"}:
            if path.stat().st_size > 200_000:
                continue
            output.append(path)
            if len(output) >= limit:
                break
    return output


@mcp.tool()
def list_project_files(project_path: str, max_depth: int = 6, limit: int = 500) -> dict[str, Any]:
    root = project_root(project_path)
    files = _files(root, max(0, min(max_depth, 20)), max(1, min(limit, 2000)))
    suffixes: dict[str, int] = {}
    for path in files:
        suffix = path.suffix.lower() or "[no extension]"
        suffixes[suffix] = suffixes.get(suffix, 0) + 1
    return {"status": "success", "files": [relative(p, root) for p in files],
            "file_count": len(files), "directory_count": len({p.parent for p in files}),
            "file_types": suffixes}


@mcp.tool()
def read_project_file(project_path: str, file_path: str, start_line: int = 1, end_line: int = 200) -> dict[str, Any]:
    path = safe_file(project_path, file_path)
    if path.suffix.lower() not in {".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".ini", ".cfg"}:
        raise SecurityError("File type is not permitted for text reading")
    if start_line < 1 or end_line < start_line or end_line - start_line > 1000:
        raise ValueError("Invalid line range")
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected = lines[start_line - 1:end_line]
    return {"status": "success", "file_path": file_path, "start_line": start_line,
            "end_line": min(end_line, len(lines)), "line_count": len(lines),
            "content": "\n".join(selected)}


@mcp.tool()
def search_code(project_path: str, query: str, use_regex: bool = False,
                extensions: list[str] | None = None, limit: int = 200) -> dict[str, Any]:
    if not query or len(query) > 200:
        raise ValueError("Query must contain 1-200 characters")
    pattern = re.compile(query) if use_regex else None
    root = project_root(project_path)
    allowed = {x.lower() if x.startswith(".") else "." + x.lower() for x in (extensions or [".py", ".md", ".toml", ".txt"])}
    matches = []
    for path in _files(root, limit=2000):
        if path.suffix.lower() not in allowed:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            found = bool(pattern.search(line)) if pattern else query.lower() in line.lower()
            if found:
                matches.append({"file": relative(path, root), "line": number, "text": line[:300]})
                if len(matches) >= max(1, min(limit, 1000)):
                    return {"status": "success", "matches": matches, "match_count": len(matches)}
    return {"status": "success", "matches": matches, "match_count": len(matches)}


@mcp.tool()
def analyze_python_project(project_path: str) -> dict[str, Any]:
    root = project_root(project_path)
    files = [p for p in _files(root, limit=2000) if p.suffix == ".py"]
    findings: list[dict[str, Any]] = []
    functions: list[str] = []
    classes: list[str] = []
    imports: list[str] = []
    syntax_errors = []
    function_lengths = []
    for path in files:
        if path.stat().st_size > 200_000:
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            syntax_errors.append({"file": relative(path, root), "line": exc.lineno, "message": exc.msg})
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
                function_lengths.append({"file": relative(path, root), "name": node.name,
                                         "lines": (getattr(node, "end_lineno", node.lineno) - node.lineno + 1)})
                if ast.get_docstring(node) is None:
                    findings.append({"severity": "LOW", "category": "documentation",
                                     "file": relative(path, root), "line": node.lineno,
                                     "description": f"Function {node.name} has no docstring",
                                     "evidence": node.name, "heuristic": True})
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(alias.name for alias in node.names)
    return {"status": "success", "files_analyzed": len(files), "file_count": len(files),
            "function_count": len(functions), "class_count": len(classes), "functions": functions,
            "classes": classes, "imports": imports, "source_lines": sum(len(p.read_text(encoding="utf-8", errors="replace").splitlines()) for p in files),
            "function_lengths": function_lengths, "syntax_errors": syntax_errors, "findings": findings}


@mcp.tool()
def inspect_test_inventory(project_path: str) -> dict[str, Any]:
    root = project_root(project_path)
    files = _files(root, limit=2000)
    tests = [p for p in files if p.name.startswith("test_") or p.name.endswith("_test.py")]
    sources = [p for p in files if p.suffix == ".py" and "test" not in p.parts and not p.name.startswith("test_")]
    test_stems = {p.stem.removeprefix("test_").removesuffix("_test") for p in tests}
    gaps = [{"module": relative(p, root), "evidence": "No correspondingly named test module found",
             "severity": "MEDIUM", "heuristic": True} for p in sources if p.stem not in test_stems]
    return {"status": "success", "test_files": [relative(p, root) for p in tests],
            "test_count": len(tests), "source_modules": [relative(p, root) for p in sources],
            "potential_gaps": gaps}


@mcp.tool()
def run_project_tests(project_path: str, test_targets: list[str] | None = None,
                      timeout_seconds: int = 60, approved: bool = False) -> dict[str, Any]:
    if not approved:
        raise PermissionError("Explicit approval is required before running tests")
    root = project_root(project_path)
    targets = test_targets or ["tests"]
    resolved_targets = []
    for target in targets:
        candidate = (root / target).resolve()
        if candidate.is_file():
            resolved_targets.append(str(safe_file(project_path, target, max_size=10_000_000)))
        else:
            resolved_targets.append(str(project_root(str(candidate))))
    command = [sys.executable, "-m", "pytest", *resolved_targets, "-q"]
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, check=False, cwd=root, stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True,
                                   timeout=max(1, min(timeout_seconds, 600)), shell=False)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        partial_output = ((exc.stdout or b"") if isinstance(exc.stdout, bytes) else (exc.stdout or "")) + "\n"
        partial_output += (exc.stderr or b"") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"status": "timed_out", "exit_code": None, "passed": 0, "failed": 0, "skipped": 0,
                "duration_seconds": time.perf_counter() - started, "output": partial_output[-2000:],
                "error_category": "timeout"}
    output = (completed.stdout + "\n" + completed.stderr)[-4000:]
    summary = re.search(r"(?:(\d+)\s+failed).*?(?:(\d+)\s+passed).*?(?:(\d+)\s+skipped)|(?:(\d+)\s+passed).*?(?:(\d+)\s+failed).*?(?:(\d+)\s+skipped)", output, re.DOTALL)
    if summary:
        values = [int(value or 0) for value in summary.groups()]
        failed_count = values[0] or values[4]
        passed_count = values[1] or values[3]
        skipped_count = values[2] or values[5]
    else:
        failed_count = passed_count = skipped_count = 0
    return {"status": "success" if completed.returncode == 0 else "failed", "exit_code": completed.returncode,
            "passed": passed_count, "failed": failed_count, "skipped": skipped_count,
            "duration_seconds": time.perf_counter() - started, "output": output, "timed_out": timed_out}


@mcp.tool()
def check_quality_rules(project_path: str) -> dict[str, Any]:
    root = project_root(project_path)
    findings = []
    passed = []
    if (root / "README.md").exists():
        passed.append("README.md present")
    else:
        findings.append({"severity": "MEDIUM", "category": "documentation", "file": "README.md",
                         "line": None, "description": "README.md is missing", "recommendation": "Add project documentation"})
    if (root / ".gitignore").exists():
        passed.append(".gitignore present")
    else:
        findings.append({"severity": "LOW", "category": "hygiene", "file": ".gitignore",
                         "line": None, "description": "Root .gitignore is missing", "recommendation": "Add generated-file exclusions"})
    if (root / ".env.example").exists():
        passed.append(".env.example present")
    for path in _files(root, limit=2000):
        if path.suffix != ".py":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.search(r"\b(password|secret|api[_-]?key|token)\s*=\s*['\"]", line, re.IGNORECASE):
                redacted = re.sub(r"(['\"])[^'\"]*\1", r"\1<redacted>\1", line[:240])
                findings.append({"severity": "HIGH", "category": "configuration", "file": relative(path, root),
                                 "line": line_no, "description": "Credential-like assignment detected (heuristic)",
                                 "evidence": redacted, "recommendation": "Use environment variables"})
    return {"status": "success", "passed": passed, "findings": findings,
            "checks_run": len(passed) + len(findings), "checks_failed": len(findings)}


@mcp.tool()
def generate_quality_report(project_path: str, results: dict[str, Any]) -> dict[str, Any]:
    findings = []
    for value in results.values():
        if isinstance(value, dict):
            findings.extend(value.get("findings", []))
            findings.extend(value.get("potential_gaps", []))
            findings.extend({
                "severity": "HIGH",
                "category": "syntax",
                "file": error.get("file"),
                "line": error.get("line"),
                "description": error.get("message", "Python syntax error"),
                "evidence": error.get("message", ""),
                "recommendation": "Fix the syntax error before release",
            } for error in value.get("syntax_errors", []))
    normalized_findings = []
    for finding in findings:
        file_path = finding.get("file") or finding.get("module", "")
        description = finding.get("description")
        if not description and finding.get("module"):
            description = f"Potential test-coverage gap for {finding['module']}"
        normalized_findings.append({
            "severity": finding.get("severity", "MEDIUM"),
            "category": finding.get("category", "coverage"),
            "file": file_path,
            "line": finding.get("line", ""),
            "description": description or "Potential repository issue",
            "evidence": finding.get("evidence", f"No correspondingly named test module found for {file_path}"),
            "recommendation": finding.get("recommendation", "Review test coverage for this module"),
            "heuristic": finding.get("heuristic", False),
        })
    tests = next((v for v in results.values() if isinstance(v, dict) and "passed" in v and "failed" in v), None)
    has_code = any(isinstance(v, dict) and "function_count" in v for v in results.values())
    has_tests = tests is not None
    has_quality = any(isinstance(v, dict) and "checks_run" in v for v in results.values())
    has_documentation = has_quality
    categories = {"code_quality", "test_health", "security", "documentation"}
    available = {key for key, present in {
        "code_quality": has_code,
        "test_health": has_tests,
        "security": has_quality,
        "documentation": has_documentation,
    }.items() if present}
    score = None
    if len(available) == len(categories):
        deductions = sum({"CRITICAL": 30, "HIGH": 20, "MEDIUM": 10, "LOW": 3}.get(str(f.get("severity", "LOW")).upper(), 3) for f in normalized_findings)
        if tests and tests.get("failed", 0):
            deductions += 20
        score = max(0, min(100, 100 - deductions))
    blocking = any(str(f.get("severity", "")).upper() == "CRITICAL" for f in normalized_findings) or bool(tests and tests.get("failed"))
    return {"status": "success", "audit_status": "release_blocked" if blocking else ("complete" if score is not None else "incomplete"),
            "score": score, "available_categories": sorted(available), "missing_categories": sorted(set(categories) - available),
            "findings": normalized_findings, "test_result": tests, "release_gate": not blocking}


if __name__ == "__main__":
    mcp.run(transport="stdio")
