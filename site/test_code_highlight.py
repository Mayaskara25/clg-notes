"""Run with: python3 -m unittest discover -s site -p 'test_*.py'."""
import html
import re
import unittest
from pathlib import Path

from code_highlight import BLOCK, highlight, highlight_code_blocks


def text(markup):
    return html.unescape(re.sub(r'</?span\b[^>]*>', '', markup))


class CodeHighlightTests(unittest.TestCase):
    def test_strings_and_comments_keep_their_boundaries(self):
        source = 'printf("// not a comment: \\"quoted\\" & <tag>"); /* if (0) */'
        result = highlight(source)
        self.assertIn('<span class="syntax-string">"// not a comment:', result)
        self.assertIn('<span class="syntax-comment">/* if (0) */</span>', result)
        self.assertEqual(text(result), source)

    def test_entities_and_operators_remain_literal_code(self):
        source = '<pre class="formula-block code">if (p-&gt;data &lt; 5 &amp;&amp; p != NULL)\n  printf("&lt;script&gt;");</pre>'
        result = highlight_code_blocks(source)
        self.assertNotIn('<script>', result)
        self.assertEqual(text(result), html.unescape(source))
        self.assertIn('<span class="syntax-operator">-&gt;</span>', result)

    def test_comments_can_span_older_highlight_spans(self):
        source = '<div class="formula-block code"><span class="cm">/* producer</span>\n<span class="cm">   buffer */</span>\nint x = 1;</div>'
        result = highlight_code_blocks(source)
        self.assertIn('<span class="syntax-comment">/* producer\n   buffer */</span>', result)
        self.assertEqual(result.count('syntax-comment'), 1)
        self.assertEqual(highlight_code_blocks(result), result)

    def test_formula_and_output_markup_is_untouched(self):
        source = '<div class="formula-block">T(n) = 2<sup>n</sup> - 1</div><pre class="formula-block">Result = 25</pre>'
        self.assertEqual(highlight_code_blocks(source), source)

    def test_directives_java_types_and_numeric_literals(self):
        source = '#include <stdio.h>\nThread t = new Thread();\nsize_t n = 0x20; double x = 1.25e-3;'
        result = highlight(source)
        for kind, value in [('directive', '#include'), ('type', 'Thread'),
                            ('keyword', 'new'), ('type', 'size_t'),
                            ('number', '0x20'), ('number', '1.25e-3')]:
            self.assertIn(f'<span class="syntax-{kind}">{value}</span>', result)
        self.assertEqual(text(result), source)

    def test_every_published_snippet_keeps_its_text(self):
        subjects = Path(__file__).resolve().parents[1] / 'subjects'
        total = 0
        for slug in ('os', 'dsa'):
            for path in (subjects / slug).glob('*.html'):
                source = path.read_text()
                result = highlight_code_blocks(source)
                before, after = list(BLOCK.finditer(source)), list(BLOCK.finditer(result))
                self.assertEqual(len(before), len(after), path.name)
                for old, new in zip(before, after):
                    self.assertEqual(text(old['body']), text(new['body']), path.name)
                    if 'syntax-' in new['body']:
                        total += 1
                self.assertEqual(highlight_code_blocks(result), result, path.name)
        self.assertGreater(total, 150)


if __name__ == '__main__':
    unittest.main()
