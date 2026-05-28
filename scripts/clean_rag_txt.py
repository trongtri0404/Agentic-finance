"""
Clean parsed text: remove XBRL noise, taxonomy URLs, and formatting artifacts.
Works for all 30 DJIA company reports.
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "rag_text"
OUTPUT_DIR = BASE_DIR / "data" / "rag_text_clean"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NOISE_PATTERNS = [
    r"^http://", r"^https://",
    r"^iso4217:", r"^xbrli:", r"^us-gaap:",
    r"^country:", r"^srt:", r"^stpr:", r"^utr:",
    r"^[a-z]{2,5}:",                          # generic XBRL prefix
    r"^\d{10}$",                               # CIK
    r"^\d{4}-\d{2}-\d{2}$",                   # date only
    r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}.*$",
    r"^P\d+Y$",                                # duration
    r"^(true|false|TRUE|FALSE)$",
    r"^[A-Z]{1,5}$",                           # short tokens
    r"^[\d\-\–\—\.\,\(\)]+$",                 # numbers only
]

IMPORTANT_MARKERS = [
    "UNITED STATES", "SECURITIES AND EXCHANGE COMMISSION", "FORM 10-K",
    "TABLE OF CONTENTS", "Item 1.", "Item 1A.", "Item 7.",
    "Risk Factors", "Business", "Management's Discussion",
]


def is_noise_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) <= 2:
        return True
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, s):
            return True
    if ("Member" in s or "member" in s) and len(s.split()) <= 4 and ":" in s:
        return True
    if "fasb.org" in s:
        return True
    return False


def find_start_index(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        for marker in IMPORTANT_MARKERS:
            if marker.lower() in line.lower():
                return i
    return 0


def clean_text(raw_text: str) -> str:
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in raw_text.split("\n")]
    start_idx = find_start_index(lines)
    lines = lines[start_idx:]

    cleaned = []
    prev = ""
    for line in lines:
        if is_noise_line(line) or len(line) < 3 or line == prev:
            continue
        cleaned.append(line)
        prev = line

    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    files = list(INPUT_DIR.glob("*.txt"))
    if not files:
        print(f"No text files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} text files")
    for infile in sorted(files):
        raw = infile.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_text(raw)
        outfile = OUTPUT_DIR / infile.name
        outfile.write_text(cleaned, encoding="utf-8")
        print(f"  [OK] {infile.name} -> {outfile.name} | {len(cleaned):,} chars")

    print(f"\nDone! {len(files)} files cleaned to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()