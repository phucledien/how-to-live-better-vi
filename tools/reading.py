"""Semantic reading edition, shared by EPUB and PDF. No prose is discarded."""
import re
import markdown
from bs4 import BeautifulSoup, NavigableString, Comment

ALIASES={'Nói dễ hiểu':'Ý chính','Lợi ích':'Chi tiết và cơ sở','Nguồn':'Dẫn chứng'}
FIELDS=('Chi phí','Ý chính','Chi tiết và cơ sở','Mức độ bằng chứng','Dẫn chứng','Lưu ý')
NOTE_PREFIX=('Ghi chú cho độc giả Việt Nam','Ghi chú cho bản Việt','Ghi chú Việt Nam')

def canonical_labels(md):
    for old,new in ALIASES.items():
        md=md.replace(f'**{old}:**',f'**{new}:**')
    return md

def link_references(md,ident,counts):
    """Link prose references only; never treat research years as entry numbers."""
    current=int(ident.split('-')[1]) if ident.startswith('chapter-') else None
    intro=True; source=False; out=[]
    def link(label,chapter,entry):
        if 1<=entry<=counts.get(chapter,0):return f'[{label}](#chapter-{chapter:02}-entry-{entry})'
        return label
    def prose(s):
        # Protect existing Markdown/HTML links, URLs, and inline code.
        parts=re.split(r'(\[[^\]\n]*\]\([^\)]+\)|<[^>]+>|https?://\S+|`[^`]+`)',s)
        for i in range(0,len(parts),2):
            t=parts[i];tokens=[]
            def hold(value):
                tokens.append(value);return f'\x01{len(tokens)-1}\x02'
            number_list=r'\d+(?:(?:\s*[–,-]\s*|\s+và\s+)\d+)*'
            def sequence(label,chapter):
                # The first number is part of the full label; subsequent numbers
                # remain separate links, so a range has clickable endpoints.
                first=True
                def replace(m):
                    nonlocal first
                    if first:
                        first=False
                        return link(m[0],chapter,int(re.search(r'\d+',m[0])[0]))
                    return link(m[0],chapter,int(m[0]))
                return re.sub(r'^[^\d]*\d+|\d+',replace,label)
            def forward(m):
                chapter=int(m[3]);entry=re.match(r'(?:mục|điều)\s+(\d+)',m[4])
                first=link(m[2]+entry[0],chapter,int(entry[1]))
                rest=re.sub(r'\d+',lambda n:link(n[0],chapter,int(n[0])),m[4][entry.end():])
                return hold(first+rest)
            t=re.sub(r'\b(([Cc]hương\s+(\d+)\s*[,.:]?\s*)((?:mục|điều)\s+'+number_list+r'))\b',
                     forward,t)
            t=re.sub(r'\b([Mm]ục\s+(\d+)\s+(?:của\s+)?chương\s+(\d+))\b',lambda m:hold(link(m[1],int(m[3]),int(m[2]))),t)
            if current:
                t=re.sub(r'\b([Mm]ục\s+'+number_list+r')\b',lambda m:hold(sequence(m[1],current)),t)
                if intro:
                    t=re.sub(r'\((\d{1,2}(?:\s*[,;–-]\s*\d{1,2})*)\)',lambda m:'('+re.sub(r'\d+',lambda n:link(n[0],current,int(n[0])),m[1])+')',t)
            t=re.sub(r'\x01(\d+)\x02',lambda m:tokens[int(m[1])],t);parts[i]=t
        return ''.join(parts)
    for line in md.splitlines():
        if line.startswith('### '):intro=False
        if line.startswith('- **'):source=line.startswith(('- **Nguồn:','- **Dẫn chứng:'))
        out.append(line if source or line.startswith(('<!--','#')) else prose(line))
    return '\n'.join(out)+'\n'

def parse_fragment(md):
    # Continuation paragraphs use two-space CommonMark indentation.
    md=re.sub(r'^  (?=\S)','',md,flags=re.M)
    soup=BeautifulSoup(markdown.markdown(md.strip(),extensions=['extra']),'html.parser')
    for c in soup.find_all(string=lambda s:isinstance(s,Comment)):c.extract()
    # Markdown merges adjacent quoted paragraphs. Keep separately labelled
    # notices independent, so a safety correction cannot enter a local-note popup.
    for quote in list(soup.find_all('blockquote',recursive=False)):
        current=quote
        for child in list(quote.children):
            if getattr(child,'name',None)=='p' and child.find('strong',recursive=False) and child.get_text(strip=True).startswith(NOTE_PREFIX+('Đính chính','Ghi chú biên tập','Ghi chú hiệu đính')):
                if child is not quote.find('p',recursive=False):
                    new=soup.new_tag('blockquote');current.insert_after(new);current=new
            if current is not quote:current.append(child.extract())
    return soup

