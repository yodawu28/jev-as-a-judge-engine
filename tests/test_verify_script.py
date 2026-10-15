import os
import shutil
import subprocess
from pathlib import Path


def test_verify_script_passes_with_only_tracked_project_files(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    clean_repo = tmp_path / "clean-repo"
    clean_repo.mkdir()

    for relative_path in [
        ".gitignore",
        "CHANGELOG.md",
        "README.md",
        "pyproject.toml",
        "scripts",
        "src",
        "tests",
        "uv.lock",
    ]:
        source = root / relative_path
        target = clean_repo / relative_path
        if source.is_dir():
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "test_verify_script.py")
            shutil.copytree(source, target, ignore=ignore)
        else:
            shutil.copy2(source, target)

    env = os.environ.copy()
    env["UV_PROJECT_ENVIRONMENT"] = str(tmp_path / "venv")
    result = subprocess.run(
        ["bash", "scripts/verify.sh"],
        cwd=clean_repo,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr + result.stdout
