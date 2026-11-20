#!/usr/bin/env python3
"""Sync Casks/deskset.rb with the latest published release of jokyme/Deskset."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.request

REPO = "jokyme/Deskset"
CASK_PATH = pathlib.Path(__file__).resolve().parent.parent / "Casks" / "deskset.rb"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_semver_key(version: str) -> tuple[int, int, int, int, tuple[tuple[int, int | str], ...]]:
    match = SEMVER_RE.match(version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version}")
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    prerelease = match.group(4)
    if prerelease is None:
        return (major, minor, patch, 1, ())
    parts: list[tuple[int, int | str]] = []
    for identifier in prerelease.split("."):
        if identifier.isdigit():
            parts.append((0, int(identifier)))
        else:
            parts.append((1, identifier))
    return (major, minor, patch, 0, tuple(parts))


def fetch_bytes(url: str) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "jokyme-homebrew-tap-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_latest_release() -> tuple[str, str, str]:
    raw = fetch_bytes(f"https://api.github.com/repos/{REPO}/releases/latest")
    release = json.loads(raw.decode("utf-8"))
    if release.get("draft") or release.get("prerelease"):
        raise RuntimeError("Latest release is marked draft or prerelease.")

    tag = release.get("tag_name", "")
    if not tag.startswith("v"):
        raise RuntimeError(f"Unexpected tag_name without leading 'v': {tag!r}")
    version = tag[1:]
    parse_semver_key(version)

    assets = {asset["name"]: asset for asset in release.get("assets", [])}
    arm_name = f"Deskset-{version}-arm64.dmg"
    intel_name = f"Deskset-{version}-x86_64.dmg"
    sums_name = "SHA256SUMS.txt"
    for required in (arm_name, intel_name, sums_name):
        if required not in assets:
            raise RuntimeError(f"Release {tag} is missing asset {required}")

    sums_text = fetch_bytes(assets[sums_name]["browser_download_url"]).decode("utf-8")
    checksums: dict[str, str] = {}
    for line in sums_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        digest, filename = parts[0].lower(), parts[1].lstrip("*")
        checksums[filename] = digest

    def verified_sha(name: str) -> str:
        sha = checksums.get(name, "")
        if not SHA256_RE.match(sha):
            raise RuntimeError(f"Missing or invalid SHA-256 for {name} in {sums_name}")
        api_digest = (assets[name].get("digest") or "").lower()
        if api_digest.startswith("sha256:") and api_digest.removeprefix("sha256:") != sha:
            raise RuntimeError(f"Digest mismatch for {name}: API={api_digest} vs {sums_name}={sha}")
        return sha

    return version, verified_sha(arm_name), verified_sha(intel_name)


def read_current_cask(text: str) -> tuple[str, str, str]:
    ver_match = re.search(r'^\s*version\s+"([^"]+)"', text, re.MULTILINE)
    sha_match = re.search(
        r'^\s*sha256\s+arm:\s+"([0-9a-f]{64})",\s*\n\s*intel:\s+"([0-9a-f]{64})"',
        text,
        re.MULTILINE,
    )
    if not ver_match or not sha_match:
        raise RuntimeError(f"Could not parse version/sha256 from {CASK_PATH}")
    return ver_match.group(1), sha_match.group(1), sha_match.group(2)


def render_updated_cask(text: str, version: str, arm_sha: str, intel_sha: str) -> str:
    updated, ver_count = re.subn(
        r'(^\s*version\s+)"[^"]+"',
        rf'\g<1>"{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    updated, sha_count = re.subn(
        r'(^\s*sha256\s+arm:\s+)"[0-9a-f]{64}",(\s*\n\s*intel:\s+)"[0-9a-f]{64}"',
        rf'\g<1>"{arm_sha}",\g<2>"{intel_sha}"',
        updated,
        count=1,
        flags=re.MULTILINE,
    )
    if ver_count != 1 or sha_count != 1:
        raise RuntimeError("Failed to update version or sha256 in cask content.")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-downgrade", action="store_true", help="Allow rolling back to an older version.")
    parser.add_argument("--check", action="store_true", help="Verify Casks/deskset.rb matches the latest release.")
    args = parser.parse_args()

    cask_text = CASK_PATH.read_text(encoding="utf-8")
    current_version, current_arm, current_intel = read_current_cask(cask_text)
    latest_version, latest_arm, latest_intel = fetch_latest_release()

    if args.check:
        if (current_version, current_arm, current_intel) != (latest_version, latest_arm, latest_intel):
            print(
                f"Check failed: cask has {current_version}, latest release is {latest_version}.",
                file=sys.stderr,
            )
            return 1
        print(f"Verified Casks/deskset.rb matches Deskset {latest_version}.")
        return 0

    if not args.allow_downgrade and parse_semver_key(latest_version) < parse_semver_key(current_version):
        raise RuntimeError(
            f"Refusing to downgrade Casks/deskset.rb from {current_version} to {latest_version} "
            "(pass --allow-downgrade to override)."
        )

    new_text = render_updated_cask(cask_text, latest_version, latest_arm, latest_intel)
    if new_text == cask_text:
        print(f"Casks/deskset.rb is already up to date ({latest_version}).")
        return 0

    CASK_PATH.write_text(new_text, encoding="utf-8")
    print(f"Updated Casks/deskset.rb from {current_version} to {latest_version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
