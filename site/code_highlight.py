"""Small build-time lexer for the guides' code snippets.

Two kinds of block are highlighted, and nothing else:
  .formula-block.code   C, Java and C-like pseudocode
  .formula-block.asm    assembly (textbook RTN style, ARM, x86)
Write plain text in them; never colour code by hand. Colours: code-highlight.css.
Keeping the
markup and CSS inline makes downloaded guides work offline without JavaScript
or third-party assets. The Render build remains standard-library only.
"""
import html
import re


BLOCK = re.compile(
    r'<(?P<tag>div|pre)\b(?P<attrs>[^>]*\bclass="[^"]*\bformula-block\b[^"]*"[^>]*)>'
    r'(?P<body>.*?)</(?P=tag)>', re.S)
# control flow (purple), declarations and built-in types (blue), library/user types (teal)
KEYWORDS = set("""
    break case continue default do else for goto if return switch throw while
    from downto to then end repeat until and or not
""".split())
STORAGE = set("""
    auto class const enum extern implements import interface monitor native new package
    private procedure protected public register restrict sizeof static struct super
    synchronized this throws transient typedef union volatile
    bool boolean byte char double float int long short signed unsigned void
""".split())
TYPES = set("""
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
            elif value in STORAGE:
                kind = "storage"
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


ASM_DIRECTIVES = set("""
    ORIGIN RESERVE DATAWORD DATABYTE END EQU DC DS DB DW DD ORG AREA ENTRY ALIGN
""".split())
ASM_REGISTER = re.compile(r'R\d+|PC|SP|FP|LR|IR|MAR|MDR|ACC|CCR|PSW|E?[A-D]X|[A-D][HL]|E?[SD]I|E?[SB]P')
ASM_LINE = re.compile(r'(?P<code>[^;]*)(?P<comment>;.*)?')
ASM_TOKEN = re.compile(r'''
    (?P<label>^[ \t]*[A-Za-z_.][\w.]*:)
  | (?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<number>\#[ \t]*[-−+]?[\w.]+|\b(?:0[xX][\da-fA-F]+|\d+[hHbB]?)\b)
  | (?P<word>\.?[A-Za-z_][\w.]*(?:[<>=≤≥≠]+0)?)
''', re.X)


def highlight_asm(text):
    """One statement per line: [label:] mnemonic operands ; comment."""
    out = []
    for line in text.split("\n"):
        m = ASM_LINE.fullmatch(line)
        code, comment, end, seen_op = m["code"], m["comment"], 0, False
        for t in ASM_TOKEN.finditer(code):
            out.append(html.escape(code[end:t.start()], quote=False))
            value, kind = t.group(), t.lastgroup
            if kind == "word":
                if not seen_op and (value.startswith(".") or value.upper() in ASM_DIRECTIVES):
                    kind = "directive"
                elif not seen_op:
                    kind = "mnemonic"
                elif ASM_REGISTER.fullmatch(value):
                    kind = "register"
                else:
                    kind = None
                seen_op = True
            elif kind == "number" and not seen_op and not value.startswith("#"):
                kind, seen_op = None, True  # address/step column of a memory map: rest is plain text
            escaped = html.escape(value, quote=False)
            out.append(f'<span class="syntax-{kind}">{escaped}</span>' if kind else escaped)
            end = t.end()
        out.append(html.escape(code[end:], quote=False))
        if comment:
            out.append(f'<span class="syntax-comment">{html.escape(comment, quote=False)}</span>')
        out.append("\n")
    return "".join(out)[:-1]


def highlight_code_blocks(guide):
    def replace(match):
        attrs, body = match["attrs"], match["body"]
        classes = re.search(r'\bclass="([^"]*)"', attrs).group(1).split()
        lang = "asm" if "asm" in classes else "code" if "code" in classes else None
        if not lang:
            return match.group()
        # Remove the older hand-colored spans before lexing the complete block,
        # so comments and strings can span those original boundaries.
        source = re.sub(r'</?span\b[^>]*>', '', body)
        if re.search(r'</?[A-Za-z][^>]*>', source):
            raise ValueError("Code blocks may contain text and spans only")
        text = html.unescape(source)
        body = highlight_asm(text) if lang == "asm" else highlight(text)
        return f'<{match["tag"]}{attrs}>{body}</{match["tag"]}>'

    return BLOCK.sub(replace, guide)
