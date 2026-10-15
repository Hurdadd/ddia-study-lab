#!/usr/bin/env python3
"""Catch removed Persian examples in chapter pages, including chapter 8's direct links.

Usage: python3 assets/check_teaching_examples.py [ch*/index.html ...]
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

# Published topic coverage: losing even one example is a regression.
EXPECTED = {
    1: (19, 17, 8), 2: (19, 20, 9), 3: (18, 17, 11), 4: (27, 20, 9),
    5: (19, 20, 9), 6: (21, 20, 9), 7: (16, 20, 9), 8: (23, 22, 11),
    9: (20, 20, 12), 10: (20, 20, 13), 11: (27, 20, 15),
    12: (25, 20, 13), 13: (29, 18, 14), 14: (19, 18, 13),
}


class Examples(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.stack = []
        self.core = self.review = self.guides = 0
        self.questions = self.teachers = 0
        self.ids = set()
        self.example_targets = set()
        self.links = []
        self.in_summary = False
        self.summary = ''
        self.technical = []
        self.active_example = None
        self.duplicate_ids = set()
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if attrs.get('id'):
            if attrs['id'] in self.ids:
                self.duplicate_ids.add(attrs['id'])
            self.ids.add(attrs['id'])
        if 'technical-example' in classes:
            assert self.active_example is None, 'nested technical examples'
            self.active_example = {'depth': len(self.stack), 'parts': [], 'version': attrs.get('data-example-version')}
            self.technical.append(self.active_example)
        if attrs.get('data-example-part') and self.active_example is not None:
            self.active_example['parts'].append(attrs['data-example-part'])
        if tag == 'a' and attrs.get('href', '').startswith('#example-'):
            self.links.append(attrs['href'][1:])
        if 'concept-example' in classes:
            assert any('fa' in a.get('class', '').split() for _, a in self.stack), 'example outside Persian content'
            if 'review-example' in classes:
                self.review += 1
            else:
                self.core += 1
            if attrs.get('id'):
                self.example_targets.add(attrs['id'])
        if 'teacher-example' in classes:
            self.guides += 1
        if 'teacher' in classes:
            self.teachers += 1
        if tag == 'summary':
            self.in_summary = True
            self.summary = ''
        if tag not in {'meta', 'link', 'br', 'hr', 'img', 'input', 'source', 'wbr', 'path', 'circle'}:
            self.stack.append((tag, attrs))

    def handle_data(self, data):
        if self.in_summary and not any('en' in a.get('class', '').split() for _, a in self.stack):
            self.summary += data

    def handle_endtag(self, tag):
        if tag == 'summary':
            if re.match(r'^\s*[۰-۹]+\.', self.summary):
                self.questions += 1
            self.in_summary = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                if self.active_example is not None and len(self.stack) <= self.active_example['depth']:
                    self.active_example = None
                break


def check(path):
    page = Examples(path.read_text(encoding='utf-8'))
    assert not page.duplicate_ids, f'duplicate anchors: {sorted(page.duplicate_ids)}'
    assert page.core > 0, 'chapter explanations have no marked examples'
    assert page.questions > 0 and page.review == page.questions, f'{page.review} examples for {page.questions} review questions'
    assert page.guides == page.teachers and page.guides > 0, f'{page.guides} guides for {page.teachers} diagram narrations'
    assert all(link in page.example_targets for link in page.links), 'an example link does not reach an example'
    ch = re.match(r'ch(\d+)-', path.parent.name)
    if ch:
        counts = (page.core, page.review, page.guides)
        assert counts == EXPECTED[int(ch[1])], f'topic coverage changed: {counts}'
    assert len(page.technical) == page.core + page.review + page.guides, 'an old or unstructured example remains'
    assert all(e['version'] == 'technical-v2' and e['parts'] == ['setup', 'steps', 'result'] for e in page.technical), 'an example lacks its initial state, operations or explained result'
    assert 'chapter-examples' in page.ids and len(page.links) == page.core, 'chapter example index is incomplete'
    if path.parent.name == 'ch8-transactions':
        required = {'example-transaction', 'example-acid', 'example-mvcc', 'example-lost-update',
                    'example-write-skew', 'example-phantom', 'example-2pc', 'example-idempotency'}
        assert 'chapter-examples' in page.ids and required <= set(page.links), 'chapter 8 example index is incomplete'
    return f'{page.core} chapter examples, {page.review} review examples, {page.guides} diagram guides'


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    paths = [Path(p) for p in sys.argv[1:]] or sorted(root.glob('ch*/index.html'))
    failed = False
    for path in paths:
        try:
            print(f'PASS {path.parent.name}: {check(path)}')
        except AssertionError as error:
            print(f'FAIL {path.parent.name}: {error}')
            failed = True
    sys.exit(1 if failed else 0)
