"""Extract the text of a subject's source PDFs, page by page, for the AI study packs.

    python3 site/tools/extract_sources.py os D2 D3 D6 D7 Q3      # selected sources
    python3 site/tools/extract_sources.py os                     # every hosted source

Writes subjects/<slug>/source-text/<ID>.txt with pages separated by form feeds (\\f), page 1 first.
Needs pdftotext (poppler) locally; the Render build only reads the committed .txt files.
Scanned pages give little or no text: check the per-page report and transcribe those by hand if needed.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clean(page):
    lines = [l.rstrip() for l in page.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # slide decks are laid out wide; drop the common left indent of each page
    ind = min((len(l) - len(l.lstrip()) for l in text.split("\n") if l.strip()), default=0)
    return "\n".join(l[ind:] for l in text.split("\n")).strip()


def main():
    slug, ids = sys.argv[1], set(sys.argv[2:])
    d = os.path.join(ROOT, "subjects", slug)
    cfg = json.load(open(os.path.join(d, "subject.json")))
    out = os.path.join(d, "source-text")
    os.makedirs(out, exist_ok=True)
    for s in cfg.get("sources", []):
        if not s.get("file") or (ids and s["id"] not in ids):
            continue
        raw = subprocess.run(["pdftotext", "-layout", os.path.join(d, "sources", s["file"]), "-"],
                             capture_output=True, text=True, check=True).stdout
        pages = [clean(p) for p in raw.split("\f")]
        if pages and not pages[-1]:
            pages.pop()
        with open(os.path.join(out, s["id"] + ".txt"), "w") as f:
            f.write("\f".join(pages) + "\n")
        thin = [i + 1 for i, p in enumerate(pages) if len(p) < 40]
        print(f"{s['id']}: {len(pages)} pages, {sum(map(len, pages))} chars"
              + (f"; little or no text on pages {thin[:15]}{'…' if len(thin) > 15 else ''}" if thin else ""))


if __name__ == "__main__":
    main()
