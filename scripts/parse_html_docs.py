"""
Parse HTML annual reports (10-K) to plain text.
Handles all 30 DJIA company reports.
"""
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from pathlib import Path

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "rag_html"
OUTPUT_DIR = BASE_DIR / "data" / "rag_text"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def html_to_text(infile: Path, outfile: Path):
    html = infile.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    cleaned = "\n".join(lines)

    outfile.write_text(cleaned, encoding="utf-8")


def main():
    # Support both .html and .htm
    files = list(INPUT_DIR.glob("*.html")) + list(INPUT_DIR.glob("*.htm"))

    if not files:
        print(f"No HTML files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} HTML files")
    for file in sorted(files):
        out = OUTPUT_DIR / f"{file.stem}.txt"
        html_to_text(file, out)
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"  [OK] {file.name} -> {out.name} ({size_mb:.1f} MB)")

    print(f"\nDone! {len(files)} files converted to {OUTPUT_DIR}")
    print("All files parsed successfully!")


if __name__ == "__main__":
    main()