"""Build either reading edition from the Markdown masters in this repository.

Usage: python3 scripts/build_complete_edition.py
       python3 scripts/build_complete_edition.py --no-notes
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import uuid
import zipfile
import xml.etree.ElementTree as ET

from build_book import ROOT, text_for, validate_epub

ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV']
BOOKS = ['The Story of One Little Family', 'An Inappropriate Gathering', 'The Lustful',
         'Strains', 'Pro and Contra', 'The Russian Monk', 'Alyosha', 'Mitya',
         'The Preliminary Investigation', 'Boys', 'Brother Ivan Fyodorovich', 'A Judicial Error']
COUNTS = [5, 8, 11, 7, 7, 3, 4, 8, 9, 7, 10, 14]
ID_PATTERN = r'<!-- ((?:B\d+-C\d+|EP-C\d+|FM-(?:DED|EPI|PRE))-P\d+) -->'
XHTML = 'http://www.w3.org/1999/xhtml'
OPF = 'http://www.idpf.org/2007/opf'
DC = 'http://purl.org/dc/elements/1.1/'


def chapter_body(chapter):
    master = text_for(chapter)
    # Replace only the two display headings, retaining internal section headings.
    match = re.match(r'\A# [^\n]+\n\s*(?:## [^\n]+|\*Part I · Book [^\n]+\*)\n', master)
    assert match, chapter['id']
    body = master[match.end():]
    body = re.sub(r'\A\s*\*Part I · Book [^\n]+\*\n', '', body)
    return re.sub(r'^### ', '#### ', body, flags=re.M).strip()


def chapter_title(chapter):
    master = (ROOT / chapter['master']).read_text()
    heading = re.match(r'\A# [^\n]+\n\s*(?:## [^\n]+|\*Part I · Book [^\n]+\*)\n', master).group()
    if '[^' not in heading:
        return chapter['title']
    title = re.search(r'^## (?:Chapter )?[IVX]+[. ·]+(.*)$', heading, re.M).group(1)
    assert re.sub(r'\[\^[^\]]+\]', '', title) == chapter['title']
    return title


def assemble(manifest):
    chapters = manifest['chapters']
    expected = [f'b{b:02}-c{c:02}' for b, n in enumerate(COUNTS, 1) for c in range(1, n + 1)]
    expected += [f'ep-c{c:02}' for c in range(1, 4)]
    assert [c['id'] for c in chapters] == expected
    fm = manifest['front_matter_packet']
    assert fm['stage'] == 'reader-ready'
    front = (ROOT / fm['master']).read_text()
    assert re.findall(ID_PATTERN, front) == fm['source_ids']
    dedication, rest = front.split('<!-- FM-EPI-P001 -->', 1)
    epigraph, preface = rest.split('# The Brothers Karamazov\n\n## A Novel in Four Parts with an Epilogue\n\n## From the Author\n', 1)
    # The original dedication, epigraph, title and preface sequence is retained.
    # Use explicit HTML for title-page paragraph classes, supported by EPUB readers.
    title = ('# The Brothers Karamazov {#title-page .unnumbered}\n\n'
             '<div class="titlepage">\n'
             '<p class="subtitle">A Novel in Four Parts with an Epilogue</p>\n'
             '<p class="author">Fyodor Dostoevsky</p>\n'
             '<p class="translator">Translated by Astra</p>\n'
             '</div>')
    sections = ['# Dedication {#dedication}\n\n' + dedication.strip(),
                '# Epigraph {#epigraph}\n\n<!-- FM-EPI-P001 -->' + epigraph.rstrip(),
                title, '# From the Author {#from-the-author}\n' + preface.rstrip()]
    for item in manifest['editorial_matter']:
        assert item['stage'] == 'reader-ready'
        assert item['placement'] == 'after the author front matter and before Part I'
        sections.append((ROOT / item['master']).read_text().strip())
    for book in range(1, 13):
        if book in (1, 4, 7, 10):
            part = (book - 1) // 3 + 1
            sections.append(f'# Part {ROMAN[part]} {{#part-{part}}}')
        sections.append(f'## Book {ROMAN[book]}: {BOOKS[book - 1]} {{#book-{book}}}')
        for chapter in (c for c in chapters if c['id'].startswith(f'b{book:02}-')):
            n = int(chapter['id'][-2:])
            sections.append(f"### {ROMAN[n]}. {chapter_title(chapter)} {{#{chapter['id']}}}\n\n" + chapter_body(chapter))
    sections.append('# Epilogue {#epilogue}')
    for chapter in (c for c in chapters if c['id'].startswith('ep-')):
        n = int(chapter['id'][-2:])
        sections.append(f"## {ROMAN[n]}. {chapter['title']} {{#{chapter['id']}}}\n\n" + chapter_body(chapter))
    metadata = {'title': manifest['title'], 'author': 'Fyodor Dostoevsky', 'lang': 'en-US',
                'date': manifest['release_date'], 'rights': 'Annotated reading edition',
                'identifier': 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'karamazov-astra-complete-2026-10-02')),
                'toc-title': 'Contents'}
    text = '---\n' + '\n'.join(f'{k}: {json.dumps(v, ensure_ascii=False)}' for k, v in metadata.items()) + '\n---\n\n'
    text += '\n\n'.join(sections) + '\n'
    expected_ids = fm['source_ids'] + [sid for c in chapters for sid in c['source_ids']]
    assert re.findall(ID_PATTERN, text) == expected_ids
    refs = re.findall(r'\[\^([^\]]+)\](?!:)', text)
    defs = re.findall(r'^\[\^([^\]]+)\]:', text, re.M)
    assert len(defs) == len(set(defs)) and set(refs) == set(defs)
    assert not re.search(r'\b(TODO|TBD|PLACEHOLDER)\b', text)
    return text


def finish_package(epub):
    """Credit translation separately and place Contents after the inside title."""
    with zipfile.ZipFile(epub) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    opf_name = next(i.filename for i, data in items if i.filename.endswith('.opf'))
    tree = ET.fromstring(dict((i.filename, data) for i, data in items)[opf_name])
    ET.register_namespace('', OPF)
    ET.register_namespace('dc', DC)
    meta = tree.find(f'{{{OPF}}}metadata')
    ET.SubElement(meta, f'{{{DC}}}contributor', {'id': 'translator'}).text = 'Astra'
    ET.SubElement(meta, f'{{{OPF}}}meta', {'refines': '#translator', 'property': 'role', 'scheme': 'marc:relators'}).text = 'trl'
    manifest = tree.find(f'{{{OPF}}}manifest')
    nav_id = next(e.attrib['id'] for e in manifest if 'nav' in e.attrib.get('properties', '').split())
    title_item = None
    for i, data in items:
        if i.filename.endswith('.xhtml') and b'id="title-page"' in data:
            title_item = next(e.attrib['id'] for e in manifest if e.attrib['href'] == i.filename.split('/', 1)[1])
    assert title_item
    spine = tree.find(f'{{{OPF}}}spine')
    nav = next(e for e in spine if e.attrib['idref'] == nav_id)
    spine.remove(nav)
    nav.attrib.pop('linear', None)
    title_index = next(n for n, e in enumerate(spine) if e.attrib['idref'] == title_item)
    spine.insert(title_index + 1, nav)
    with zipfile.ZipFile(epub, 'w') as z:
        for info, data in items:
            if info.filename == opf_name:
                data = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
            elif info.filename.endswith('.xhtml'):
                # Readers may show popups; a backlink also supports ordinary navigation.
                value = data.decode('utf-8')
                refs = dict(re.findall(r'<a href="#(fn\d+)" class="footnote-ref" id="([^"]+)"', value))
                def backlink(match):
                    note_id = re.search(r'\bid="([^"]+)"', match.group(1)).group(1)
                    assert note_id in refs, (info.filename, note_id)
                    return (match.group(1) + match.group(2) +
                            f'<p class="note-return"><a href="#{refs[note_id]}" class="footnote-back" '
                            'role="doc-backlink" aria-label="Return to text">↩ Return to text</a></p>\n</aside>')
                value = re.sub(r'(<aside\b[^>]*>)(.*?)</aside>', backlink, value, flags=re.S)
                data = value.encode('utf-8')
            z.writestr(info, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-notes', action='store_true', help='Build a separate edition without notes')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'book-manifest.json').read_text())
    text = assemble(manifest)
    note_count = len(re.findall(r'^\[\^[^\]]+\]:', text, re.M))
    if args.no_notes:
        text = text.replace('rights: "Annotated reading edition"', 'rights: "Unannotated reading edition"')
        text = text.replace('Notes are included selectively where background helps understanding.',
                            'This edition omits the annotations.')
        old_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'karamazov-astra-complete-2026-10-02'))
        new_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'karamazov-astra-complete-no-notes-2026-10-02'))
        text = text.replace(old_id, new_id)
    out = ROOT / 'exports'
    out.mkdir(exist_ok=True)
    epub = out / ('The Brothers Karamazov — No Notes.epub' if args.no_notes else 'The Brothers Karamazov.epub')
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    md = build / ('no-notes.md' if args.no_notes else 'annotated.md')
    if args.no_notes:
        # Parse footnotes structurally, including multiline notes and heading references.
        text = subprocess.run(['pandoc', '--from=markdown', '--to=markdown-smart', '--standalone',
                               '--wrap=none', '--lua-filter=' + str(ROOT / 'scripts/omit-notes.lua')],
                              input=text, text=True, capture_output=True, check=True).stdout
    md.write_text(text)
    cover = ROOT / 'artwork/karamazov-astra-cover-v1.png'
    assert cover.is_file()
    subprocess.run(['pandoc', str(md), '--from=markdown', '--to=epub3', '--standalone',
                    '--toc', '--toc-depth=3', '--split-level=3', '--epub-title-page=false',
                    '--css=' + str(ROOT / 'scripts/complete-edition.css'),
                    '--epub-cover-image=' + str(cover), '-o', str(epub)], check=True)
    finish_package(epub)
    links = validate_epub(epub)
    print(f'{epub}\n96 chapters; 4,990 ordered source units; {0 if args.no_notes else note_count} notes; {links} valid internal links.')


if __name__ == '__main__':
    main()
