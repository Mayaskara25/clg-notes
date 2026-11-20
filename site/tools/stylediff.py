"""Show what a change does to the look of every guide, before you push it.

Builds a git revision (default HEAD) in a temporary worktree and the working tree as it is now, records
the computed style and size of every element in each unit page (light/dark x desktop/phone), and prints
which properties changed on how many elements, with one example each. Run it after editing
site/guide-base.css, site/sidebar-top.html, site/unit-chrome.html or a guide's own <style>.

    cd ~/clg/dsa && uv run python ~/clg/notes-site/site/tools/stylediff.py [--ref origin/main] [--only os/unit-3]

Needs Playwright (the ~/clg/dsa venv) and the bundled Chromium; never run `playwright install`.
Exit status 1 when something changed, so it can gate a script.
"""
import argparse, asyncio, collections, glob, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")
PROPS = ["color", "background-color", "font-family", "font-size", "font-weight", "font-style", "line-height",
         "margin", "padding", "border-top", "border-left", "border-radius", "display", "fill", "stroke",
         "stroke-width", "opacity", "text-align", "white-space", "tab-size", "box-shadow"]
# elements the site injects (toolbar, dialog, sidebar extras) are skipped: compare the guide content
DUMP = """(props)=>{const out={};const root=document.querySelector('.shell')||document.body;const seen={};
 for(const el of root.querySelectorAll('*')){
  if(el.closest('.site-side,.sd,.sitebar'))continue;
  const cs=getComputedStyle(el),r=el.getBoundingClientRect();
  const base=(el.id?'#'+el.id:'')+' '+el.tagName.toLowerCase()+'.'+(el.getAttribute('class')||'').trim().replace(/\\s+/g,'.');
  const n=seen[base]=(seen[base]||0)+1;const o={};for(const p of props)o[p]=cs.getPropertyValue(p);
  o.size=Math.round(r.width)+'x'+Math.round(r.height);out[base+' #'+n]=o}
 return out}"""
VIEWS = [(1400, "light"), (1400, "dark"), (390, "light"), (390, "dark")]


def build(root):
    r = subprocess.run([sys.executable, os.path.join(root, "site", "build.py")], cwd=root, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"build failed in {root}:\n{r.stdout}{r.stderr}")
    return os.path.join(root, "public")


async def dump(pub, only):
    from playwright.async_api import async_playwright
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for f in sorted(glob.glob(f"{pub}/*/unit-*/index.html")):
            unit = os.path.relpath(os.path.dirname(f), pub)
            if only and only not in unit:
                continue
            for w, theme in VIEWS:
                pg = await b.new_page(viewport={"width": w, "height": 900})
                await pg.goto(f"file://{f}?theme={theme}", wait_until="load")
                await pg.evaluate("document.fonts.ready")
                res[f"{unit} {theme} {w}px"] = await pg.evaluate(DUMP, PROPS)
                await pg.close()
        await b.close()
    return res


def report(a, b):
    changed_any = False
    for page in sorted(set(a) | set(b)):
        x, y = a.get(page, {}), b.get(page, {})
        if not x or not y:
            print(f"== {page}: only in {'new' if y else 'old'} build"); changed_any = True; continue
        props, ex = collections.Counter(), {}
        for k in x.keys() & y.keys():
            for p, v in x[k].items():
                if v != y[k].get(p):
                    props[p] += 1; ex.setdefault(p, (k, v, y[k].get(p)))
        gone, new = len(x.keys() - y.keys()), len(y.keys() - x.keys())
        if props or gone or new:
            changed_any = True
            print(f"== {page}: {len(x)} elements" + (f", {gone} gone, {new} new" if gone or new else ""))
            for p, n in props.most_common():
                k, o, nw = ex[p]
                print(f"   {p:16} {n:6}  e.g. {k[:60]}: {str(o)[:45]!r} -> {str(nw)[:45]!r}")
    print("no visible style changes" if not changed_any else "(size changes of a pixel or two are usually font rounding)")
    return changed_any


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", default="HEAD", help="git revision to compare against (default HEAD)")
    ap.add_argument("--only", default="", help="limit to units whose path contains this, e.g. os/unit-3")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="stylediff-")
    old_root = os.path.join(tmp, "old")
    try:
        subprocess.run(["git", "worktree", "add", "--detach", "-q", old_root, a.ref], cwd=ROOT, check=True)
        old = asyncio.run(dump(build(old_root), a.only))
        new = asyncio.run(dump(build(ROOT), a.only))
        print(f"comparing {a.ref} -> working tree")
        sys.exit(1 if report(old, new) else 0)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", old_root], cwd=ROOT, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
