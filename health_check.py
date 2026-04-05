import sys
import os
import importlib
import importlib.util
import json
import shutil
from pathlib import Path


def file_exists(p: Path) -> bool:
    return p.exists()


def read_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return "<unreadable>"


def syntax_check(filepath: Path) -> (bool, str):
    try:
        source = filepath.read_text(encoding="utf-8")
        compile(source, str(filepath), "exec")
        return True, "OK"
    except SyntaxError as se:
        return False, f"SyntaxError: {se}"
    except Exception as e:
        return False, f"Error: {e}"


def try_import(module_path: str) -> (bool, str):
    try:
        if module_path in sys.modules:
            return True, "already imported"
        spec = importlib.util.find_spec(module_path)
        if spec is None:
            return False, f"Module not found: {module_path}"
        mod = importlib.import_module(module_path)
        return True, f"OK ({getattr(mod, '__name__', module_path)})"
    except Exception as e:
        return False, f"Import error: {e}"


def main():
    root = Path(".").resolve()
    report = {
        "python_version": sys.version,
        "cwd": str(root),
        "files": {
            "main_py": str(root / "main.py"),
            "requirements_txt": str(root / "requirements.txt"),
        },
        "virtualenv": bool((root / ".venv").exists()),
        "rg_available": bool(shutil.which("rg")),
        "node": {"present": bool(shutil.which("node")), "version": None},
        "npm": {"present": bool(shutil.which("npm")), "version": None},
        "imports": {},
        "syntax": {},
        "health": {},
    }

    # Node/NPM versions if present (best effort)
    if report["node"]["present"]:
        try:
            version = shutil.which("node")
            # We won't shell out for version to keep cross-platform simple
            report["node"]["version"] = version
        except Exception:
            report["node"]["version"] = None
    if report["npm"]["present"]:
        report["npm"]["version"] = None

    # Check syntax of main.py if available
    if file_exists(root / "main.py"):
        ok, msg = syntax_check(root / "main.py")
        report["syntax"]["main.py"] = {"ok": ok, "message": msg}
        report["health"]["syntax_main"] = ok
    else:
        report["syntax"]["main.py"] = {"ok": False, "message": "missing"}
        report["health"]["syntax_main"] = False

    # Try importing key modules to surface basic import issues
    modules_to_test = [
        "engines.brain_engine",
        "engines.speech_engine",
        "engines.audio_engine",
        "engines.command_engine",
        "modules.system_monitor",
        "modules.memory_manager",
        "modules.security_manager",
        "modules.emotion_manager",
        "ui.app_gui",
    ]
    for m in modules_to_test:
        ok, msg = try_import(m)
        report["imports"][m] = {"ok": ok, "message": msg}

    # Determine a small human-friendly health summary
    issues = []
    if not report["syntax"].get("main.py", {}).get("ok"):
        issues.append("Syntax error in main.py")
    for m, info in report["imports"].items():
        if not info["ok"]:
            issues.append(f"Import issue: {m} - {info['message']}")
    if report["node"]["present"] is False:
        issues.append("Node.js not found")
    if report["rg_available"] is False:
        issues.append("rg not found (ripgrep) for fast search")

    report["health"]["issues"] = issues
    report["health"]["status"] = len(issues) == 0

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
