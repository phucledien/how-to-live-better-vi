#!/usr/bin/env python3
"""Coverage, provenance, EPUB links, and PDF text/geometry checks. Not a semantic review."""
from pathlib import Path
import argparse, hashlib, json, os, re, unicodedata, zipfile
from decimal import Decimal
from collections import Counter
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET
import pymupdf
from bs4 import BeautifulSoup
import markdown
from reading import canonical_labels

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=Path(os.environ.get('HLTB_BUILD_ROOT', Path.home()/'Library/Developer/CodexBuilds/HowToLiveBetter-vi'))/'exports'
URL_RE=r'https?://[^\s<>\)\]"；]+'
def urls(s): return {u.rstrip('.,;') for u in re.findall(URL_RE,s)}
def norm(s): return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('\u200b','')
def entries(s):return {int(n):body for n,body in re.findall(r'^### (\d+)\.(.*?)(?=^### \d+\.|\Z)',s,re.M|re.S)}
def field(body,name):
 m=re.search(r'^- '+re.escape(name)+r'：(.*)',body,re.M)
 return m[1] if m else ''
def vifield(body,name):
 m=re.search(r'^- \*\*'+re.escape(name)+r':\*\*(.*?)(?=\n- \*\*|\Z)',body,re.M|re.S)
 return m[1] if m else ''
