from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.config import get_settings

LOGGER = logging.getLogger(__name__)

GIT_URL_RE = re.compile(r"^https://github.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$")


@dataclass(frozen=True)
class RepoMetadata:
    owner: str
    name: str
    default_branch: str
    sha: str

    @property
    def cache_dir(self) -> Path:
        settings = get_settings()
        return settings.cache_root / f"{self.owner}_{self.name}" / self.sha


class GitNotInstalledError(FileNotFoundError):
    pass


def _run_git(*args: str, cwd: Optional[Path] = None) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover
        raise GitNotInstalledError("Git executable not found. Please install Git and ensure it is in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        LOGGER.error("Git command failed: %s", exc.stderr.strip())
        raise ValueError(exc.stderr.strip()) from exc
    return completed.stdout.strip()


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    match = GIT_URL_RE.match(repo_url)
    if not match:
        raise ValueError("Only https://github.com/<owner>/<repo> URLs are supported")
    return match.group("owner"), match.group("repo")


def fetch_repo_metadata(repo_url: str) -> RepoMetadata:
    owner, name = parse_repo_url(repo_url)
    symref = _run_git("ls-remote", "--symref", repo_url, "HEAD")
    default_branch = "main"
    head_sha = ""
    for line in symref.splitlines():
        if line.startswith("ref:"):
            # Example line: "ref: refs/heads/main\tHEAD"
            # Extract branch from the "refs/heads/<branch>" token
            tokens = line.split()
            if len(tokens) >= 2 and "refs/heads/" in tokens[1]:
                default_branch = tokens[1].split("/")[-1]
        elif "HEAD" in line and "ref:" not in line:
            head_sha = line.split()[0]
    if not head_sha:
        head_sha = _run_git("ls-remote", repo_url, default_branch).split()[0]
    return RepoMetadata(owner=owner, name=name, default_branch=default_branch, sha=head_sha)


def ensure_cloned(repo_url: str, metadata: RepoMetadata) -> Path:
    cache_dir = metadata.cache_dir
    repo_path = cache_dir / "repo"
    if repo_path.exists():
        LOGGER.info("Using cached clone at %s", repo_path)
        return repo_path
    cache_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Cloning %s into %s", repo_url, repo_path)
    _run_git(
        "clone",
        "--depth",
        "1",
        "--branch",
        metadata.default_branch,
        repo_url,
        str(repo_path),
    )
    return repo_path
