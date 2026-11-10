#!/usr/bin/env python3
"""Build the multi-subject exam-notes website into ./public and validate it.

Standard library only (Render's build image just needs python3).
Exit code 1 = validation failed -> Render aborts the deploy and keeps the last good version live.

Layout it reads:
  site/site.json                     global title / subtitle / repo
  subjects/<slug>/subject.json       one per subject: units, changelog
  subjects/<slug>/<guide>.html       the published guides (only files listed in subject.json)
  subjects/<slug>/sources/*.pdf      registered faculty sources (served by GitHub only)
  site/sources.html                  source-register page template

Layout it writes:
  public/index.html                  all subjects
  public/<slug>/index.html           one subject's units
  public/<slug>/sources/index.html   source register with GitHub Open / Download links
  public/<slug>/unit-<n>/index.html  one guide, with the site toolbar injected
  public/search.json                 search index for every section of every guide

Usage (from the repo root):  python3 site/build.py
"""
import html, json, os, re, shutil, subprocess, sys
from datetime import date
from html.parser import HTMLParser
from urllib.parse import quote
from code_highlight import highlight_code_blocks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
SUBJECTS = os.path.join(ROOT, "subjects")
OUT = os.path.join(ROOT, "public")
errors = []
e = html.escape


def err(msg):
    errors.append(msg)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def version():
    v = os.environ.get("RENDER_GIT_COMMIT", "")
    if v:
        return v[:7]
    try:
        return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "local"


def human(d):
    y, m, dd = map(int, d.split("-"))
    return f"{dd} {date(y, m, dd):%b} {y}"