def numbers(s):
 # Normalize thousands separators and equivalent Chinese/Vietnamese counting units.
 scales={'千':1000,'万':10000,'亿':100000000,'nghìn':1000,'ngàn':1000,'triệu':1000000,'tỷ':1000000000,'vạn':10000}
 values=set()
 for m in re.finditer(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(千|万|亿|nghìn|ngàn|triệu|tỷ|vạn)?',s):
  n=Decimal(m[1].replace(',',''));values.add(str(n.normalize()))
  if m[2]:values.add(str((n*scales[m[2]]).normalize()))
 return values

def numeric_missing(source,target):
 scales={'千':1000,'万':10000,'亿':100000000}
 have=numbers(target) | numbers(re.sub(r'(?<=\d),(?=\d)', '.', target)) | numbers(re.sub(r'(?<=\d)[ .](?=\d{3}(?:\D|$))', '', target));missing=[]
 for match in re.finditer(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(千|万|亿)?',source):
  n=Decimal(match[1].replace(',',''));options={str(n.normalize())}
  if match[2]:options.add(str((n*scales[match[2]]).normalize()))
  if not options & have and ('.' in match[1] or n>=10):missing.append(match[0].strip())
 return sorted(set(missing))

ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=DEFAULT);ap.add_argument('--source',type=Path,help='Path to the pinned Chinese source clone');args=ap.parse_args()
m=json.loads((ROOT/'manifest.json').read_text());errors=[];warnings=[];stats=[]
source=args.source.resolve() if args.source else (ROOT/m['source_clone']).resolve()
for c in m['chapters']:
 if c['status'] not in ('draft','reviewed'):continue
 original=source/c['source'];translated=ROOT/c['translation']
 if hashlib.sha256(original.read_bytes()).hexdigest()!=c['source_sha256']:errors.append(f'Source drift: {original}')
 zh=original.read_text();vi=canonical_labels(translated.read_text());a=entries(zh);b=entries(vi)
 if re.search(r'@SOURCE-|TODO|待翻译',vi):errors.append(f'Unfinished placeholder in chapter {c["number"]}')
 if list(b)!=list(a):errors.append(f'Entry numbering mismatch chapter {c["number"]}')
 for n,z in a.items():
  v=b.get(n,'');required=['Chi phí','Ý chính','Chi tiết và cơ sở','Mức độ bằng chứng','Dẫn chứng','Lưu ý']
  for key in required:
   if not vifield(v,key).strip():errors.append(f'Chapter {c["number"]}.{n}: missing {key}')
  grade=field(z,'证据等级').strip();vg=vifield(v,'Mức độ bằng chứng').strip()
  if not vg.startswith(re.match(r'[ABC]',grade)[0] if re.match(r'[ABC]',grade) else grade):errors.append(f'Evidence grade mismatch {c["number"]}.{n}: {grade} / {vg}')
  if '争议' in grade and 'tranh' not in vg:errors.append(f'Missing disputed-grade qualifier {c["number"]}.{n}')
  missing=urls(field(z,'来源'))-urls(vifield(v,'Dẫn chứng'))
  if missing:errors.append(f'Citation URLs missing {c["number"]}.{n}: {sorted(missing)}')
  significant=numeric_missing(field(z,'收益'),vifield(v,'Chi tiết và cơ sở'))
  if significant:warnings.append({'chapter':c['number'],'entry':n,'source_numbers_not_literal_in_vi_benefit':significant})
 stats.append({'chapter':c['number'],'entries':len(b),'source_urls':len(urls(zh)),'translation_urls':len(urls(vi))})

appendix_stats=[]
for a in m.get('appendices',[]):
 if a['status'] not in ('draft','reviewed'):continue
 original=source/a['source'];translated=ROOT/a['translation']
 if hashlib.sha256(original.read_bytes()).hexdigest()!=a['source_sha256']:errors.append(f'Source drift: {original}')
 zh=original.read_text();vi=canonical_labels(translated.read_text())
 missing=urls(zh)-urls(vi)
 if missing:errors.append(f'Citation URLs missing appendix {a["id"]}: {sorted(missing)}')
 if re.search(r'@SOURCE-|TODO|待翻译',vi):errors.append(f'Unfinished placeholder in appendix {a["id"]}')
 appendix_stats.append({'id':a['id'],'source_urls':len(urls(zh)),'translation_urls':len(urls(vi))})

build_report=json.loads((args.out/'build-report.json').read_text())
if build_report['chapters']!=[c['chapter'] for c in stats]:errors.append('Export coverage differs from registered chapters; rebuild before delivery')
if build_report.get('appendices',[])!=[a['id'] for a in appendix_stats]:errors.append('Export coverage differs from registered appendices; rebuild before delivery')
for filename,digest in build_report.get('input_sha256',{}).items():
 if hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()!=digest:errors.append(f'Translation changed after build: {filename}')
for filename,details in build_report['outputs'].items():
 if hashlib.sha256((args.out/filename).read_bytes()).hexdigest()!=details['sha256']:errors.append(f'Export changed since build: {filename}')

pdf=args.out/'Song-tot-hon-vi-ban-nhap.pdf';epub=args.out/'Song-tot-hon-vi-ban-nhap.epub'
doc=pymupdf.open(pdf);body=[];bad_boxes=[]
for i,page in enumerate(doc):
 for block in page.get_text('dict')['blocks']:
  if 'lines' not in block:continue
  for line in block['lines']:
   for span in line['spans']:
    x0,y0,x1,y1=span['bbox']
    if x0<-0.5 or y0<-0.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:bad_boxes.append({'page':i+1,'text':span['text'],'bbox':span['bbox']})
 for block in page.get_text('blocks'):
  x0,y0,x1,y1,t,*_=block
  if 44<y0 and y1<page.rect.height-45:body.append(t)
 if not page.get_text().strip():errors.append(f'Blank PDF page {i+1}')
if bad_boxes:errors.append(f'{len(bad_boxes)} PDF text spans outside page')
pdftext=norm(''.join(body));missing_paragraphs=[]
with zipfile.ZipFile(epub) as z:
 if z.namelist()[0]!='mimetype' or z.getinfo('mimetype').compress_type!=zipfile.ZIP_STORED:errors.append('Invalid EPUB mimetype packaging')
 files={n:ET.fromstring(z.read(n)) for n in z.namelist() if n.endswith(('.xhtml','.opf','.xml'))}
 ns={'h':'http://www.w3.org/1999/xhtml'}
 opf=files['EPUB/package.opf'];op={'o':'http://www.idpf.org/2007/opf'}
 order=[i.get('idref') for i in opf.findall('.//o:spine/o:itemref',op)]
 if order[:2]!=['cover','contents']:errors.append('Visible contents page must follow cover')
 for name,tree in files.items():
  for ref in tree.findall('.//h:a',ns):
   if ref.get('{http://www.idpf.org/2007/ops}type')=='noteref':
    parts=urlsplit(ref.get('href'));target=str(Path(name).parent/parts.path) if parts.path else name
    note=next((e for e in files[target].iter() if e.get('id')==parts.fragment),None) if target in files else None
    if note is None or note.tag!='{http://www.w3.org/1999/xhtml}aside' or note.get('{http://www.idpf.org/2007/ops}type')!='footnote':errors.append(f'Invalid Apple Books footnote {name}: {ref.get("href")}')

 for name,tree in files.items():
  if not name.endswith('.xhtml'):continue
  chapter_match=re.fullmatch(r'EPUB/chapter-(\d+)\.xhtml',name)
  if chapter_match:
   chapter=next(c for c in m['chapters'] if c['number']==int(chapter_match[1]))
   for label in ('Chi phí','Ý chính','Chi tiết và cơ sở','Mức độ bằng chứng','Dẫn chứng','Lưu ý'):
    count=sum(el.get('data-field')==label for el in tree.iter())
    if count!=chapter['entries']:errors.append(f'Rendered field lost in {name}: {label} {count}/{chapter["entries"]}')
  ids={e.get('id') for e in tree.iter() if e.get('id')}
  for a in tree.findall('.//h:a',ns):
   href=a.get('href','')
   if urlsplit(href).scheme:continue
   parts=urlsplit(href);target=str(Path(name).parent/parts.path) if parts.path else name
   if target not in files:errors.append(f'Broken EPUB link {name} -> {href}');continue
   if parts.fragment and not any(e.get('id')==unquote(parts.fragment) for e in files[target].iter()):errors.append(f'Broken EPUB anchor {name} -> {href}')
  if name.endswith(('nav.xhtml','contents.xhtml','cover.xhtml')):continue
  for tag in ('p','li'):
   for p in tree.findall('.//h:'+tag,ns):
    if p.get('data-ui')=='true':continue
    t=''.join(p.itertext())
    if norm(t) and norm(t) not in pdftext:missing_paragraphs.append({'file':name,'text':t[:200]})
if missing_paragraphs:errors.append(f'{len(missing_paragraphs)} paragraphs not matched in PDF text extraction; inspect before delivery')
report={'chapters':stats,'appendices':appendix_stats,'pdf_pages':len(doc),'pdf_out_of_bounds':bad_boxes,'pdf_unmatched_paragraphs':missing_paragraphs,'numeric_review':warnings,'errors':errors,'limitation':'Structure and text checks do not prove semantic translation fidelity or independent source validity.'}
(args.out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({**report,'pdf_unmatched_paragraphs':missing_paragraphs[:10],'pdf_out_of_bounds':bad_boxes[:10]},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
