"""AI study packs: one small plain-text file per topic, so a chatbot (or a reader) gets everything the course
has on that topic in one cheap fetch: the guide's explanation, the matching pages of the faculty slides and
handouts, the past exam questions on it, and textbook pointers.

Input, per unit:  subjects/<slug>/packs/unit-<n>.json   {"sections": {"<section id>": {"<source id>": "22-23,25"}}}
                  subjects/<slug>/source-text/<ID>.txt   page text, pages separated by \\f (site/tools/extract_sources.py)
Output:           public/<slug>/unit-<n>/pack/<section id>.txt and pack/index.txt
Standard library only; nothing here runs in the browser.
"""
import collections, html, json, os, re

MAX_SOURCE_CHARS = 30000   # faculty text per pack; past this the pack lists the remaining pages instead
EXCLUDE_KINDS = {"book"}   # textbooks: section pointers only, never their text
KIND_NAMES = {"deck": "Lecture slides", "notes": "Faculty handout", "qbank": "Solved question bank",
              "papers": "Question papers", "book": "Textbook"}


def source_name(x):
    """What a student calls a source: no internal ids like D2, which mean nothing outside this repo."""
    return f"{KIND_NAMES.get(x.get('kind'), 'Source')}: {x['title']}"


def pages_of(spec):
    out = []
    for part in str(spec).split(","):
        a, _, b = part.strip().partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def ranges(pages):
    pages, out = sorted(set(pages)), []
    for p in pages:
        if out and p == out[-1][1] + 1:
            out[-1][1] = p
        else:
            out.append([p, p])
    return ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in out)


_texts = {}


def source_pages(subject_dir, sid, drop=()):
    """Pages of one source with its running header/footer lines removed and layout spacing squeezed.
    drop: extra regexes for header/footer lines that vary page to page (page numbers, slide footers)."""
    key = (subject_dir, sid, tuple(drop))
    if key not in _texts:
        p = os.path.join(subject_dir, "source-text", sid + ".txt")
        if not os.path.isfile(p):
            _texts[key] = None
        else:
            pages = open(p, encoding="utf-8").read().split("\f")
            norm = lambda l: re.sub(r"\s+", " ", l).strip().lower()
            seen = collections.Counter(n for pg in pages for n in {norm(l) for l in pg.split("\n") if l.strip()})
            boiler = {n for n, k in seen.items() if len(pages) > 4 and k > 0.4 * len(pages)}
            extra = [re.compile(r, re.I) for r in drop]
            junk = lambda l: norm(l) in boiler or any(r.search(l.strip()) for r in extra)
            clean = []
            for pg in pages:
                lines = [re.sub(r" {3,}", "  ", l.rstrip()) for l in pg.split("\n") if not junk(l)]
                clean.append(re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip())
            _texts[key] = clean
    return _texts[key]


