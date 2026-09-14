#!/usr/bin/env python3
"""Generate a Python module with the current git-based version string.

Usage:
  ./get_git_version.sh                 -> generates generated/version.py
  ./get_git_version.sh out/path.py     -> generates out/path.py
  ./get_git_version.sh -o out/path.py  -> same as above
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_git(git_cmd: str) -> str:
    args = git_cmd.split()
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def compute_version(no_sha: bool = False) -> str:
    fw_tag = run_git("describe --tags --abbrev=0 --always")
    fw_full_hash = run_git(f"rev-list -n 1 {fw_tag}")
    fw_num_commits = int(run_git(f"rev-list {fw_full_hash}..HEAD --count"))
    fw_sha = run_git("rev-parse --short=4 HEAD")

    fw_version = fw_tag
    if fw_num_commits != 0:
        fw_version = f"{fw_version}-{fw_num_commits}"
    
    if not no_sha:
        fw_version = f"{fw_version}-{fw_sha}"

    if "dirty" in run_git("describe --dirty"):
        fw_version = f"{fw_version}-dirty"

    return fw_version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("path", nargs="?")
    parser.add_argument("-o", "--output", dest="output")
    parser.add_argument("-r", "--reset", action="store_true", help="Reset settings if version has changed.")
    parser.add_argument("-n", "--no-sha", action="store_true", help="Remove SHA from version.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.path or "generated/version.py"

    fw_version = compute_version(args.no_sha)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # get the current year for the copyright notice
    last_commit_year = run_git("log -1 --format=%cd --date=format:'%Y'")
    # check reset flag and if version has changed, reset settings
    if args.reset:
        settings_reset = "True"
    else:
        settings_reset = "False"

    output_path.write_text(
        f'# This file is generated automatically by the script get_git_version.py and should not be edited manually.\n'
        f'VERSION = "{fw_version}"\nLAST_COMMIT_YEAR = {last_commit_year}\nRESET_SETTINGS = {settings_reset}\n',
        encoding="utf-8"
    )
    # output_path.write_text(f'', encoding="utf-8")
    print(f"{fw_version}")


if __name__ == "__main__":
    main()
