"""Answer boundaries, original-text search, and all published guides (stdlib only)."""
import json
from pathlib import Path
import re
import unittest

from build import QuestionScanner, plain, sections, wrap_answers


class AnswerTests(unittest.TestCase):
    def test_nested_markup_and_entities_are_preserved(self):
        source = ('<div class="qbox" id="example"><div class="qmeta">Paper</div>'
                  '<div class="qtext">What is &lt;x&gt;?</div>'
                  '<div class="ans-label">Answer</div><div><div>A &amp; B</div></div></div>')
        result, count, skipped = wrap_answers(source, 1)
        self.assertEqual((count, skipped), (1, 0))
        self.assertIn('aria-controls="example-ans"', result)
        self.assertIn('id="example-ans" hidden="until-found"', result)
        box = QuestionScanner(result).boxes[0]
        self.assertEqual([x.attrs.get('class') for x in box.children],
                         ['qmeta', 'qtext', 'ans-toggle', 'ans'])
        answer = box.children[-1]
        self.assertEqual(result[answer.inner:answer.close],
                         '<div class="ans-label">Answer</div><div><div>A &amp; B</div></div>')

    def test_consecutive_givens_including_second_question_stay_visible(self):
        source = ('<div class="qbox"><div class="qtext">Given</div>'
                  '<div class="qtext q-given">More input</div>'
                  '<table class="q-given"><tr><td>12</td></tr></table>'
                  '<div class="q-given"><svg><path d="M0 0"/></svg></div>'
                  '<p>Solution</p></div>')
        result, _, _ = wrap_answers(source, 2)
        self.assertLess(result.index('More input'), result.index('ans-toggle'))
        self.assertLess(result.index('</svg>'), result.index('ans-toggle'))
        self.assertGreater(result.index('Solution'), result.index('hidden="until-found"'))

    def test_bare_text_comments_and_void_elements(self):
        source = '<div class="qbox"><div class="qtext">Q<br>?</div><!-- answer -->42<br></div>'
        result, count, _ = wrap_answers(source, 1)
        self.assertEqual(count, 1)
        self.assertIn('<!-- answer -->42<br></div>', result)
        QuestionScanner(result)

    def test_empty_question_is_skipped(self):
        source = '<div class="qbox"><div class="qtext">Q</div>\n<!-- nothing --></div>'
        self.assertEqual(wrap_answers(source, 1), (source, 0, 1))

    def test_generated_ids_do_not_collide(self):
        source = ('<p id="q-1-1">existing</p><p id="q-1-2-ans">existing</p>'
                  '<div class="qbox"><div class="qtext">Q</div><p>A</p></div>'
                  '<div class="qbox"><div class="qtext">Q</div><p>A</p></div>')
        result, count, _ = wrap_answers(source, 1)
        ids = re.findall(r'id="([^"]+)"', result)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(count, 2)

    def test_reprocessing_is_idempotent(self):
        source = '<div class="qbox"><div class="qtext">Q</div><p>A</p></div>'
        result, _, _ = wrap_answers(source, 1)
        self.assertEqual(wrap_answers(result, 1)[0], result)

    def test_malformed_boundary_fails_instead_of_cutting_the_wrong_div(self):
        with self.assertRaises(ValueError):
            wrap_answers('<div class="qbox"><div class="qtext">Q</div><p>A</div>', 1)

    def test_existing_answer_id_collision_fails(self):
        with self.assertRaisesRegex(ValueError, 'answer id already exists'):
            wrap_answers('<p id="x-ans"></p><div class="qbox" id="x">'
                         '<div class="qtext">Q</div><p>A</p></div>', 1)

    def test_all_published_question_boundaries_and_search_sections(self):
        root = Path(__file__).resolve().parents[1]
        total, skipped, given = 0, 0, 0
        for slug in ('dsa', 'os', 'adld'):
            folder = root/'subjects'/slug
            cfg = json.loads((folder/'subject.json').read_text())
            for unit in cfg['units']:
                source = (folder/unit['source']).read_text()
                result, count, empty = wrap_answers(source, unit['n'])
                total += count
                skipped += empty
                before = QuestionScanner(source)
                after = QuestionScanner(result)
                self.assertEqual(len(before.boxes), len(after.boxes))
                # Original sections/search must retain the same anchors/titles.
                self.assertEqual([(x['id'], x['title']) for x in sections(source)],
                                 [(x['id'], x['title']) for x in sections(result)])
                self.assertTrue(before.ids.issubset(after.ids))
                for old, new in zip(before.boxes, after.boxes):
                    answer = new.children[-1]
                    self.assertTrue(answer.has_class('ans'), (slug, unit['n']))
                    self.assertEqual(answer.attrs['hidden'], 'until-found')
                    original_children = [x for x in new.children if not x.has_class('ans-toggle')]
                    retained = original_children[:-1]
                    self.assertEqual(len(retained)+len(answer.children), len(old.children))
                    for a,b in zip(old.children, retained+answer.children):
                        self.assertEqual(source[a.start:a.end], result[b.start:b.end])
                    given += sum(x.has_class('q-given') for x in retained)
        self.assertEqual((total, skipped, given), (348, 0, 10))


if __name__ == '__main__':
    unittest.main()
