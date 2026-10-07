"""Compare the packaged EPUB against all reading masters and validate its inventory."""
import sys,json,re,subprocess,zipfile,hashlib
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as E
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_complete_edition import ROOT, ID_PATTERN
no_notes = '--no-notes' in sys.argv
class Content(HTMLParser):
 def __init__(self): super().__init__();self.stack=[];self.parts=[];self.counts={k:0 for k in ['br','em','strong','blockquote']}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);skip=bool(self.stack and self.stack[-1]) or tag in ['head','h1','h2','h3'] or any(c in a.get('class','').split() for c in ['footnote-ref','footnote-back','note-return'] + (['footnotes'] if no_notes else [])) or (no_notes and a.get('role') == 'doc-footnote')
  if not skip and tag in self.counts:self.counts[tag]+=1
  if not skip and tag in ['p','br','li','h4','blockquote']:self.parts.append(' ')
  if tag not in ['br','hr','meta','link','img','input']:self.stack.append(skip)
 def handle_endtag(self,tag):
  if tag not in ['br','hr','meta','link','img','input'] and self.stack:self.stack.pop()
  self.parts.append(' ' if tag in ['p','li','h4','blockquote'] else '')
 def handle_data(self,data):
  if not self.stack or not self.stack[-1]:self.parts.append(data)
 def text(self):return re.sub(r'\s+',' ',''.join(self.parts)).strip()
m=json.loads((ROOT/'book-manifest.json').read_text());p=ROOT/'exports'/('The Brothers Karamazov — No Notes.epub' if no_notes else 'The Brothers Karamazov.epub')
note_masters = [m['front_matter_packet']['master']] + [c['master'] for c in m['chapters']] + [e['master'] for e in m['editorial_matter']]
expected_notes = 0 if no_notes else sum(len(re.findall(r'^\[\^[^\]]+\]:', (ROOT/path).read_text(), re.M)) for path in note_masters)
with zipfile.ZipFile(p) as z:
 docs={n:z.read(n).decode() for n in z.namelist() if n.endswith('.xhtml')}
 for c in m['chapters']:
  doc=next(t for t in docs.values() if f'<section id="{c["id"]}"' in t)
  original=(ROOT/c['master']).read_text()
  original=re.sub(r'^### ', '#### ', original, flags=re.M)
  original=re.sub(r'^\*Part I · Book [^\n]+\*$', '', original, flags=re.M)
  base=subprocess.run(['pandoc','-f','markdown','-t','html5'],input=original,text=True,capture_output=True,check=True).stdout
  a=Content();a.feed(base);b=Content();b.feed(doc)
  assert a.text()==b.text(),(c['id'],'text mismatch',a.text()[:80],b.text()[:80])
  assert a.counts==b.counts,(c['id'],a.counts,b.counts)
 ns={'o':'http://www.idpf.org/2007/opf','h':'http://www.w3.org/1999/xhtml','d':'http://purl.org/dc/elements/1.1/'}
 opf=E.fromstring(z.read('EPUB/content.opf'));items={e.get('id'):e.get('href') for e in opf.find('o:manifest',ns)}
 order=['EPUB/'+items[e.get('idref')] for e in opf.find('o:spine',ns)]
 ids=[v for name in order for v in re.findall(ID_PATTERN,docs.get(name,''))]
 assert ids==m['front_matter_packet']['source_ids']+[v for c in m['chapters'] for v in c['source_ids']]
 assert len(ids)==len(set(ids))==4990
 assert opf.find('o:metadata/d:title',ns).text=='The Brothers Karamazov'
 assert [e.text for e in opf.findall('o:metadata/d:creator',ns)]==['Fyodor Dostoevsky']
 assert opf.find('o:metadata/d:contributor',ns).text=='Astra'
 assert sum(t.count('role="doc-footnote"') for t in docs.values())==expected_notes
 assert sum(t.count('role="doc-backlink"') for t in docs.values())==expected_notes
 if no_notes:
  assert not any(re.search(r'footnote-ref|epub:type="noteref"|class="edition"|Private annotated reading edition', t) for t in docs.values())
 nav=E.fromstring(docs['EPUB/nav.xhtml']);toc=next(n for n in nav.findall('h:body/h:nav',ns) if n.get('{http://www.idpf.org/2007/ops}type')=='toc')
 hrefs=[e.get('href') for e in toc.findall('.//h:a',ns)]
 for c in m['chapters']: assert any(h.endswith('#'+c['id']) for h in hrefs),c['id']
 cover=next(e for e in opf.find('o:manifest',ns) if e.get('properties')=='cover-image')
 assert hashlib.sha256(z.read('EPUB/'+cover.get('href'))).digest()==hashlib.sha256((ROOT/'artwork/karamazov-astra-cover-v1.png').read_bytes()).digest()
 print('PASS: all 96 rendered chapter texts match their independently rendered reading masters' + (' with notes excluded' if no_notes else ', including notes') + '; emphasis, bold, blockquotes and line-break counts match.')
 print('PASS: all 4,990 source markers are unique and in spine order; all 96 chapters appear in navigation; note inventory, title/author/translator metadata and cover bytes match.')
