"""Source-register and citation validation. Run with unittest discovery in site/."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build


class SourcesTests(unittest.TestCase):
    def setUp(self):
        build.errors.clear()
        self.cfg = {'repo': 'college/notes', 'url': 'https://notes.example'}
        self.subject = {'slug': 'os', 'sources': [
            {'id': 'D3', 'kind': 'deck', 'title': 'Queues & "examples"', 'file': 'queue.pdf'},
            {'id': 'B1', 'kind': 'book', 'title': 'Operating System Concepts'}]}

    def tearDown(self):
        build.errors.clear()

    def test_file_link_keeps_page_as_text_and_preserves_surrounding_html(self):
        before = '<p>front &gt; rear '
        after = ' next.</p>'
        result = build.render_citations('unit', before + '<cite class="src" data-src="D3" data-p="14-16"></cite>' + after, self.subject, self.cfg)
        self.assertTrue(result.startswith(before))
        self.assertTrue(result.endswith(after))
        self.assertIn('https://github.com/college/notes/blob/main/subjects/os/sources/queue.pdf"', result)
        self.assertIn('target="_blank" rel="noopener"', result)
        self.assertIn('D3 · p.14-16</a>', result)
        self.assertIn('Queues &amp; &quot;examples&quot;, p.14-16', result)
        self.assertEqual(build.errors, [])

    def test_book_link_is_absolute_and_sections_have_no_page_prefix(self):
        result = build.render_citations('unit', "<cite data-src='B1' class='other src' data-p='§6.2'></cite>", self.subject, self.cfg)
        self.assertIn('href="https://notes.example/os/sources/#src-B1"', result)
        self.assertIn('B1 · §6.2</a>', result)
        self.assertNotIn('p.§', result)
        self.assertEqual(build.errors, [])

    def test_bad_citations_fail_instead_of_silently_rendering(self):
        for markup in ['<cite class="src" data-src="X9"></cite>',
                       '<cite class="src" data-src="D3" data-p="14#page"></cite>',
                       '<cite class="src" data-src="D3">text</cite>',
                       '<cite class="src" data-src="D3">',
                       '<cite class="src" data-src="D3"/>',
                       '<cite data-src="D3"></cite>',
                       '<cite class="src" data-src="D3" data-src="B1"></cite>']:
            with self.subTest(markup=markup):
                build.errors.clear()
                build.render_citations('unit', markup, self.subject, self.cfg)
                self.assertTrue(build.errors)

    def test_register_missing_unlisted_oversized_and_book_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'sources'
            folder.mkdir()
            pdf = folder / 'queue.pdf'
            subject = dict(self.subject, dir=directory)
            build.validate_sources(subject)
            self.assertTrue(any('missing PDF' in x for x in build.errors))
            pdf.write_bytes(b'%PDF-1.4')
            build.errors.clear()
            build.validate_sources(subject)
            self.assertEqual(build.errors, [])
            extra = folder / 'extra.pdf'
            extra.write_bytes(b'%PDF-1.4')
            build.validate_sources(subject)
            self.assertTrue(any('unlisted source PDF' in x for x in build.errors))
            extra.unlink()
            with pdf.open('wb') as f:
                f.truncate(20_000_001)
            build.errors.clear()
            build.validate_sources(subject)
            self.assertTrue(any('exceeds 20 MB' in x for x in build.errors))
            subject['sources'] = [dict(subject['sources'][0], kind='book')]
            build.errors.clear()
            build.validate_sources(subject)
            self.assertTrue(any('book must have no file' in x for x in build.errors))

    def test_build_rejects_any_pdf_in_public(self):
        with tempfile.TemporaryDirectory() as directory:
            original = build.write
            def write_and_leak_pdf(path, text):
                original(path, text)
                (Path(directory) / 'accidental.PDF').write_bytes(b'%PDF-1.4')
            with patch.object(build, 'OUT', directory), patch.object(build, 'write', write_and_leak_pdf):
                with self.assertRaises(SystemExit) as raised:
                    build.main()
            self.assertEqual(raised.exception.code, 1)
            self.assertTrue(any('public must contain no PDFs' in x for x in build.errors))


if __name__ == '__main__':
    unittest.main()
