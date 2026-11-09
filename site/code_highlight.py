"""Small build-time lexer for the guides' C, Java and C-like pseudocode.

Only explicitly marked .formula-block.code blocks are highlighted. Keeping the
markup and CSS inline makes downloaded guides work offline without JavaScript
or third-party assets. The Render build remains standard-library only.
"""
import html
import re


BLOCK = re.compile(
    r'<(?P<tag>div|pre)\b(?P<attrs>[^>]*\bclass="[^"]*\bformula-block\b[^"]*"[^>]*)>'
    r'(?P<body>.*?)</(?P=tag)>', re.S)
KEYWORDS = set("""
    auto break case class const continue default do else enum extern for goto if
    implements import interface monitor native new package private procedure
    protected public register restrict return sizeof static struct super switch
    synchronized this throw throws transient typedef union volatile while
    from downto to then end repeat until and or not
""".split())
TYPES = set("""
    bool boolean byte char double float int long short signed unsigned void
    condition item semaphore Semaphore String Thread Runnable
""".split())
LITERALS = {"true", "false", "null", "NULL", "TRUE", "FALSE"}
TOKEN = re.compile(r'''
    (?P<comment>//[^\n]*|/\*[\s\S]*?\*/)
  | (?P<string>"(?:\\[\s\S]|[^"\\\n])*"|'(?:\\[\s\S]|[^'\\\n])*')
  | (?P<directive>\#[ \t]*[A-Za-z_]\w*|(?<=\#include)[ \t]*<[^>\n]+>)
  | (?P<number>\b(?:0[xX][\da-fA-F]+|0[bB][01]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)[uUlLfF]*\b)
  | (?P<word>[A-Za-z_]\w*)
  | (?P<operator>[-+*/%=!<>~&|^?:]+)
''', re.X)


def highlight(text):
    """Escape all source text, then wrap lexical tokens without changing it."""
    out, end = [], 0
    for match in TOKEN.finditer(text):
        out.append(html.escape(text[end:match.start()], quote=False))
        value, kind = match.group(), match.lastgroup
        if kind == "word":
            if value in KEYWORDS:
                kind = "keyword"
            elif value in TYPES or value.endswith("_t"):
                kind = "type"
            elif value in LITERALS:
                kind = "constant"
            elif re.match(r'[ \t]*\(', text[match.end():]):
                kind = "function"
            elif re.fullmatch(r'[A-Z][A-Z_\d]*', value) and len(value) > 1:
                kind = "constant"
            elif re.fullmatch(r'[A-Z][a-zA-Z\d]*', value):
                kind = "type"
            else:
                kind = None
        escaped = html.escape(value, quote=False)
        out.append(f'<span class="syntax-{kind}">{escaped}</span>' if kind else escaped)
        end = match.end()
    out.append(html.escape(text[end:], quote=False))
    return "".join(out)


def highlight_code_blocks(guide):
    def replace(match):
        attrs, body = match["attrs"], match["body"]
        classes = re.search(r'\bclass="([^"]*)"', attrs).group(1).split()
        if "code" not in classes:
            return match.group()
        # Remove the older hand-colored spans before lexing the complete block,
        # so comments and strings can span those original boundaries.
        source = re.sub(r'</?span\b[^>]*>', '', body)
        if re.search(r'</?[A-Za-z][^>]*>', source):
            raise ValueError("Code blocks may contain text and spans only")
        text = html.unescape(source)
        return f'<{match["tag"]}{attrs}>{highlight(text)}</{match["tag"]}>'

    return BLOCK.sub(replace, guide)
