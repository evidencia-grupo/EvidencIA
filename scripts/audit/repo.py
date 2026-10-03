"""Read-only repository access abstractions for documentation and code repos."""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class RepoAccess:
    """Provides safe, strictly read-only inspection of both repositories."""

    def __init__(self, docs_repo: Path | str, code_repo: Path | str) -> None:
        self.docs_path = Path(docs_repo).resolve()
        self.code_path = Path(code_repo).resolve()

        if not self.docs_path.exists():
            raise FileNotFoundError(f"Docs repository path does not exist: {self.docs_path}")
        if not self.code_path.exists():
            raise FileNotFoundError(f"Code repository path does not exist: {self.code_path}")

    # -------------------------------------------------------------------------
    # File Reading & Existence
    # -------------------------------------------------------------------------

    def docs_exists(self, rel_path: str | Path) -> bool:
        return (self.docs_path / rel_path).exists()

    def code_exists(self, rel_path: str | Path) -> bool:
        return (self.code_path / rel_path).exists()

    def read_docs(self, rel_path: str | Path) -> Optional[str]:
        target = self.docs_path / rel_path
        if not target.is_file():
            return None
        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return target.read_text(encoding="latin-1", errors="replace")

    def read_code(self, rel_path: str | Path) -> Optional[str]:
        target = self.code_path / rel_path
        if not target.is_file():
            return None
        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return target.read_text(encoding="latin-1", errors="replace")

    def read_json_docs(self, rel_path: str | Path) -> Optional[Any]:
        content = self.read_docs(rel_path)
        if content is None:
            return None
        try:
            return json.loads(content)
        except Exception:
            return None

    def read_json_code(self, rel_path: str | Path) -> Optional[Any]:
        content = self.read_code(rel_path)
        if content is None:
            return None
        try:
            return json.loads(content)
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Git Introspection (Read-Only)
    # -------------------------------------------------------------------------

    def get_commit_sha(self, repo_type: str = "code") -> str:
        root = self.docs_path if repo_type == "docs" else self.code_path
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def get_tags(self, repo_type: str = "code") -> List[str]:
        root = self.docs_path if repo_type == "docs" else self.code_path
        try:
            res = subprocess.run(
                ["git", "tag"],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if res.returncode == 0:
                return [t.strip() for t in res.stdout.splitlines() if t.strip()]
        except Exception:
            pass
        return []

    def get_tracked_files(self, repo_type: str = "code") -> List[str]:
        """Lists files tracked by git. If not in a git repo, falls back to filesystem."""
        root = self.docs_path if repo_type == "docs" else self.code_path
        try:
            res = subprocess.run(
                ["git", "ls-files"],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                return [p.strip().replace("\\", "/") for p in res.stdout.splitlines() if p.strip()]
        except Exception:
            pass

        # Filesystem fallback (for mock/tmp_path repos without git initialized)
        files: List[str] = []
        ignored_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
            rel_dir = os.path.relpath(dirpath, root)
            for f in filenames:
                if rel_dir == ".":
                    files.append(f.replace("\\", "/"))
                else:
                    files.append(os.path.join(rel_dir, f).replace("\\", "/"))
        return files

    # -------------------------------------------------------------------------
    # AST Analysis Helper
    # -------------------------------------------------------------------------

    def parse_ast_code(self, rel_path: str | Path) -> Optional[ast.AST]:
        content = self.read_code(rel_path)
        if content is None:
            return None
        try:
            return ast.parse(content, filename=str(rel_path))
        except SyntaxError:
            return None