def structured_markdown(md,ident):
    md=canonical_labels(md)
    if not ident.startswith('chapter-'):return parse_fragment(md)
    chunks=re.split(r'(?m)^(### \d+\.[^\n]*)\n',md)
    soup=parse_fragment(chunks[0]); local=[]
    for note in list(soup.find_all('blockquote',recursive=False)):
        if note.get_text().strip().startswith(NOTE_PREFIX):local.append(note.extract())
    for note in local:soup.append(note)
    for offset in range(1,len(chunks),2):
        title=chunks[offset][4:];body=chunks[offset+1];number=int(re.match(r'\d+',title)[0]);key=f'{ident}-entry-{number}'
        h=soup.new_tag('h3',id=key);h.string=title;soup.append(h)
        fields=re.split(r'(?m)^- \*\*([^:\n]+):\*\*\s*',body)
        values={fields[i]:fields[i+1].strip() for i in range(1,len(fields),2)}
        if not all(k in values for k in FIELDS):raise ValueError(f'Missing fields: {key}: {values.keys()}')
        def block(label,cls):
            tag=soup.new_tag('div',attrs={'class':cls,'data-field':label})
            frag=parse_fragment(values[label])
            # Keep edition-specific notes out of a preceding field's body.
            notes=[]
            for b in list(frag.find_all('blockquote',recursive=False)):notes.append(b.extract())
            for node in list(frag.contents):tag.append(node.extract())
            return tag,notes
        extras=[]
        main,notes=block('Ý chính','main-copy');soup.append(main);extras+=notes
        cost,notes=block('Chi phí','cost');soup.append(cost);extras+=notes
        caution,notes=block('Lưu ý','caution');soup.append(caution);extras+=notes
        detail=soup.new_tag('div',attrs={'class':'research','id':key+'-research'})
        for label,cls in [('Chi tiết và cơ sở','detail'),('Mức độ bằng chứng','grade'),('Dẫn chứng','sources')]:
            b,notes=block(label,cls);detail.append(b);extras+=notes
        soup.append(detail)
        # Preserve any extra named fields, including translator's notes.
        for label,value in values.items():
            if label not in FIELDS:
                note=soup.new_tag('blockquote');note.append(parse_fragment(f'**{label}:** '+value));extras.append(note)
        for note in extras:soup.append(note)
    return soup

def classify_notes(soup,ident):
    for index,b in enumerate(list(soup.find_all('blockquote',recursive=False))):
        text=b.get_text(' ',strip=True)
        b['class']='local-note' if text.startswith(NOTE_PREFIX) else 'correction'
        b['id']=f'{ident}-note-{index+1}'
    # A few notes were authored as plain paragraphs instead of quotes.
    for index,p in enumerate(list(soup.find_all('p',recursive=False))):
        if p.get_text(' ',strip=True).startswith(NOTE_PREFIX):p['class']='local-note';p['id']=f'{ident}-pnote-{index+1}'
    return soup

def epub_reading(soup,ident):
    """Native Apple Books footnotes: hidden until tapped; no JavaScript needed."""
    out=BeautifulSoup(str(soup),'html.parser')
    for box in list(out.select('div.research, blockquote.local-note, p.local-note')):
        key=box['id'];is_research='research' in box.get('class',[])
        label='i  Chi tiết và dẫn chứng' if is_research else 'i  Ghi chú Việt Nam'
        ref=out.new_tag('p',attrs={'class':'note-toggle','data-ui':'true','id':key+'-ref'})
        a=out.new_tag('a',href=f'#{key}',attrs={'epub:type':'noteref','role':'doc-noteref'});a.string=label;ref.append(a)
        box.insert_before(ref);box.name='aside';box['epub:type']='footnote';box['role']='doc-footnote'
        title=out.new_tag('p',attrs={'class':'note-heading','data-ui':'true'});title.string=label[3:];box.insert(0,title)
        back=out.new_tag('p',attrs={'class':'note-back','data-ui':'true'});a=out.new_tag('a',href=f'#{key}-ref');a.string='Về nội dung đang đọc';back.append(a);box.append(back)
    for d in out.select('[data-field]'):
        field=d['data-field']
        if field=='Ý chính':continue
        title=out.new_tag('p',attrs={'class':'field-label','data-ui':'true'});title.string=('!  ' if field=='Lưu ý' else '')+field;d.insert(0,title)
    return out
