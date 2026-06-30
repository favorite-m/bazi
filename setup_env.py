#!/usr/bin/env python3
"""
setup_env.py - Install project dependencies.

Called by install.bat after creating .venv.
Runs inside the project's virtual environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANTIAN = ROOT / ".reasonix" / "skills" / "cantian-bazi"


def log(msg: str, status: str = "OK"):
    """Print a formatted log line."""
    print(f"  [{status:4s}] {msg}")


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> bool:
    """Run a command, return True if successful."""
    kwargs = {"cwd": cwd or ROOT, "check": True,
              "timeout": timeout, "capture_output": False}
    try:
        if os.name == "nt":
            cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)
            subprocess.run(cmd_str, shell=True, **kwargs)
        else:
            subprocess.run(cmd, **kwargs)
        return True
    except subprocess.CalledProcessError:
        return False
    except (FileNotFoundError, OSError):
        return False


def pip_install(package: str) -> bool:
    """Install a pip package."""
    return run([sys.executable, "-m", "pip", "install", package, "-q"])


def main():
    has_errors = False

    print()
    print("============================================")
    print(" Installing Python packages")
    print("============================================")
    print()

    # Upgrade pip silently
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"])

    # Lunar-python (bazi engine)
    if pip_install("lunar-python"):
        log("lunar-python", "OK")
    else:
        log("lunar-python install failed", "FAIL")
        has_errors = True

    # PyYAML (archive manager)
    if pip_install("pyyaml"):
        log("pyyaml", "OK")
    else:
        log("pyyaml install failed", "FAIL")
        has_errors = True

    print()
    print("============================================")
    print(" Installing Node.js packages (cantian-bazi)")
    print("============================================")
    print()

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")

    if not node_path or not npm_path:
        log("Node.js not found, skipping JS dependencies", "SKIP")
    else:
        try:
            ver = subprocess.run(
                f'"{node_path}" --version',
                capture_output=True, text=True, shell=True, timeout=15
            ).stdout.strip()
            log(f"Node.js {ver}")
        except Exception:
            log("Could not get Node.js version", "WARN")

        if (CANTIAN / "node_modules").exists():
            log("cantian-bazi already installed", "OK")
        else:
            log("Running npm install...")
            if run([npm_path, "install", "--no-optional"], cwd=CANTIAN):
                log("cantian-bazi dependencies", "OK")
            else:
                log("npm install failed", "FAIL")
                has_errors = True


    print()
    print("============================================")
    if has_errors:
        print("  Setup finished with some errors.")
        print("  Check the log above for [FAIL] items.")
    else:
        print("  Setup complete!")
    print("============================================")
    print()

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
