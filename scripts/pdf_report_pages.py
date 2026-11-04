from pathlib import Path
import json,re,unicodedata
import fitz
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/report'
def normalize(text):return re.sub(r'\s+','',unicodedata.normalize('NFKC',text)).casefold()
pages=[normalize(page.get_text()) for page in fitz.open(FOLDER/'tieuluan_final_06_13_hungnbv.pdf')]
result={}
for heading in json.loads((FOLDER/'pdf_headings.json').read_text(encoding='utf-8')):
    target=normalize(heading['title'])
    matches=[i+1 for i,text in enumerate(pages) if target in text]
    if not matches:raise RuntimeError('Rendered heading missing from PDF: '+heading['title'])
    result[heading['id']]=max(matches)
print(json.dumps(result))
