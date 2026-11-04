#!/usr/bin/env python3
"""Build only explicitly registered translation drafts into Markdown, EPUB 3 and PDF."""
from pathlib import Path
import argparse, hashlib, html, json, os, re, shutil, urllib.request, zipfile, posixpath, tempfile
from urllib.parse import quote, urlsplit, unquote
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
import markdown
from bs4 import BeautifulSoup, NavigableString
from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, KeepTogether, Flowable
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get('HLTB_BUILD_ROOT', Path.home()/'Library/Developer/CodexBuilds/HowToLiveBetter-vi')).resolve()
TITLE = 'Sống tốt hơn'
NS = 'http://www.w3.org/1999/xhtml'
EPUBNS = 'http://www.idpf.org/2007/ops'
TEAL = '#205B58'


def safe_local(path):
    p = Path(path).expanduser().resolve()
    if any(x in p.parts for x in ('Documents','Desktop','Mobile Documents','CloudStorage')) or 'icloud' in str(p).lower():
        raise ValueError(f'Generated output may not be in a synced location: {p}')
    return p


def prepare_fonts(text):
    safe_local(CACHE).mkdir(parents=True, exist_ok=True)
    downloads = {
        'NotoSerif-variable.ttf':'https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif%5Bwdth,wght%5D.ttf',
        'NotoSansSC-variable.ttf':'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf',
    }
    for name, url in downloads.items():
        p = CACHE/name
        if not p.exists(): urllib.request.urlretrieve(url, p)
    specs = [('Text','NotoSerif-variable.ttf',{'wght':400,'wdth':100}),
             ('TextBold','NotoSerif-variable.ttf',{'wght':700,'wdth':100}),
             ('CJK','NotoSansSC-variable.ttf',{'wght':400})]
    fonts = {}
    required = text + ''.join(chr(i) for i in range(32,127)) + 'ăâđêôơưĂÂĐÊÔƠƯ'
    for name, src, axes in specs:
        static = CACHE/f'{name}-static.ttf'
        if not static.exists():
            f = instantiateVariableFont(FTFont(CACHE/src), axes, inplace=True)
            f.save(static)
        pdfmetrics.registerFont(TTFont(name,str(static)))
        fonts[name] = static
    pdfmetrics.registerFontFamily('Text',normal='Text',bold='TextBold',italic='Text',boldItalic='TextBold')
    cmaps = {k:FTFont(v).getBestCmap() for k,v in fonts.items()}
    missing = sorted({ord(c) for c in required if not c.isspace() and not any(ord(c) in m for m in cmaps.values())})
    if missing: raise ValueError(f'Missing glyphs: {[chr(c) for c in missing]}')
    for name, static in fonts.items():
        f = FTFont(static)
        opt = subset.Options(); opt.recalc_timestamp = False
        s = subset.Subsetter(options=opt); s.populate(text=required); s.subset(f)
        f.save(CACHE/f'{name}-epub.ttf')
    return cmaps


def render_html(md, prefix):
    # Python-Markdown needs a blank line before a list resumes after prose.
    # CommonMark permits the two-space continuation used in some chapters.
    lines=[]
    for line in md.splitlines():
        if line.startswith('- **') and lines and lines[-1].strip() and not lines[-1].startswith('- **'):
            lines.append('')
        lines.append(line)
    md='\n'.join(lines)
    soup = BeautifulSoup(markdown.markdown(md,extensions=['extra']), 'html.parser')
    # Reflow wide comparison tables as labeled rows in the reading editions.
    # The editable Markdown keeps its original tables.
    for table in list(soup.find_all('table')):
        rows=table.find_all('tr')
        if not rows: continue
        headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['th','td'])]
        for row in rows[1:]:
            cells=row.find_all(['th','td'])
            if not cells: continue
            heading=soup.new_tag('h3')
            heading.append(headers[0]+': ' if headers[0] else '')
            for child in list(cells[0].contents):heading.append(child.extract())
            table.insert_before(heading)
            for j,cell in enumerate(cells[1:],1):
                para=soup.new_tag('p');strong=soup.new_tag('strong');strong.string=(headers[j] if j<len(headers) else '')+': '
                para.append(strong)
                for child in list(cell.contents):para.append(child.extract())
                table.insert_before(para)
        table.decompose()
    for i,h in enumerate(soup.find_all(['h1','h2','h3'])):
        n = re.match(r'(\d+)\.',h.get_text())
        h['id'] = f'{prefix}-entry-{n[1]}' if h.name=='h3' and n else f'{prefix}-heading-{i}'
    for li in soup.find_all('li'):
        if li.get_text().strip().startswith('Nguồn:'): li['class'] = 'sources'
        if li.get_text().strip().startswith(('Ghi chú cho độc giả Việt Nam', 'Ghi chú cho bản Việt', 'Ghi chú Việt Nam','Ghi chú hiệu đính')): li['class'] = 'local-note'
    for para in soup.find_all('p'):
        if para.get_text().startswith(('Ghi chú cho độc giả Việt Nam', 'Ghi chú cho bản Việt', 'Ghi chú Việt Nam','Ghi chú hiệu đính')):para['class']='local-note'
    return soup


