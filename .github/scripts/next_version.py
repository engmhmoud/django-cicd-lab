"""Next SemVer tag and release notes from Conventional Commits since the last v* tag.

Writes notes.md and prints GitHub step outputs (tag=..., previous=...). Rules:
  breaking (`type!:` or a `BREAKING CHANGE:` footer) -> major (minor while the major is 0)
  feat -> minor;  anything else -> patch
"""

import os
import re
import subprocess

TYPE = re.compile(r"^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!)?: (?P<desc>.+)$")
SECTIONS = [("breaking", "Breaking changes"), ("feat", "Features"), ("fix", "Fixes"), ("perf", "Performance")]


def git(*args):
    # fixed argv, no shell; "git" from PATH on the runner
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()  # noqa: S603, S607


def main():
    try:
        previous = git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*")
    except subprocess.CalledProcessError:
        previous = ""
    major, minor, patch = (int(x) for x in (previous[1:] if previous else "0.0.0").split("."))
    log = git("log", f"{previous}..HEAD" if previous else "HEAD", "--format=%s%x1f%b%x1e")
    groups = {key: [] for key, _ in SECTIONS} | {"other": []}
    bump = "patch"
    for entry in filter(None, (e.strip() for e in log.split("\x1e"))):
        subject, _, body = entry.partition("\x1f")
        m = TYPE.match(subject)
        breaking = bool(m and m["bang"]) or "BREAKING CHANGE:" in body
        if breaking:
            groups["breaking"].append(subject)
            bump = "major"
        elif m and m["type"] in groups:
            groups[m["type"]].append(m["desc"] + (f" ({m['scope']})" if m["scope"] else ""))
            if m["type"] == "feat" and bump == "patch":
                bump = "minor"
        else:
            groups["other"].append(subject)
    if bump == "major" and major == 0:
        bump = "minor"  # SemVer 0.x: anything may change; breaking changes bump the minor
    major, minor, patch = {
        "major": (major + 1, 0, 0),
        "minor": (major, minor + 1, 0),
        "patch": (major, minor, patch + 1),
    }[bump]
    tag = f"v{major}.{minor}.{patch}"

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    lines = [f"## {tag}", ""]
    for key, title in [*SECTIONS, ("other", "Other changes")]:
        if groups[key]:
            lines += [f"### {title}", *(f"- {item}" for item in groups[key]), ""]
    span = f"compare/{previous}...{tag}" if previous else f"commits/{tag}"
    lines.append(f"**Full changelog:** https://github.com/{repo}/{span}")
    with open("notes.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"tag={tag}")
    print(f"previous={previous or 'none'}")
    print(f"bump={bump}")


if __name__ == "__main__":
    main()
