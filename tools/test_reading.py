"""Regression cases for book navigation and optional supporting material."""
import unittest
from reading import link_references, structured_markdown, classify_notes, epub_reading


class ReadingTests(unittest.TestCase):
    counts = {1: 49, 2: 47, 13: 49}

    def linked(self, text, chapter='chapter-02'):
        return link_references(text, chapter, self.counts)

    def test_intro_numbers_and_ranges(self):
        result = self.linked('Thắt dây an toàn (1); ngủ (2–3). Nghiên cứu (2020).')
        self.assertIn('([1](#chapter-02-entry-1))', result)
        self.assertIn('([2](#chapter-02-entry-2)–[3](#chapter-02-entry-3))', result)
        self.assertIn('(2020)', result)

    def test_cross_chapter_and_reversed_references(self):
        result = self.linked('Xem chương 1, mục 17–19 và mục 45 chương 1. Xem mục 3.')
        for entry in [17, 19, 45]:
            self.assertIn(f'#chapter-01-entry-{entry}', result)
        self.assertIn('#chapter-02-entry-3', result)
        self.assertNotIn('#chapter-02-entry-45', result)

    def test_explicit_list_in_appendix(self):
        result = self.linked('Xem chương 1, mục 7, 8 và 14.', 'a1')
        for entry in [7, 8, 14]:
            self.assertIn(f'#chapter-01-entry-{entry}', result)

    def test_do_not_link_citations_existing_links_or_study_numbers(self):
        text = ('### 1. Tiêu đề\n- **Dẫn chứng:** Nghiên cứu (1), mục 3.\n'
                '  Nguồn tiếp: mục 4.\n- **Lưu ý:** Có (2) nhóm. '
                '[mục 3](https://example.org) `mục 4` https://example.org/mục-5')
        result = self.linked(text)
        self.assertEqual(result, text + '\n')
        self.assertNotIn('#chapter-', self.linked('Xem mục 99 và chương 99, mục 1.'))

    def test_safety_visible_research_and_vietnam_notes_are_footnotes(self):
        source = '''# Chương thử
### 1. Nội dung
- **Chi phí:** Chi phí mẫu.
- **Nói dễ hiểu:** Đoạn chính.
- **Lợi ích:** Kết quả nghiên cứu.
- **Mức độ bằng chứng:** B
- **Nguồn:** [Nghiên cứu](https://example.org).
- **Lưu ý:** Cảnh báo cần đọc.

> **Ghi chú Việt Nam:** Ghi chú địa phương.

> **Đính chính an toàn:** Không bỏ cảnh báo này.
'''
        html = epub_reading(classify_notes(structured_markdown(source, 'chapter-01'), 'chapter-01'), 'chapter-01')
        self.assertEqual(len(html.select('[data-field]')), 6)
        self.assertEqual(len(html.select('aside')), 2)
        for note in html.select('aside'):
            self.assertEqual(note.get('epub:type'), 'footnote')
            ref = html.find('a', href='#' + note['id'])
            self.assertEqual(ref.get('epub:type'), 'noteref')
        self.assertIsNone(html.select_one('.caution').find_parent('aside'))
        self.assertIsNone(html.select_one('.correction').find_parent('aside'))
        for text in ['Đoạn chính.', 'Kết quả nghiên cứu.', 'Cảnh báo cần đọc.', 'Ghi chú địa phương.', 'Không bỏ cảnh báo này.']:
            self.assertIn(text, html.get_text())
        self.assertLess(str(html).index('Đoạn chính.'), str(html).index('Ghi chú địa phương.'))


if __name__ == '__main__':
    unittest.main()