def xhtml(title, fragment, extra=''):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="{NS}" xmlns:epub="{EPUBNS}" xml:lang="vi" lang="vi">
<head><meta name="viewport" content="width=device-width, initial-scale=1.0"/><title>{html.escape(title)}</title><link href="style.css" rel="stylesheet" type="text/css"/></head>
<body>{extra}{fragment}</body></html>'''


CSS = '''@font-face{font-family:Book;src:url(fonts/Text.ttf)}
@font-face{font-family:Book;src:url(fonts/TextBold.ttf);font-weight:bold}
@font-face{font-family:CJK;src:url(fonts/CJK.ttf)}
html{font-family:Book,CJK,serif;color:#252E2D;background:#fff}
body{margin:5%;line-height:1.65;overflow-wrap:break-word;hyphens:none}
h1,h2,h3{color:#205B58;line-height:1.3;break-after:avoid;page-break-after:avoid}
h1{font-size:1.8em;margin:1em 0}h2{font-size:1.3em;margin-top:1.8em}h3{font-size:1.15em;margin-top:2em}
p,li{orphans:3;widows:3}p{margin:.7em 0}ul{padding-left:1.2em}li{margin:.6em 0}
a{color:#205B58;text-decoration:underline;overflow-wrap:anywhere;word-wrap:break-word}
.sources{font-size:.85em;line-height:1.6}.local-note{border-left:3px solid #B18D51;padding-left:.7em}
.cover{padding-top:15%;text-align:left}.cover h1{font-size:3em}.eyebrow{letter-spacing:.12em;font-size:.75em}
.status{border-top:1px solid #B18D51;margin-top:2em;padding-top:1em}
nav ol{padding-left:1.3em}nav li{margin:.4em 0}
'''


def build_epub(out,pages,coverage,meta):
    uid = 'urn:sha256:'+hashlib.sha256((''.join(str(s) for _,_,s in pages)+coverage).encode()).hexdigest()
    items=[]; spine=[]; nav=[]; contents={}
    cover = f'<section class="cover"><p class="eyebrow">BẢN TIẾNG VIỆT · BẢN THẢO</p><h1>{TITLE}</h1><p>Cẩm nang cân nhắc thời gian, sức khỏe,<br/>tiền bạc và tự do</p><p>Nguyên tác: eternity4719 và cộng tác viên</p><p class="status">{html.escape(coverage)}</p></section>'
    contents['cover.xhtml'] = xhtml(TITLE,cover)
    items.append(('cover','cover.xhtml','application/xhtml+xml','')); spine.append('cover')
    for ident,title,soup in pages:
        fname=f'{ident}.xhtml'
        fragment=BeautifulSoup(str(soup),'html.parser')
        for link in fragment.find_all('a',href=True):
            href=link['href']
            if href.startswith('#'):
                owner=next((i for i,_,_ in pages if href.startswith('#'+i+'-')),None)
                if owner:link['href']=owner+'.xhtml'+href
        contents[fname]=xhtml(title,str(fragment))
        items.append((ident,fname,'application/xhtml+xml','')); spine.append(ident)
        children=''.join(f'<li><a href="{fname}#{h["id"]}">{html.escape(h.get_text())}</a></li>' for h in soup.find_all(['h2','h3']))
        nav.append(f'<li><a href="{fname}">{html.escape(title)}</a>'+ (f'<ol>{children}</ol>' if children else '')+'</li>')
    contents['nav.xhtml']=xhtml('Mục lục', '<nav epub:type="toc" id="toc"><h1>Mục lục</h1><ol>'+''.join(nav)+'</ol></nav>')
    items.append(('nav','nav.xhtml','application/xhtml+xml','nav'))
    contents['style.css']=CSS; items.append(('css','style.css','text/css',''))
    for name in ('Text','TextBold','CJK'):
        contents[f'fonts/{name}.ttf']=(CACHE/f'{name}-epub.ttf').read_bytes()
        items.append((f'font-{name}',f'fonts/{name}.ttf','font/ttf',''))
    for p in (ROOT/'assets').glob('OFL*.txt'):
        contents[f'licenses/{p.name}']=p.read_bytes();items.append((p.stem,f'licenses/{p.name}','text/plain',''))
    modified=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest=''.join(f'<item id="{i}" href="{h}" media-type="{m}"'+(f' properties="{pr}"' if pr else '')+'/>' for i,h,m,pr in items)
    opf=f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">{uid}</dc:identifier><dc:title>{TITLE} — Bản dịch tiếng Việt — bản thảo</dc:title><dc:language>vi</dc:language><dc:creator>eternity4719 và cộng tác viên</dc:creator><dc:description>{html.escape(coverage)}</dc:description><dc:source>{meta['source_repository']}/tree/{meta['source_commit']}</dc:source><dc:rights>CC BY 4.0; bản dịch độc lập có hỗ trợ AI, không phải bản chính thức.</dc:rights><meta property="dcterms:modified">{modified}</meta><meta property="rendition:layout">reflowable</meta></metadata><manifest>{manifest}</manifest><spine>{''.join(f'<itemref idref="{i}"/>' for i in spine)}</spine></package>'''
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('EPUB/package.opf',opf,compress_type=zipfile.ZIP_DEFLATED)
        for name,content in contents.items():
            if name.endswith('.xhtml'): ET.fromstring(content)
            z.writestr('EPUB/'+name,content,compress_type=zipfile.ZIP_DEFLATED)
    preview=CACHE/'epub-preview'; preview.mkdir(exist_ok=True)
    with zipfile.ZipFile(out) as z: z.extractall(preview)


def build_pdf(out,pages,coverage,cmaps):
    width,height=170*mm,240*mm
    styles={
      'p':ParagraphStyle('body',fontName='Text',fontSize=10.1,leading=15.8,spaceAfter=7,allowWidows=0,allowOrphans=0,splitLongWords=1),
      'source':ParagraphStyle('source',fontName='Text',fontSize=7.9,leading=11.7,spaceAfter=7,allowWidows=0,allowOrphans=0,splitLongWords=1,textColor=colors.HexColor('#4D5B59')),
      'h1':ParagraphStyle('chapter',fontName='TextBold',fontSize=23,leading=30,textColor=colors.HexColor(TEAL),spaceAfter=18,keepWithNext=True),
      'h2':ParagraphStyle('section',fontName='TextBold',fontSize=14,leading=20,textColor=colors.HexColor(TEAL),spaceBefore=12,spaceAfter=9,keepWithNext=True),
      'h3':ParagraphStyle('entry',fontName='TextBold',fontSize=12.2,leading=18,textColor=colors.HexColor(TEAL),spaceBefore=12,spaceAfter=9,keepWithNext=True),
      'note':ParagraphStyle('local',fontName='Text',fontSize=9.3,leading=14.5,spaceBefore=5,spaceAfter=9,borderColor=colors.HexColor('#B18D51'),borderWidth=.5,borderPadding=7,allowWidows=0,allowOrphans=0),
    }
    def txt(s):
        result=[]
        for part in re.split(r'([\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]+)',s):
            esc=html.escape(part)
            if part and any(ord(c) not in cmaps['Text'] for c in part if not c.isspace()):
                result.append(f'<font name="CJK">{esc}</font>')
            else: result.append(esc)
        return ''.join(result)
    def inline(el):
        if isinstance(el,NavigableString): return txt(str(el))
        content=''.join(inline(c) for c in el.children)
        if el.name in ('strong','b'): return '<b>'+content+'</b>'
        if el.name in ('em','i'): return '<i>'+content+'</i>'
        if el.name=='a': return '<a href="'+html.escape(el.get('href',''),quote=True)+'" color="'+TEAL+'">'+content+'</a>'
        if el.name=='br': return '<br/>'
        if el.name in ('sup','sub'): return f'<{el.name}>{content}</{el.name}>'
        return content
    class Book(BaseDocTemplate):
        def beforeDocument(self):
            self.running = ""
        def afterFlowable(self,flow):
            if getattr(flow,'book_heading',None):
                level,key,title=flow.book_heading
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(title,key,level=level,closed=level>0)
                if level==0:
                    self.running=title
                    self.notify('TOCEntry',(0,title,self.page,key))
    doc=Book(str(out),pagesize=(width,height),leftMargin=17*mm,rightMargin=17*mm,topMargin=20*mm,bottomMargin=19*mm,title=TITLE,author='eternity4719 và cộng tác viên; bản dịch tiếng Việt độc lập')
    doc.running=''
    def decorate(canvas,doc):
        if doc.page==1:return
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#C2CDCA'));canvas.setLineWidth(.4)
        canvas.line(17*mm,15*mm,width-17*mm,15*mm)
        canvas.setFont('Text',8);canvas.setFillColor(colors.HexColor('#5E6B68'))
        canvas.drawString(17*mm,10*mm,'Sống tốt hơn · Bản dịch tiếng Việt — bản thảo')
        canvas.drawRightString(width-17*mm,10*mm,str(doc.page))
        label=doc.running
        while pdfmetrics.stringWidth(label,'Text',7.6)>width-34*mm:label=label[:-2]
        canvas.setFont('Text',7.6);canvas.drawString(17*mm,height-12*mm,label)
        canvas.restoreState()
    frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='book',frames=frame,onPageEnd=decorate))
    story=[Spacer(1,26*mm),Paragraph('BẢN TIẾNG VIỆT · BẢN THẢO',styles['source']),Spacer(1,8*mm),Paragraph(TITLE,ParagraphStyle('title',fontName='TextBold',fontSize=39,leading=49,textColor=colors.HexColor(TEAL))),Spacer(1,8*mm),Paragraph('Cẩm nang cân nhắc thời gian,<br/>sức khỏe, tiền bạc và tự do',styles['h2']),Spacer(1,18*mm),Paragraph('Nguyên tác: eternity4719 và cộng tác viên',styles['p']),Paragraph(coverage,styles['p']),Spacer(1,8*mm),Paragraph('Bản dịch độc lập có hỗ trợ AI · CC BY 4.0<br/>Nguồn được ghim ngày 04-11-2026',styles['source']),PageBreak(),Paragraph('Mục lục',styles['h1'])]
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Text',fontSize=10,leading=15,spaceBefore=5,leftIndent=0,rightIndent=15)]
    story += [toc]
    for ident,title,soup in pages:
        story.append(PageBreak())
        group=[]
        def flush():
            nonlocal group
            if group:
                story.extend(group)
                group=[]
        for el in soup.children:
            if isinstance(el,NavigableString):continue
            tag=el.name
            if tag in ('h1','h2','h3'):
                flush();p=Paragraph(inline(el),styles[tag])
                if tag=='h1':p.book_heading=(0,el['id'],el.get_text())
                elif tag=='h3':p.book_heading=(1,el['id'],el.get_text())
                if tag=='h3':group.append(p)
                else:story.append(p)
            elif tag in ('ul','ol'):
                for li_index,li in enumerate(el.find_all('li',recursive=False),1):
                    cls=li.get('class',[]);style=styles['source'] if 'sources' in cls else styles['note'] if 'local-note' in cls else styles['p']
                    prefix=(str(li_index)+'. ' if tag=='ol' else ('• ' if not li.find('strong',recursive=False) else ''))
                    p=Paragraph(prefix+inline(li),style)
                    if group:group.append(p)
                    else:story.append(p)
            elif tag=='p':
                p=Paragraph(inline(el),styles['note'] if 'local-note' in el.get('class',[]) else styles['p'])
                if group:group.append(p)
                else:story.append(p)
            elif tag=='pre':
                p=Paragraph(txt(el.get_text()).replace('\n','<br/>'),styles['source'])
                if group:group.append(p)
                else:story.append(p)
            elif tag=='blockquote':
                for child in el.find_all('p',recursive=False):
                    p=Paragraph(inline(child),styles['note'])
                    if group:group.append(p)
                    else:story.append(p)
            elif tag=='hr':pass
            else:raise ValueError(f'Unsupported PDF element {tag}; add handling rather than silently omit it')
        flush()
    doc.multiBuild(story)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(CACHE/'exports'));args=ap.parse_args()
    out=safe_local(args.out);out.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='build-',dir=safe_local(CACHE)))
    manifest_bytes=(ROOT/'manifest.json').read_bytes()
    meta=json.loads(manifest_bytes)
    input_hashes={'manifest.json':hashlib.sha256(manifest_bytes).hexdigest()}
    chapters=[c for c in meta['chapters'] if c['status'] in ('draft','reviewed') and c['translation']]
    if not chapters:raise ValueError('No completed chapter drafts registered')
    count=sum(c['entries'] for c in chapters);nums=', '.join(str(c['number']) for c in chapters)
    appendices=[a for a in meta.get('appendices',[]) if a['status'] in ('draft','reviewed')]
    complete=len(chapters)==34 and count==772 and len(appendices)==9
    coverage=(f'Bản dịch đầy đủ 34 chương, 772 mục và 9 bài bổ sung. Bản thảo tiếng Việt để đọc và tiếp tục biên tập; chưa được thẩm định chuyên môn độc lập.' if complete else f'Bản nháp gồm các chương {nums}: {len(chapters)}/34 chương, {count}/772 mục; {len(appendices)}/9 bài bổ sung. Đây là bản đang biên tập, chưa đủ toàn bộ nội dung.')
    front=(ROOT/'book/00-loi-mo-dau.md').read_text()
    input_hashes['book/00-loi-mo-dau.md']=hashlib.sha256(front.encode()).hexdigest()
    edition=f'# Thông tin ấn bản\n\n{coverage}\n\nBản dịch dùng ngôn ngữ tự nhiên, giữ nguyên nguồn và bối cảnh nghiên cứu. Ghi chú Việt Nam được đánh dấu riêng. Trạng thái “bản nháp” chưa đồng nghĩa toàn bộ nguồn đã được thẩm định lại.\n\nNguồn gốc: [{meta["source_repository"]}]({meta["source_repository"]}/tree/{meta["source_commit"]}). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).\n'
    materials=[('edition','Thông tin ấn bản',edition),('front','Lời mở đầu',front)]
    for c in chapters:
        p=ROOT/c['translation'];md=p.read_text();input_hashes[c['translation']]=hashlib.sha256(md.encode()).hexdigest(); title=re.search(r'^# (.+)',md,re.M)[1]
        matches=re.findall(r'^### (\d+)\.',md,re.M)
        if list(map(int,matches))!=list(range(1,c['entries']+1)):raise ValueError(f'Incomplete/out-of-order entries in {p}')
        materials.append((f'chapter-{c["number"]:02}',title,md))
    for a in appendices:
        md=(ROOT/a['translation']).read_text();input_hashes[a['translation']]=hashlib.sha256(md.encode()).hexdigest();title=re.search(r'^# (.+)',md,re.M)[1]
        materials.append((a['id'],title,md))
    known_translations={c['translation']:f'chapter-{c["number"]:02}' for c in chapters}
    known_translations.update({a['translation']:a['id'] for a in appendices})
    known_sources={c['source']:f'chapter-{c["number"]:02}' for c in chapters}
    known_sources.update({a['source']:a['id'] for a in appendices})
    paths={f'chapter-{c["number"]:02}':(c['translation'],c['source']) for c in chapters}
    paths.update({a['id']:(a['translation'],a['source']) for a in appendices})
    def absolute_links(md,ident):
        def fix(match):
            label,href=match.groups();parts=urlsplit(href)
            if parts.scheme or href.startswith('#'):return match[0]
            vi_path,zh_path=paths.get(ident,('book/front.md','book/front.md'))
            target_vi=posixpath.normpath(posixpath.join(posixpath.dirname(vi_path),unquote(parts.path)))
            target_zh=posixpath.normpath(posixpath.join(posixpath.dirname(zh_path),unquote(parts.path)))
            linked=known_translations.get(target_vi) or known_sources.get(target_zh)
            if linked and not parts.fragment:return f'[{label}](#{linked}-heading-0)'
            return f'[{label}]({meta["source_repository"]}/blob/{meta["source_commit"]}/{quote(target_zh,safe="/")}{"#"+parts.fragment if parts.fragment else ""})'
        return re.sub(r'\[([^]\n]+)\]\(([^)\s]+)\)',fix,md)
    materials=[(i,t,absolute_links(md,i)) for i,t,md in materials]
    combined='\n\n'.join(f'<a id="{i}-heading-0"></a>\n\n'+md.strip() for i,_,md in materials)+'\n'
    cmaps=prepare_fonts(combined+coverage)
    pages=[(i,t,render_html(md,i)) for i,t,md in materials]
    stem='Song-tot-hon-vi-ban-nhap'
    md_toc='## Mục lục\n\n'+'\n'.join(f'- [{title}](#{ident}-heading-0)' for ident,title,_ in materials)+'\n\n'
    (work/f'{stem}.md').write_text('# Sống tốt hơn\n\n'+md_toc+combined)
    build_epub(work/f'{stem}.epub',pages,coverage,meta)
    build_pdf(work/f'{stem}.pdf',pages,coverage,cmaps)
    for artifact in work.glob(stem+'.*'): os.replace(artifact,out/artifact.name)
    work.rmdir()
    report={'input_sha256':input_hashes,'chapters':[c['number'] for c in chapters],'entries':count,'appendices':[a['id'] for a in appendices],'source_commit':meta['source_commit'],'coverage':coverage,'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.glob(stem+'.*'))}}
    (out/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
