#!/usr/bin/env python3
"""Register completed chapters; never infer completion from a partially written file."""
from pathlib import Path
import argparse, json, re
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'manifest.json';m=json.loads(p.read_text())
ap=argparse.ArgumentParser();ap.add_argument('chapters',nargs='+',help='Chapter numbers or appendix ids a1–a9');args=ap.parse_args()
for token in args.chapters:
 if token.startswith('a'):
  a=next(a for a in m['appendices'] if a['id']==token)
  text=(ROOT/a['translation']).read_text()
  if not re.search(r'^# .+',text,re.M) or len(text)<500:raise ValueError(f'Empty appendix {token}')
  if not (ROOT/f'editorial/{token}-review.md').exists():raise ValueError(f'Missing review for {token}')
  a['status']='draft'
  continue
 n=int(token)
 c=m['chapters'][n-1];files=list((ROOT/'book').glob(f'{n:02}-*.md'))
 if len(files)!=1:raise ValueError(f'Expected exactly one translation file for chapter {n}')
 text=files[0].read_text();got=list(map(int,re.findall(r'^### (\d+)\.',text,re.M)))
 if got!=list(range(1,c['entries']+1)):raise ValueError(f'Incomplete chapter {n}: {len(got)}/{c["entries"]}')
 for label in ('Chi phí','Nói dễ hiểu','Lợi ích','Mức độ bằng chứng','Nguồn','Lưu ý'):
  if len(re.findall(r'^- \*\*'+re.escape(label)+r':\*\*',text,re.M))!=c['entries']:raise ValueError(f'Missing/duplicate field {label} in chapter {n}')
 if not (ROOT/f'editorial/{n:02}-review.md').exists():raise ValueError(f'Missing editorial review for chapter {n}')
 c['translation']=str(files[0].relative_to(ROOT));c['status']='draft'
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
done=[c for c in m['chapters'] if c['status'] in ('draft','reviewed')]
lines=['# Tiến độ bản dịch','',f'Đã có bản nháp đầy đủ: {len(done)}/34 chương, {sum(c["entries"] for c in done)}/772 mục.','', '“Bản nháp” nghĩa là đã chuyển ngữ đủ mục và tự đối chiếu; chưa phải bản đã thẩm định độc lập toàn bộ nguồn hay bản địa hóa hoàn chỉnh.','', '| Chương | Nội dung | Số mục | Trạng thái |','| --- | --- | ---: | --- |']
for c in m['chapters']:
 title=re.search(r'^# (.+)',(ROOT/c['translation']).read_text(),re.M)[1] if c['translation'] else c['source_title']
 link=f'[{title}]({c["translation"]})' if c['translation'] else title
 lines.append(f'| {c["number"]} | {link} | {c["entries"]} | '+('Đã có bản nháp' if c['status']=='draft' else 'Chờ dịch')+' |')
lines += ['', '## Bài bổ sung', '', '| Bài | Trạng thái |', '| --- | --- |']
for a in m['appendices']:
 ready=a['status'] in ('draft','reviewed')
 title=re.search(r'^# (.+)',(ROOT/a['translation']).read_text(),re.M)[1] if ready else Path(a['source']).stem
 label=f'[{title}]({a["translation"]})' if ready else title
 lines.append(f'| {label} | '+('Đã có bản nháp' if ready else 'Chờ dịch')+' |')
(ROOT/'PROGRESS.md').write_text('\n'.join(lines)+'\n')
print(f'Registered {args.chapters}; {len(done)}/34 chapters, {sum(c["entries"] for c in done)}/772 entries')