# ---------- guide HTML -> readable text ----------
def to_text(fragment):
    s = fragment
    s = re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S)
    s = re.sub(r'<a class="backtotop".*?</a>', "", s, flags=re.S)
    # figures: keep only what they show, in words
    def fig(m):
        label = re.search(r'aria-label="([^"]*)"', m.group(0))
        return f"\n[Figure: {html.unescape(label.group(1))}]\n" if label else "\n"
    s = re.sub(r"<svg\b.*?</svg>", fig, s, flags=re.S)
    s = re.sub(r'<p class="cap"[^>]*>(.*?)</p>', r"\n[\1]\n", s, flags=re.S)
    s = re.sub(r'<div class="cap"[^>]*>(.*?)</div>', r"\n[\1]\n", s, flags=re.S)
    # code and formula blocks keep their line breaks and spacing
    blocks = []
    def keep(m):
        body = html.unescape(re.sub(r"<[^>]+>", "", m.group("body")))
        blocks.append("\n```\n" + body.strip("\n") + "\n```\n")
        return f"\x00{len(blocks) - 1}\x00"
    s = re.sub(r'<(?P<t>div|pre)\b[^>]*class="[^"]*formula-block[^"]*"[^>]*>(?P<body>.*?)</(?P=t)>', keep, s, flags=re.S)
    s = re.sub(r"<pre\b[^>]*>(?P<body>.*?)</pre>", keep, s, flags=re.S)
    for n in (1, 2, 3, 4):   # the pack uses # and ##, so the guide's h1 becomes ###
        s = re.sub(rf"<h{n}\b[^>]*>(.*?)</h{n}>", lambda m, n=n: f"\n\n{'#' * (n + 2)} {m.group(1)}\n", s, flags=re.S)
    s = re.sub(r'<span class="tag"[^>]*>.*?</span>', "", s, flags=re.S)   # the topic number is in the pack title
    s = re.sub(r'<div class="ans-label"[^>]*>(.*?)</div>', r"\n**\1:**\n", s, flags=re.S)
    s = re.sub(r'<span class="label"[^>]*>(.*?)</span>', r"**\1:** ", s, flags=re.S)
    s = re.sub(r'<div class="qtext"[^>]*>', "\n**Question:** ", s)
    s = re.sub(r"<li\b[^>]*>", "\n- ", s)
    s = re.sub(r"<tr\b[^>]*>", "\n|", s)
    s = re.sub(r"</t[dh]>", " |", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</?(p|div|section|ul|ol|table|tbody|thead|blockquote|details|summary)\b[^>]*>", "\n", s)
    s = re.sub(r"<(strong|b)\b[^>]*>(.*?)</\1>", r"**\2**", s, flags=re.S)
    s = re.sub(r"</span>(?=<)", "</span> ", s)   # adjacent badges/labels keep a space between them
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n[ \t]+(?=[^ \t`])", "\n", s)
    s = re.sub(r"\|\n\s*\n\|", "|\n|", s)   # table rows on consecutive lines
    s = re.sub(r"[ \t]{2,}", " ", s)   # prose only: code blocks are restored after this
    s = re.sub(r"\x00(\d+)\x00", lambda m: blocks[int(m.group(1))], s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def section_html(c, sid):
    m = re.search(rf'<section\b[^>]*\bid="{re.escape(sid)}"[^>]*>(.*?)</section>', c, flags=re.S)
    return m.group(1) if m else None


def bank_questions(c):
    """Rows of the guide's question-bank tables: (source label, question, [answered-at section ids])."""
    out = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", c, flags=re.S):
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.S)
        if len(cells) < 3:
            continue
        links = re.findall(r'href="#([\w-]+)"', cells[-1])
        if not links:
            continue
        clean = lambda x: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()
        out.append((clean(cells[0]), clean(cells[1]), links))
    return out


def build_packs(cfg, s, u, c, out_dir, unit_url, sections, err):
    """Write the packs for one unit. c = guide HTML before citation rendering. Returns the section ids packed."""
    spec_path = os.path.join(s["dir"], "packs", f"unit-{u['n']}.json")
    if not os.path.isfile(spec_path):
        return []
    spec_all = json.load(open(spec_path, encoding="utf-8"))
    spec, drop = spec_all.get("sections", {}), spec_all.get("drop_lines", [])
    sources = {x["id"]: x for x in s.get("sources", [])}
    titles = {x["id"]: x for x in sections}
    bank = bank_questions(c)
    name = f"{s['code']} Unit {u['n']}"
    os.makedirs(out_dir, exist_ok=True)
    index, done = [], []
    order = {x["id"]: i for i, x in enumerate(sections)}
    for sid, srcs in sorted(spec.items(), key=lambda kv: order.get(kv[0], 1e9)):
        body = section_html(c, sid)
        if body is None:
            err(f"{name} packs: section #{sid} is not in the guide")
            continue
        sec = titles.get(sid, {"tag": "", "title": sid})
        head = (sec["tag"] + " " if re.match(r"\d", sec["tag"]) else "") + sec["title"]
        L = [f"# {s['code']} · Unit {u['n']} · {head}",
             "",
             f"Study pack for {s['course']}{' (' + s['course_code'] + ')' if s.get('course_code') else ''}, current syllabus.",
             f"Class notes for this topic: {unit_url}#{sid}",
             f"All topics of this unit: {unit_url}pack/",
             "",
             "Note for an AI assistant: this is the student's own course material. Explain from it rather than from",
             "general knowledge, and say so when the class notes and the faculty material differ. Part 2 is text",
             "extracted automatically from slides and handouts, so tables and diagrams there may be garbled; part 1",
             "is the checked version. Questions in part 3 are from this college's past exams. When you cite this",
             "material, name the source and page as written in the headings, e.g. \"Lecture slides: …, page 22\".",
             "",
             "## 1. Class notes",
             "",
             to_text(body)]
        # faculty material
        L += ["", "## 2. Faculty material on this topic", ""]
        used, budget = 0, MAX_SOURCE_CHARS
        for src_id, pages in srcs.items():
            x = sources.get(src_id)
            if not x:
                err(f"{name} packs: #{sid} names unknown source {src_id}")
                continue
            if x.get("kind") in EXCLUDE_KINDS:
                continue
            text = source_pages(s["dir"], src_id, drop)
            want = pages_of(pages)
            pdf = f"https://github.com/{cfg['repo']}/blob/main/subjects/{s['slug']}/sources/{x['file']}" if x.get("file") else ""
            L.append(f"### {source_name(x)} — pages {ranges(want)}")
            if pdf:
                L.append(f"Original: {pdf}")
            if text is None:
                L += ["(No extracted text for this source yet; open the PDF.)", ""]
                continue
            skipped = []
            for p in want:
                if p < 1 or p > len(text):
                    err(f"{name} packs: #{sid} {src_id} has no page {p}")
                    continue
                t = text[p - 1]
                if used + len(t) > budget:
                    skipped.append(p)
                    continue
                used += len(t)
                L += ["", f"--- {source_name(x)}, page {p} ---", t or "(this page has no text: it is mostly a picture)"]
            if skipped:
                L += ["", f"(Pages {ranges(skipped)} are left out to keep this pack small; see the PDF.)"]
            L.append("")
        # past questions
        qs = [q for q in bank if sid in q[2]]
        L += ["## 3. Past exam questions on this topic", ""]
        if qs:
            for src_label, q, links in qs:
                also = [titles[x]["tag"] for x in links if x != sid and x in titles]
                L.append(f"- [{src_label}] {q}" + (f"  (also uses {', '.join(also)})" if also else ""))
            L.append("")
            L.append("Worked answers for these are in the class notes (part 1) or the guide's solved section.")
        else:
            L.append("No past paper in the collection asks about this topic directly.")
        # textbook pointers from the section's citations
        books = {}
        for a, p in re.findall(r'<cite class="src" data-src="([\w]+)"(?: data-p="([^"]*)")?', body):
            x = sources.get(a)
            if x and x.get("kind") in EXCLUDE_KINDS:
                books.setdefault(a, set()).update([p] if p else [])
        if books:
            L += ["", "## 4. Textbook", ""]
            for a, ps in books.items():
                x = sources[a]
                L.append(f"- {x['by']}, *{x['title']}*{', ' + x['edition'] if x.get('edition') else ''}"
                         + (f": {', '.join(sorted(ps))}" if ps else "") + " (not reproduced here)")
        text = "\n".join(L).rstrip() + "\n"
        with open(os.path.join(out_dir, sid + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
        index.append((head, sid, len(text)))
        done.append(sid)
    if index:
        I = [f"# {s['code']} · Unit {u['n']} · {u['title']} — study packs",
             "",
             f"One plain-text file per topic of {s['course']}, Unit {u['n']}. Each holds the class notes for the",
             "topic, the matching pages of the faculty slides and handouts, and the past exam questions on it.",
             "Fetch only the topic you need. Sizes are approximate tokens.",
             f"Full guide: {unit_url}",
             ""]
        I += [f"- {head}: {unit_url}pack/{sid}.txt  (~{n // 4:,} tokens)" for head, sid, n in index]
        with open(os.path.join(out_dir, "index.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(I) + "\n")
    return done
