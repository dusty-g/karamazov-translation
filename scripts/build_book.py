"""Shared manuscript and EPUB checks; no dependency on the production archive."""
from pathlib import Path
import re, zipfile, posixpath
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, unquote
ROOT = Path(__file__).resolve().parents[1]

def validate_epub(path):
    count = 0
    with zipfile.ZipFile(path) as z:
        assert z.infolist()[0].filename == 'mimetype'
        assert z.infolist()[0].compress_type == zipfile.ZIP_STORED
        assert z.read('mimetype') == b'application/epub+zip'
        trees = {n:ET.fromstring(z.read(n)) for n in z.namelist() if n.endswith(('.xhtml','.opf','.ncx','.xml'))}
        ids = {n:{e.attrib['id'] for e in t.iter() if 'id' in e.attrib} for n,t in trees.items()}
        for n,t in trees.items():
            for e in t.iter():
                href = e.attrib.get('href')
                if not href or urlsplit(href).scheme:
                    continue
                u = urlsplit(href)
                target = posixpath.normpath(posixpath.join(posixpath.dirname(n),unquote(u.path))) if u.path else n
                assert target in z.namelist(), (n,href)
                if u.fragment:
                    assert unquote(u.fragment) in ids.get(target,set()), (n,href)
                count += 1
    return count

def text_for(c):
    assert c['stage'] == 'reader-ready', 'Refusing to export unfinished chapter'
    t = (ROOT/c['master']).read_text()
    found = re.findall(r'<!-- ((?:B\d+|EP)-C\d+-P\d+) -->',t)
    assert found == c['source_ids'], (c['id'],found)
    assert not re.search(r'\b(TODO|TBD|PLACEHOLDER)\b',t)
    return t
