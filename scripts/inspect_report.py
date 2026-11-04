"""Validate report artifacts and render a contact sheet for visual inspection."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
import fitz
from PIL import Image,ImageDraw
from docx import Document

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/report';AUDIT=ROOT/'docs/validation/phase08/report_layout';AUDIT.mkdir(parents=True,exist_ok=True)
pdf=fitz.open(OUT/'tieuluan_final_06_13_hungnbv.pdf')
pages=[];overflow=[];texts=[]
for index,page in enumerate(pdf):
    text=page.get_text();texts.append(text)
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for span in line['spans']:
                x0,y0,x1,y1=span['bbox']
                if x0<10 or x1>page.rect.width-10 or y0<0 or y1>page.rect.height:overflow.append({'page':index+1,'bbox':span['bbox'],'text':span['text'][:70]})
    pages.append({'page':index+1,'characters':len(text),'images':len(page.get_images())})
    thumbnail=page.get_pixmap(matrix=fitz.Matrix(.35,.35))
    thumbnail.save(AUDIT/f'page-{index+1:03d}.png')
columns=6;thumb_w=230;thumb_h=335
for batch in range(0,len(pdf),24):
    count=min(24,len(pdf)-batch);sheet=Image.new('RGB',(columns*thumb_w,((count+columns-1)//columns)*thumb_h),'#e1e5e7');draw=ImageDraw.Draw(sheet)
    for i in range(count):
        thumb=Image.open(AUDIT/f'page-{batch+i+1:03d}.png').convert('RGB');thumb.thumbnail((thumb_w-16,thumb_h-30))
        x=(i%columns)*thumb_w+8;y=(i//columns)*thumb_h+22;sheet.paste(thumb,(x,y));draw.text((x,y-17),str(batch+i+1),fill='black')
    sheet.save(AUDIT/f'contact-{batch//24+1}.png')
full='\n'.join(texts)
assert len(pdf)>20
assert all(title in full for title in ['CHƯƠNG 1. GIỚI THIỆU','CHƯƠNG 2. HỆ ĐA AGENT','CHƯƠNG 3. KIẾN TRÚC TỔNG QUAN','CHƯƠNG 4. CÁC THÀNH PHẦN HỆ THỐNG','CHƯƠNG 5. CODE, DEMO VÀ ĐÁNH GIÁ'])
assert 'Nguyễn Bá Việt Hùng' in full and 'B23DCCN358' in full
assert not re.search(r'Error!|Bookmark not defined|Reference source not found',full)
assert not overflow,overflow[:3]
document=Document(OUT/'tieuluan_final_06_13_hungnbv.docx')
assert len(document.inline_shapes)>=15
result={'timestamp':datetime.now(timezone.utc).isoformat(),'pdf_pages':len(pdf),'pages':pages,'text_outside_page':overflow,'docx_inline_images':len(document.inline_shapes),'checks':'All chapters, author, page bounds, nonempty report and no unresolved reference errors verified. Visual inspection is separate.','renderer':json.loads((OUT/'pdf_render.json').read_text())}
(AUDIT/'checks.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
manifest=json.loads((OUT/'build_manifest.json').read_text(encoding='utf-8'))
manifest.update(pdf_status='RENDERED_AND_STRUCTURALLY_CHECKED',pdf_pages=len(pdf),docx_sha256=hashlib.sha256((OUT/'tieuluan_final_06_13_hungnbv.docx').read_bytes()).hexdigest(),pdf_sha256=hashlib.sha256((OUT/'tieuluan_final_06_13_hungnbv.pdf').read_bytes()).hexdigest(),pdf_renderer='Chromium, measured PDF TOC; native Word export did not complete')
(OUT/'build_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'pages':len(pdf),'docx_images':len(document.inline_shapes),'overflow':len(overflow),'contact_sheets':(len(pdf)+23)//24}))