def js_str(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("</", "<\\/")


def fill(template, values, name):
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if left:
        err(f"{name}: unfilled placeholders {sorted(set(left))}")
    return template


# ---------- validation (same checks as the notes-maker Tier-1 script) ----------
TAGS = ["section", "div", "svg", "g", "table", "ul", "ol", "tr", "td", "th", "h1", "h2", "h3"]


def validate_unit(name, c):
    for t in TAGS:
        o = len(re.findall(r"<" + t + r"(\s|>)", c))
        cl = len(re.findall(r"</" + t + r">", c))
        if o != cl:
            err(f"{name}: <{t}> opened {o} times but closed {cl} times")
    ids = re.findall(r'id="([\w-]+)"', c)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        err(f"{name}: duplicate ids {dup[:8]}")
    broken = set(re.findall(r'href="#([\w-]+)"', c)) - set(ids)
    if broken:
        err(f"{name}: links to missing sections {sorted(broken)[:8]}")
    figs = re.findall(r'class="cap"[^>]*>\s*(?:<[^>]+>\s*)*Fig (\d+)([a-z]?)\.', c)
    keys = [(int(n), s) for n, s in figs]
    if keys != sorted(keys):
        err(f"{name}: figure captions out of order: {['%d%s' % k for k in keys]}")
    curved = re.findall(r'<path d="M[^"]*[QC][^"]*"[^>]*>', c)
    bad = [p for p in curved if "fill=" not in p]
    if bad:
        err(f"{name}: {len(bad)} curved <path> without fill=\"none\"")
    if re.search(r"</?(antml|thinking)\b|<cite\b", c):
        err(f"{name}: contains chat-formatting artifacts")
    if "</head>" not in c or "</body>" not in c:
        err(f"{name}: missing </head> or </body>")


# ---------- content extraction ----------
def plain(s):
    s = re.sub(r"<(svg|script|style)\b.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def sections(c):
    out = []
    for m in re.finditer(r'<section\b([^>]*)>(.*?)</section>', c, flags=re.S):
        attrs, body = m.group(1), m.group(2)
        idm = re.search(r'\bid="([\w-]+)"', attrs)
        if not idm or "section" not in attrs:
            continue
        tag = re.search(r'class="tag"[^>]*>(.*?)</span>', body, flags=re.S)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S)
        out.append({"id": idm.group(1), "tag": plain(tag.group(1)) if tag else "",
                    "title": plain(h1.group(1)) if h1 else idm.group(1), "text": plain(body)})
    return out


def unit_videos(name, c, entries):
    """Check videos.json entries against the guide and pack them small for the page."""
    bodies = {m.group(1): m.group(2) for m in
              re.finditer(r'<section\b[^>]*\bid="([\w-]+)"[^>]*>(.*?)</section>', c, flags=re.S)}
    out = []
    for x in entries:
        sid, h = x.get("section"), x.get("sub")
        if sid not in bodies:
            err(f"{name} videos.json: section #{sid} not in the guide")
            continue
        if h is not None and h not in [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", t))).strip()
                                       for t in re.findall(r"<h2[^>]*>(.*?)</h2>", bodies[sid], flags=re.S)]:
            err(f"{name} videos.json: heading not found in #{sid}: {h}")
            continue
        vids = []
        for v in x.get("videos", []):
            if not re.fullmatch(r"[\w-]{11}", v.get("id", "")):
                err(f"{name} videos.json: bad video id {v.get('id')!r}")
                continue
            vids.append([v["id"], v["title"], v["channel"], v.get("duration", ""),
                         v.get("kind", "topic"), v.get("note", ""), int(v.get("start") or 0)])
        if vids:
            out.append({"s": sid, "h": h or "", "v": vids})
            if x.get("label"):   # optional popup title, e.g. for the cover's revision videos
                out[-1]["l"] = x["label"]
    return out


def unit_slug(n):
    return "unit-" + re.sub(r"[^a-z0-9]+", "-", str(n).lower()).strip("-")


# ---------- loading ----------
REQUIRED_SUBJECT = ["code", "title", "course", "accent", "units", "changelog"]
REQUIRED_UNIT = ["n", "source", "title", "topics", "updated"]
SOURCE_KINDS = {"deck", "notes", "papers", "qbank", "lab", "book"}


def validate_sources(s):
    folder = os.path.join(s["dir"], "sources")
    listed, ids = set(), set()
    sources = s.get("sources", [])
    if not isinstance(sources, list):
        err(f"{s['slug']}: sources must be a list")
        s["sources"] = []
        return
    for x in sources:
        if not isinstance(x, dict):
            err(f"{s['slug']}: each source must be an object")
            continue
        sid = x.get("id", "")
        name = f"{s['slug']} source {sid}"
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Z]\d+", sid):
            err(f"{name}: invalid source ID")
            continue
        if sid in ids:
            err(f"{name}: duplicate source ID")
        ids.add(sid)
        if x.get("kind") not in SOURCE_KINDS:
            err(f"{name}: invalid source kind")
        if not isinstance(x.get("title"), str) or not x["title"].strip():
            err(f"{name}: missing title")
        if x.get("kind") == "book":
            if "file" in x:
                err(f"{name}: a book must have no file")
            continue
        f = x.get("file", "")
        if not isinstance(f, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.pdf", f):
            err(f"{name}: file must be a clean lowercase ASCII PDF name")
            continue
        listed.add(f)
        p = os.path.join(folder, f)
        if not os.path.isfile(p):
            err(f"{name}: missing PDF {f}")
        elif os.path.getsize(p) > 20_000_000:
            err(f"{name}: PDF exceeds 20 MB: {f}")
    actual = {os.path.relpath(os.path.join(d, f), folder) for d, _, fs in os.walk(folder)
              for f in fs if f.lower().endswith(".pdf")}
    for f in sorted(actual - listed):
        err(f"{s['slug']}: unlisted source PDF {f}")


def source_url(cfg, s, x, download=False):
    mode = "raw" if download else "blob"
    return f"https://github.com/{cfg['repo']}/{mode}/main/subjects/{s['slug']}/sources/{quote(x['file'])}"


def render_citations(name, content, s, cfg):
    """Replace only explicit, empty citation elements; preserve the rest byte for byte."""
    sources = {x['id']: x for x in s.get('sources', [])}

    class Citations(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.starts = [0]
            self.starts += [m.end() for m in re.finditer('\n', content)]
            self.opened = None
            self.edits = []

        def citation_position(self):
            line, col = self.getpos()
            return self.starts[line - 1] + col

        def handle_starttag(self, tag, attrs):
            if self.opened is not None:
                err(f'{name}: citation must be empty')
            if tag != 'cite':
                return
            a = dict(attrs)
            if self.opened is not None:
                err(f'{name}: nested citation')
                return
            self.opened = (self.citation_position(), a)
            if 'src' not in (a.get('class') or '').split():
                err(f'{name}: contains chat-formatting artifacts (unrecognized cite)')
            if len(a) != len(attrs) or set(a) - {'class', 'data-src', 'data-p'}:
                err(f'{name}: invalid citation attributes')
            if a.get('data-src') not in sources:
                err(f"{name}: unknown citation source {a.get('data-src')!r}")
            if 'data-p' in a and not re.fullmatch(r'§?[\d.]+(-[\d.]+)?', a['data-p'] or ''):
                err(f"{name}: invalid citation page {a['data-p']!r}")

        def handle_startendtag(self, tag, attrs):
            if tag == 'cite':
                err(f'{name}: citation needs an explicit closing tag')

        def handle_endtag(self, tag):
            if tag != 'cite':
                return
            if self.opened is None:
                err(f'{name}: citation closing tag without opening tag')
                return
            start, a = self.opened
            end = self.citation_position() + len('</cite>')
            inner = content[content.index('>', start) + 1:self.citation_position()]
            if inner:
                err(f'{name}: citation must be empty')
            self.opened = None
            x = sources.get(a.get('data-src'))
            if x is None:
                return
            page = a.get('data-p') or ''
            detail = page if page.startswith('§') else ('p.' + page if page else '')
            label = x['id'] + (' · ' + detail if detail else '')
            title = x['title'] + (', ' + detail if detail else '')
            href = (source_url(cfg, s, x) if x.get('file') else
                    f"{cfg['url']}/{s['slug']}/sources/#src-{x['id']}")
            external = ' target="_blank" rel="noopener"' if x.get('file') else ''
            self.edits.append((start, end, f'<a class="src-chip" href="{e(href)}" title="{e(title)}"{external}>{e(label)}</a>'))

    parser = Citations()
    parser.feed(content)
    parser.close()
    if parser.opened is not None:
        err(f'{name}: unclosed citation')
    for start, end, replacement in reversed(parser.edits):
        content = content[:start] + replacement + content[end:]
    return content


def source_groups(cfg, s):
    groups = [("Lecture decks & notes", {"deck", "notes"}), ("Question papers", {"papers"}),
              ("Question banks", {"qbank"}), ("Lab", {"lab"}), ("Textbooks", {"book"})]
    out = []
    for title, kinds in groups:
        rows = []
        for x in s.get("sources", []):
            if x["kind"] not in kinds:
                continue
            detail = " · ".join(filter(None, [x.get("by"), x.get("edition"),
                               "Units " + ", ".join(str(n) for n in x.get("units", []))]))
            links = ""
            if x.get("file"):
                size = os.path.getsize(os.path.join(s["dir"], "sources", x["file"])) / 1_000_000
                detail += f" · {size:.2f} MB"
                links = (f'<a class="btn" href="{e(source_url(cfg, s, x))}" target="_blank" rel="noopener">Open</a>'
                         f'<a class="btn" href="{e(source_url(cfg, s, x, True))}">Download</a>')
            elif x.get("url"):
                links = f'<a class="btn" href="{e(x["url"])}" target="_blank" rel="noopener">Read online ↗</a>'
            note = f'<p class="source-note">{e(x["note"])}</p>' if x.get("note") else ""
            rows.append(f'<article class="source-row" id="src-{e(x["id"])}">'
                        f'<span class="source-id">{e(x["id"])}</span><div class="source-info">'
                        f'<h3>{e(x["title"])}</h3><p>{e(detail)}</p>{note}</div>'
                        f'<div class="source-actions">{links}</div></article>')
        if rows:
            out.append(f'<section><h2 class="h">{e(title)}</h2>' + "\n".join(rows) + '</section>')
    return "\n".join(out)


def load_subjects():
    subs = []
    for slug in sorted(os.listdir(SUBJECTS)):
        d = os.path.join(SUBJECTS, slug)
        if not os.path.isdir(d):
            continue
        p = os.path.join(d, "subject.json")
        if not os.path.isfile(p):
            err(f"subjects/{slug}: missing subject.json")
            continue
        try:
            s = json.loads(read(p))
        except ValueError as ex:
            err(f"subjects/{slug}/subject.json: invalid JSON ({ex})")
            continue
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            err(f"subjects/{slug}: folder name must be lowercase letters, digits and dashes")
        missing = [k for k in REQUIRED_SUBJECT if k not in s]
        if missing:
            err(f"subjects/{slug}/subject.json: missing fields {missing}")
            continue
        s["slug"], s["dir"] = slug, d
        validate_sources(s)
        s["videos"] = {}
        vp = os.path.join(d, "videos.json")   # optional: YouTube links per section, shown by "Videos" buttons
        if os.path.isfile(vp):
            try:
                s["videos"] = json.loads(read(vp))["units"]
            except (ValueError, KeyError) as ex:
                err(f"subjects/{slug}/videos.json: invalid ({ex})")
        seen = set()
        for u in s["units"]:
            miss = [k for k in REQUIRED_UNIT if k not in u]
            if miss:
                err(f"{s['code']} unit {u.get('n', '?')}: missing fields {miss}")
            u["slug"] = unit_slug(u.get("n", "x"))
            if u["slug"] in seen:
                err(f"{s['code']}: two units map to /{u['slug']}/")
            seen.add(u["slug"])
            u.setdefault("accent", s["accent"])
        listed = {u.get("source") for u in s["units"]}
        stray = [f for f in os.listdir(d) if f.endswith(".html") and f not in listed]
        if stray:
            err(f"subjects/{slug}: HTML files not listed in subject.json (add them or remove them): {stray}")
        subs.append(s)
    subs.sort(key=lambda s: (s.get("order", 99), s["slug"]))
    if not subs:
        err("no subjects found under subjects/")
    return subs


def status(s):
    n, planned = len(s["units"]), s.get("planned")
    if n == 0:
        return "Notes in progress"
    if planned and n < planned:
        return f"{n} of {planned} units ready"
    return f"{n} unit{'s' if n != 1 else ''}"


def changelog_items(entries, code=None, slug=None, limit=10):
    out = []
    for entry in sorted(entries, key=lambda x: x["date"], reverse=True)[:limit]:
        tags = ""
        if code:
            tags += f'<a class="s" href="{slug}/">{e(code)}</a>'
        tags += "".join(f'<span class="u">U{e(str(k))}</span>' for k in entry.get("units", []))
        out.append(f'<li><time datetime="{entry["date"]}">{human(entry["date"])}</time>'
                   f'<div>{tags}{e(entry["text"])}</div></li>')
    return out


def main():
    cfg = json.loads(read(os.path.join(SITE, "site.json")))
    ver = version()
    chrome_t = read(os.path.join(SITE, "unit-chrome.html"))
    home_t = read(os.path.join(SITE, "home.html"))
    subject_t = read(os.path.join(SITE, "subject.html"))
    sources_t = read(os.path.join(SITE, "sources.html"))
    theme_js = read(os.path.join(SITE, "theme-links.js"))
    search_js = read(os.path.join(SITE, "search.js"))
    style = read(os.path.join(SITE, "landing.css"))
    code_style = read(os.path.join(SITE, "code-highlight.css"))
    # runs after each guide's own OS-preference script, so an explicit ?theme= wins before first paint
    theme_head = ("<script>(function(){try{var t=new URLSearchParams(location.search).get('theme');"
                  "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}})();</script>\n")

    # visitor counts (GoatCounter: no cookies, no login); skipped for localhost and saved copies
    gc = cfg.get("goatcounter")
    analytics = (f'<script data-goatcounter="https://{gc}.goatcounter.com/count" async '
                 f'src="https://gc.zgo.at/count.js"></script>') if gc else ""

    subjects = load_subjects()
    if errors:
        print("BUILD FAILED — nothing was deployed:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        sys.exit(1)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    search, subject_cards, all_log, built = [], [], [], {}
    for s in subjects:
        code, slug = s["code"], s["slug"]
        cards, labs = [], []
        for u in s["units"]:
            n, src = u["n"], os.path.join(s["dir"], u["source"])
            name = f"{code} Unit {n}"
            if not os.path.isfile(src):
                err(f"{name}: source file missing: subjects/{slug}/{u['source']}")
                continue
            c = read(src)
            c = render_citations(name, c, s, cfg)
            validate_unit(name, c)
            secs = sections(c)
            if not secs:
                err(f"{name}: no sections found (expected <section class=\"section\" id=...>)")
            ids = set(re.findall(r'id="([\w-]+)"', c))
            if u.get("lab") and u["lab"] not in ids:
                err(f"{name}: lab anchor #{u['lab']} not found")

            topics = [x for x in secs if re.match(r"\d", x["tag"])]
            nfig = len(set(re.findall(r'class="cap"[^>]*>\s*(?:<[^>]+>\s*)*Fig (\d+[a-z]?)\.', c)))
            nq = len(re.findall(r'class="qbox"', c))
            path = f"{slug}/{u['slug']}/"

            for x in secs:
                search.append({"s": slug, "c": code, "n": str(n), "g": x["tag"], "t": x["title"],
                               "u": f"{path}#{x['id']}", "x": x["text"][:3000]})

            vids = unit_videos(name, c, s["videos"].get(str(n), []))
            chrome = fill(chrome_t, {
                "VIDEOS_JSON": json.dumps(vids, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") if vids else "null",
                "UPDATED_HUMAN": human(u["updated"]), "UPDATED": u["updated"], "VERSION": ver,
                "ANALYTICS": analytics, "REPO": cfg["repo"], "CODE": e(code), "CODE_JS": js_str(code), "CODE_Q": code.replace(" ", "+"),
                "UNIT_N": e(str(n)), "UNIT_N_JS": js_str(n), "UNIT_N_Q": str(n).replace(" ", "+"),
                "UNIT_TITLE_JS": js_str(u["title"]), "DOWNLOAD_NAME": e(u["source"], quote=True),
                "COURSE_JS": js_str(s["course"]), "COURSE_CODE_JS": js_str(s.get("course_code", "")),
                "SITE_URL": cfg["url"], "PAGE_URL_JS": js_str(f'{cfg["url"]}/{slug}/{u["slug"]}/'),
                "SUBJECT_SLUG": slug,
            }, name + " toolbar")
            page = c
            if slug in {"os", "dsa"}:
                page = highlight_code_blocks(page)
                page = page.replace("</head>", "<style>\n" + code_style + "</style>\n</head>", 1)
            page = page.replace("</head>", '<meta name="robots" content="noindex, nofollow">\n' + theme_head + "</head>", 1)
            i = page.rfind("</body>")
            page = page[:i] + chrome + "\n<script>" + theme_js + "</script>\n" + page[i:]
            write(os.path.join(OUT, slug, u["slug"], "index.html"), page)
            built[path] = set(re.findall(r'id="([\w-]+)"', page))

            stats = [f"{len(topics)} topics", f"{nfig} diagrams", f"{nq} worked examples", f"updated {human(u['updated'])}"]
            cards.append(
                f'<div class="unit" style="--accent:{u["accent"]}"><div class="no">UNIT {e(str(n))}</div>'
                f'<div><h3><a href="{u["slug"]}/">{e(u["title"])}</a></h3><div class="topics">{e(u["topics"])}</div>'
                f'<div class="stats">{"".join("<span>" + x + "</span>" for x in stats)}</div></div>'
                f'<div class="acts"><a class="btn primary" href="{u["slug"]}/">Open</a>'
                f'<a class="btn" href="{u["slug"]}/index.html" download="{e(u["source"], quote=True)}">Download</a></div></div>')
            if u.get("lab"):
                labs.append(f'      <li><a href="{u["slug"]}/#{u["lab"]}">Unit {e(str(n))} — {e(u["title"])}</a></li>')

        if not s["units"]:
            cards.append('<div class="empty">The notes for this subject are still being written. '
                         'Units appear here as soon as they are finished.</div>')
        log = changelog_items(s["changelog"])
        if not log:
            log = ['<li class="none">Nothing yet.</li>']
        all_log += [dict(x, code=code, slug=slug) for x in s["changelog"]]
        dates = [u["updated"] for u in s["units"]] + [x["date"] for x in s["changelog"]]
        latest = max(dates) if dates else None

        labs_box = ""
        if labs:
            labs_box = '  <div class="box">\n    <h3>Lab programs</h3>\n    <ul>\n' + "\n".join(labs) + "\n    </ul>\n  </div>"
        page = fill(subject_t, {
            "STYLE": style, "TITLE": e(s["title"]), "COURSE": e(s["course"]), "CODE": e(code),
            "SUBTITLE": e(s.get("subtitle", "")), "SITE_TITLE": e(cfg["title"]),
            "UPDATED": f"Last updated <b>{human(latest)}</b>" if latest else "<b>In progress</b>",
            "ANALYTICS": analytics, "VERSION": ver, "REPO": cfg["repo"], "ISSUE_Q": code.replace(" ", "+"),
            "UNITS": "\n".join(cards), "CHANGELOG": "\n".join(log), "LABS_BOX": labs_box,
            "THEME_LINKS": theme_js, "SEARCH_JS": search_js, "SEARCH_BASE": "../", "SEARCH_SCOPE": js_str(slug),
            "SEARCH_HINT": e(s.get("search_hint", "e.g. a topic, algorithm or definition")),
            "HIDE_IF_EMPTY": "" if s["units"] else " hidden",
        }, f"{code} landing")
        write(os.path.join(OUT, slug, "index.html"), page)

        source_page = fill(sources_t, {
            "STYLE": style, "TITLE": e(s["title"]), "CODE": e(code), "SITE_TITLE": e(cfg["title"]),
            "SOURCES": source_groups(cfg, s), "THEME_LINKS": theme_js, "ANALYTICS": analytics,
        }, f"{code} sources")
        write(os.path.join(OUT, slug, "sources", "index.html"), source_page)
        source_path = f"{slug}/sources/"
        built[source_path] = set(re.findall(r'id="([\w-]+)"', source_page))
        kind_labels = {"deck": "Lecture deck", "notes": "Faculty notes", "papers": "Question papers",
                       "qbank": "Question bank", "lab": "Lab manual", "book": "Textbook"}
        for x in s.get("sources", []):
            search.append({"s": slug, "c": code, "n": "", "g": "Source " + x["id"],
                           "t": x["title"], "u": source_path + "#src-" + x["id"],
                           "x": " ".join([kind_labels[x["kind"]], x["title"], x.get("by", ""), x.get("note", "")])})

        e_course = e(s["course"]) + (f' <span class="cc">{e(s["course_code"])}</span>' if s.get("course_code") else "")
        ready = "ready" if s["units"] else "wip"
        subject_cards.append(
            f'<a class="subject {ready}" href="{slug}/" style="--accent:{s["accent"]}">'
            f'<div class="code">{e(code)}</div><h3>{e_course}</h3>'
            f'<div class="status">{e(status(s))}' + (f' · updated {human(latest)}' if latest and s["units"] else "") + '</div>'
            + (f'<div class="units-list">{" · ".join(e(u["title"]) for u in s["units"])}</div>' if s["units"] else "")
            + '</a>')

    dates = [x["date"] for x in all_log] + [u["updated"] for s in subjects for u in s["units"]]
    latest = max(dates) if dates else date.today().isoformat()
    home_log = []
    for entry in sorted(all_log, key=lambda x: x["date"], reverse=True)[:12]:
        home_log += changelog_items([entry], code=entry["code"], slug=entry["slug"])
    home = fill(home_t, {
        "STYLE": style, "TITLE": e(cfg["title"]), "SUBTITLE": e(cfg["subtitle"]),
        "UPDATED_HUMAN": human(latest), "VERSION": ver, "REPO": cfg["repo"], "ANALYTICS": analytics,
        "SUBJECTS": "\n".join(subject_cards),
        "CHANGELOG": "\n".join(home_log) or '<li class="none">Nothing yet.</li>',
        "THEME_LINKS": theme_js, "SEARCH_JS": search_js, "SEARCH_BASE": "", "SEARCH_SCOPE": "",
    }, "home")
    write(os.path.join(OUT, "index.html"), home)
    write(os.path.join(OUT, "search.json"), json.dumps(search, ensure_ascii=False, separators=(",", ":")))
    write(os.path.join(OUT, "ask-ai.js"), read(os.path.join(SITE, "ask-ai.js")))
    # search engines and AI training crawlers stay out; the fetchers an AI chat uses when a
    # student pastes a link are let in, so the "Ask AI" link to the notes can be read
    write(os.path.join(OUT, "robots.txt"),
          "User-agent: ChatGPT-User\nUser-agent: Claude-User\nUser-agent: Perplexity-User\nAllow: /\n\n"
          "User-agent: *\nDisallow: /\n")
    write(os.path.join(OUT, "404.html"),
          '<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex">'
          '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Not found</title>'
          '<body style="font:16px system-ui;padding:48px 20px;max-width:640px;margin:auto">'
          '<h1>Page not found</h1><p><a href="/">Go to all subjects</a></p></body>')

    # every search link must point at a real section of a built page
    for x in search:
        p, _, anchor = x["u"].partition("#")
        if anchor not in built.get(p, set()):
            err(f"search link broken: {x['u']}")

    for d, _, fs in os.walk(OUT):
        for f in fs:
            if f.lower().endswith(".pdf"):
                err(f"public must contain no PDFs: {os.path.relpath(os.path.join(d, f), OUT)}")

    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    if errors:
        print("BUILD FAILED — nothing was deployed:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        sys.exit(1)
    summary = ", ".join(f"{s['code']} {len(s['units'])}" for s in subjects)
    print(f"OK: {len(subjects)} subjects ({summary} units), {len(search)} searchable sections, "
          f"{size/1024:.0f} KB total, version {ver}, latest update {latest}")


if __name__ == "__main__":
    main()
