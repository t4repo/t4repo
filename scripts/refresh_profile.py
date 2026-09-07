#!/usr/bin/env python3
"""Refreshes the generated sections of the profile README.

No third-party services, no tracking pixels, no external widget hosts — the
profile renders from this account's own data, fetched with the workflow token
and committed as plain text. Stdlib only.

Sections are delimited by HTML comment markers in README.md:
    <!-- REPOS:START --> … <!-- REPOS:END -->
    <!-- LANGS:START --> … <!-- LANGS:END -->
    <!-- META:START -->  … <!-- META:END -->
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = os.environ.get("PROFILE_USER", "t4repo")
README = Path(os.environ.get("PROFILE_README", "README.md"))
API = "https://api.github.com"

# Repos that should never appear in Selected work.
EXCLUDE = {USER, ".github", f"{USER}.github.io"}
# Curated display order for Selected work. Anything not listed falls in behind,
# ranked by stars then recency. Reorder this list to reorder the profile.
PRIORITY = [
    "OrderManagementSystem",
    "library-managment-db",
    "Thebestoo-ak4yhud-Fully-fixed",
    "Thebestoo-Fivem-Old-Benny-UI-esx",
    "thebesto-drugcreator",
]
MAX_REPOS = 6
MAX_LANGS = 6
BAR_WIDTH = 24


def api(path: str):
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"{USER}-profile-refresh",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"::warning::GET {path} -> {e.code} {e.reason}", file=sys.stderr)
        return None


def fetch_repos() -> list[dict]:
    out, page = [], 1
    while page <= 5:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&sort=pushed")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [
        r for r in out
        if not r.get("fork") and not r.get("archived") and not r.get("private")
        and r["name"] not in EXCLUDE
    ]


def _neg(iso: str) -> str:
    """Sort key that orders ISO timestamps newest-first inside an ascending sort."""
    return "".join(chr(0x7E - ord(c) % 0x7E) for c in iso)


def month(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")


def render_repos(repos: list[dict]) -> str:
    def rank(r):
        try:
            curated = PRIORITY.index(r["name"])
        except ValueError:
            curated = len(PRIORITY)
        # Curated first (ascending), then stars and recency (descending).
        return (curated, -r.get("stargazers_count", 0), _neg(r.get("pushed_at", "")))

    ranked = sorted(repos, key=rank)[:MAX_REPOS]
    if not ranked:
        return "_No public repositories to show yet._"

    lines = []
    for r in ranked:
        desc = (r.get("description") or "").strip().rstrip(".")
        facts = []
        if r.get("language"):
            facts.append(f"`{r['language']}`")
        if r.get("stargazers_count"):
            facts.append(f"`★ {r['stargazers_count']}`")
        if r.get("pushed_at"):
            facts.append(f"updated {month(r['pushed_at'])}")
        # Two trailing spaces: a hard break in CommonMark, and harmless on
        # GitHub whether or not it treats the newline as a break already.
        lines.append(f"**[{r['name']}]({r['html_url']})**" + (f" — {desc}" if desc else "") + "  ")
        lines.append(f"<sub>{' · '.join(facts)}</sub>")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_langs(repos: list[dict]) -> str:
    totals: dict[str, int] = {}
    for r in repos:
        data = api(f"/repos/{USER}/{r['name']}/languages") or {}
        for lang, count in data.items():
            totals[lang] = totals.get(lang, 0) + int(count)
    grand = sum(totals.values())
    if not grand:
        return ""

    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:MAX_LANGS]
    width = max(len(name) for name, _ in top)
    rows = []
    for name, count in top:
        pct = 100.0 * count / grand
        filled = round(BAR_WIDTH * pct / 100.0)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        rows.append(f"{name.ljust(width)}  {bar}  {pct:5.1f}%")
    body = "\n".join(rows)
    return (
        "**Public code by language**\n\n"
        f"```text\n{body}\n```\n\n"
        "<sub>Measured across this account's own public repositories — forks excluded. "
        "It reflects what is open, not what pays the bills.</sub>"
    )


def render_meta(repos: list[dict]) -> str:
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    return (
        f"<sub>{len(repos)} public repositories · {stars} stars · "
        f"last refreshed {stamp} by "
        f"[a workflow in this repository](https://github.com/{USER}/{USER}/blob/main/"
        ".github/workflows/refresh-profile.yml).</sub>"
    )


def splice(text: str, tag: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!-- {tag}:START -->)(.*?)(<!-- {tag}:END -->)", re.DOTALL
    )
    if not pattern.search(text):
        print(f"::warning::marker {tag} not found in README", file=sys.stderr)
        return text
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)


def main() -> int:
    repos = fetch_repos()
    if not repos:
        print("No repositories fetched; leaving README untouched.")
        return 0

    original = README.read_text(encoding="utf-8")
    updated = splice(original, "REPOS", render_repos(repos))
    updated = splice(updated, "LANGS", render_langs(repos))
    updated = splice(updated, "META", render_meta(repos))

    if updated == original:
        print("README already current.")
        return 0
    README.write_text(updated, encoding="utf-8")
    print(f"README updated from {len(repos)} repositories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
