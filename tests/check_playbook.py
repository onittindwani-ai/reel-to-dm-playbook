#!/usr/bin/env python3
"""Check the Reel to DM Playbook files. Python 3 standard library only.

Run from anywhere:  python tests/check_playbook.py
Exit code 0 means every check passed.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "01-THE-PLAYBOOK.md",
    "02-KEYWORD-PICKER.md",
    "03-DM-TEMPLATES.md",
    "04-COMMENT-REPLY-VARIATIONS.md",
    "05-VYRAL-SETUP.md",
    "06-PROMPT-MAKE-YOUR-KIT.md",
    "07-LAUNCH-CHECKLIST.md",
    "templates/REEL-DM-TRACKER.csv",
    "LICENSE",
    "CHANGELOG.md",
    ".github/workflows/check.yml",
    "tests/check_playbook.py",
]

# Files where fill in slots like [THING] are expected.
SLOT_FILES = {
    "03-DM-TEMPLATES.md",
    "04-COMMENT-REPLY-VARIATIONS.md",
    "06-PROMPT-MAKE-YOUR-KIT.md",
}

CSV_HEADER = (
    "date,reel_topic,keyword,resource,link,comments,"
    "dms_sent,dm_replies,new_follows,notes"
)

# Built from code points so this file does not contain the characters itself.
BANNED_CHARS = {chr(0x2014): "em dash (U+2014)", chr(0x2013): "en dash (U+2013)"}

# Built from pieces so this file does not trip its own check.
PLACEHOLDER_WORDS = ["TO" + "DO", "T" + "BD", "lor" + "em"]
PLACEHOLDER_RE = re.compile(
    r"\b(" + "|".join(PLACEHOLDER_WORDS) + r")\b", re.IGNORECASE
)

# A slot is a square bracket holding an uppercase word, like [THING] or
# [GITHUB LINK]. Checkboxes "[ ]" / "[x]" and Markdown links "[text](url)"
# are not slots.
SLOT_RE = re.compile(r"\[[A-Z][A-Z0-9 ,'\"./:_-]*\](?!\()")

TEXT_SUFFIXES = {".md", ".csv", ".yml", ".yaml", ".py", ".txt"}


def text_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(ROOT).parts:
            continue
        if path.suffix in TEXT_SUFFIXES or path.name == "LICENSE":
            yield path


def outside_code_fences(text):
    """Yield (line_number, line) for lines not inside ``` fences."""
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield number, line


def check_required(errors):
    for name in REQUIRED_FILES:
        if not (ROOT / name).is_file():
            errors.append(f"missing file: {name}")


def check_text(errors):
    for path in text_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: not valid UTF-8")
            continue
        if text and not text.endswith("\n"):
            errors.append(f"{rel}: file does not end with a newline")
        for number, line in enumerate(text.splitlines(), start=1):
            for char, label in BANNED_CHARS.items():
                if char in line:
                    errors.append(f"{rel}:{number}: contains an {label}")
            match = PLACEHOLDER_RE.search(line)
            if match:
                errors.append(
                    f"{rel}:{number}: placeholder word '{match.group(0)}'"
                )


def check_markdown(errors):
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if ".git" in path.relative_to(ROOT).parts:
            continue
        text = path.read_text(encoding="utf-8")
        first = next((ln for ln in text.splitlines() if ln.strip()), "")
        if not first.startswith("# "):
            errors.append(f"{rel}: first line must be a top level '# ' heading")
        if rel in SLOT_FILES:
            continue
        for number, line in outside_code_fences(text):
            # Inline code like `[THING]` explains slots and is fine.
            plain = re.sub(r"`[^`]*`", "", line)
            slot = SLOT_RE.search(plain)
            if slot:
                errors.append(
                    f"{rel}:{number}: unfilled slot {slot.group(0)} "
                    "(slots belong only in 03, 04 and 06)"
                )


def check_csv(errors):
    path = ROOT / "templates" / "REEL-DM-TRACKER.csv"
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != CSV_HEADER:
        errors.append("templates/REEL-DM-TRACKER.csv: header does not match")
        return
    columns = len(CSV_HEADER.split(","))
    for number, line in enumerate(lines[1:], start=2):
        if line.strip() and len(line.split(",")) != columns:
            errors.append(
                f"templates/REEL-DM-TRACKER.csv:{number}: "
                f"expected {columns} columns"
            )


def main():
    errors = []
    check_required(errors)
    check_text(errors)
    check_markdown(errors)
    check_csv(errors)
    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for error in errors:
            print(f"  {error}")
        return 1
    print("PASS: all playbook checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
