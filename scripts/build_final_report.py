"""Build a source-backed Vietnamese report. PDF rendering is a separate native step."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/report'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def field(paragraph,instruction):
    node=OxmlElement('w:fldSimple');node.set(qn('w:instr'),instruction);paragraph._p.append(node)
def plain(text):return re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',text).replace('`','').replace('**','')

def measured_tables():
    parts=['# BẢNG KẾT QUẢ THỰC NGHIỆM\n','Các bảng được đọc trực tiếp từ CSV có manifest; không lấy con số từ câu chữ của báo cáo. Timestamps/hash ở manifest là phiên bản phép đo, không tự đổi thành measurement cho mọi source code mới.\n']
    specs=[('prediction','Bảng KQ.1. Prediction trên cùng test split',['model','accuracy','precision','recall','f1','roc_auc','pr_auc'],None),('diabetes_rag','Bảng KQ.2. Retrieval confirmatory phrasings',['strategy','recall_at_3','precision_at_returned','mrr_at_3','citation_provenance','latency_ms'],lambda row:row['split']=='confirmatory_phrasing'),('diabetes_mas','Bảng KQ.3. Offline MAS/direct, khác retry budget',['method','runs','task_completion','evidence_relevance','safety_invariants','latency_ms'],None),('rl','Bảng KQ.4. Policy trên cùng simulator evaluation seeds',['policy','average_episode_reward','completion_rate','reward_variance_across_scenarios','unsafe_action_attempts'],None),('diabetes_safety','Bảng KQ.5. Current finite safety expectations',['layer','cases','passed','pass_rate'],None),('diabetes_llm','Bảng KQ.6. LLM summary, acceptance có điều kiện',['questions','actual_llm_responses','independent_verifier_acceptance','latency_ms','input_tokens','output_tokens'],None)]
    labels={'model':'Model','accuracy':'Accuracy','precision':'Precision','recall':'Recall','f1':'F1','roc_auc':'ROC-AUC','pr_auc':'AP','strategy':'Strategy','recall_at_3':'Recall@3','precision_at_returned':'Precision returned','mrr_at_3':'MRR@3','citation_provenance':'Provenance','latency_ms':'Latency ms','method':'Method','runs':'Runs','task_completion':'Completion','evidence_relevance':'Evidence relevance','safety_invariants':'Safety invariant','policy':'Policy','average_episode_reward':'Avg reward','completion_rate':'Completion','reward_variance_across_scenarios':'Reward variance','unsafe_action_attempts':'Unsafe attempts','layer':'Layer','cases':'Cases','passed':'Passed','pass_rate':'Pass rate','questions':'Questions','actual_llm_responses':'LLM outputs','independent_verifier_acceptance':'Conditional acceptance','input_tokens':'Input tokens','output_tokens':'Output tokens'}
    evidence=[]
    for name,title,keys,where in specs:
        path=ROOT/f'experiments/results/{name}.csv';manifest=ROOT/f'experiments/results/{name}.manifest.json'
        meta=json.loads(manifest.read_text(encoding='utf-8'))
        for output,digest in meta['outputs'].items():
            if sha(ROOT/output)!=digest:raise RuntimeError('Measured artifact checksum mismatch: '+output)
        rows=list(csv.DictReader(path.open(encoding='utf-8')))
        if where:rows=[row for row in rows if where(row)]
        parts+=['## '+title+'\n','| '+' | '.join(labels.get(k,k) for k in keys)+' |','| '+' | '.join(['---']*len(keys))+' |']
        for row in rows:
            values=[]
            for key in keys:
                value=row[key]
                try:value=f'{float(value):.6f}' if '.' in value else value
                except ValueError:pass
                values.append(value.replace('|','/'))
            parts.append('| '+' | '.join(values)+' |')
        seed=meta['seed']
        seed_display=f'{len(seed)} fixed evaluation seeds, {min(seed)}..{max(seed)}; full list in manifest' if isinstance(seed,list) else str(seed)
        parts.append(f"\nNguồn: `experiments/results/{name}.csv`; manifest timestamp `{meta['timestamp']}`; seed `{seed_display}`. Scope: {json.loads((ROOT/f'experiments/results/{name}.json').read_text(encoding='utf-8'))['scope']}\n")
        evidence.append({'name':name,'csv_sha256':sha(path),'manifest_sha256':sha(manifest),'measurement_timestamp':meta['timestamp'],'measurement_code_version':meta['code_version']})
    # All six attempted question outcomes, including failures to generate.
    parts+=['## Bảng KQ.7. Toàn bộ sáu câu LLM benchmark\n','| Question ID | Language | Mode | Accepted | Provider error |','| --- | --- | --- | --- | --- |']
    for row in csv.DictReader((ROOT/'experiments/results/diabetes_llm_rows.csv').open(encoding='utf-8')):
        parts.append('| '+' | '.join(row[k] or '—' for k in ['question_id','language','generation_mode','accepted','provider_error'])+' |')
    parts.append('\nNguồn: diabetes_llm_rows.csv. Accepted coverage 3/6; 3/3 chỉ là acceptance có điều kiện trên generated outputs. Non-generation không bị loại khỏi bảng.\n')
    text='\n'.join(parts);(OUT/'07_measured_tables.md').write_text(text,encoding='utf-8');return evidence

def appendix():
    parts=['# PHỤ LỤC: TRUY VẾT SOURCE, KIỂM THỬ VÀ DEMO\n','## A. Code excerpts từ implementation\n','Các trích đoạn dưới đây được lấy tự động từ source hiện tại. Chúng giải thích cơ chế, không thay cho toàn bộ source hoặc output kiểm thử.\n']
    snippets=[('backend/app/research/coordinator.py','        async def dispatch(',24),('backend/app/research/api.py',"@router.post('/mas/runs'",28),('backend/app/ml/pipeline.py','class MLP',5),('backend/app/rl/learning.py','',30),('backend/app/research/grounding.py','def publication_errors',28)]
    for name,marker,length in snippets:
        text=(ROOT/name).read_text(encoding='utf-8').splitlines();start=next((i for i,line in enumerate(text) if marker in line),0)
        parts+=['### '+name+f' — từ dòng {start+1}\n','```python','\n'.join(text[start:start+length]),'```',f'Nguồn: `{name}`, SHA256 `{sha(ROOT/name)}`.\n']
    parts+=['## B. Kết quả nghiệm thu cuối\n','Backend 249 PASS; frontend 22 unit PASS; TypeScript/Vite build PASS; browser/API 6 PASS. Migration head, seed, model/policy/encoder/reranker loads và ba HTTPS scenarios được lưu ở docs/validation/phase08. Docker runtime BLOCKED do thiếu engine; cloud deployment NOT_COMPLETED. Các số này là software verification, không phải accuracy của hệ y tế.\n','## C. Lệnh vận hành và handoff\n','```powershell','python -m alembic upgrade head','python scripts/bootstrap_demo.py','npm --prefix frontend run build','python scripts/demo_host.py status','docker compose --env-file .env.compose config --quiet','docker compose --env-file .env.compose up --build --wait','```','Lệnh bootstrap thay đổi schema/graph idempotently và kiểm loaders; chỉ chạy vào database mình có quyền quản lý. Lệnh Compose cuối hiện chưa thành công trên host này. Không đưa secrets vào terminal trình chiếu.\n','## D. Kịch bản và phản biện\n']
    parts.append((ROOT/'docs/defense/demo_2_minutes.md').read_text(encoding='utf-8').replace('# Demo 2 phút — bản ngắn dùng trước giảng viên','### Demo 2 phút'))
    parts.append('## E. Câu hỏi kỹ thuật chọn lọc\n')
    qa=(ROOT/'docs/defense/qa.md').read_text(encoding='utf-8')
    parts.append(qa.replace('# Câu hỏi phản biện kỹ thuật','').replace('\n## ','\n### '))
    (OUT/'08_appendix.md').write_text('\n'.join(parts),encoding='utf-8')

def render_markdown(doc,text):
    lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
            for row in code:
                p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.05
                r=p.add_run(row.expandtabs(4));r.font.name='Consolas';r.font.size=Pt(8)
            i+=1;continue
        image=re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)',line)
        if image:
            path=OUT/image.group(2)
            w,h=Image.open(path).size;width=min(15.2,17.5*w/h)
            p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
            p.add_run().add_picture(str(path),width=Cm(width))
            p=doc.add_paragraph(image.group(1),style='Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[plain(cell.strip()) for cell in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',cell) for cell in row):rows.append(row)
                i+=1
            table=doc.add_table(rows=1,cols=len(rows[0]));table.style='Light Shading Accent 1'
            for j,value in enumerate(rows[0]):table.rows[0].cells[j].text=value
            repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
            for row in rows[1:]:
                cells=table.add_row().cells
                for j,value in enumerate(row[:len(cells)]):cells[j].text=value
            for row in table.rows:
                no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
                for cell in row.cells:
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.05
                        for r in p.runs:r.font.size=Pt(9)
            doc.add_paragraph();continue
        header=re.match(r'^(#{1,3})\s+(.*)',line)
        if header:doc.add_heading(plain(header.group(2)),level=len(header.group(1)));i+=1;continue
        if line.startswith('- '):p=doc.add_paragraph(plain(line[2:]),style='List Bullet')
        else:
            p=doc.add_paragraph(plain(line))
            if line.startswith('Nguồn Hình') or line.startswith('Nguồn:'):
                p.paragraph_format.first_line_indent=Cm(0)
                for r in p.runs:r.italic=True;r.font.size=Pt(10)
        i+=1

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    locks=OUT/'measurement_lock.json'
    inputs_to_lock=[ROOT/f'experiments/results/{name}.csv' for name in ['prediction','diabetes_rag','diabetes_mas','rl','diabetes_safety','diabetes_llm','diabetes_llm_rows']]
    current={path.relative_to(ROOT).as_posix():sha(path) for path in inputs_to_lock}
    if locks.exists() and json.loads(locks.read_text(encoding='utf-8'))['csv_sha256']!=current:
        raise RuntimeError('Measured results changed. Review report narrative and version the evidence before replacing measurement_lock.json; do not combine new tables with old conclusions.')
    if not locks.exists():locks.write_text(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'csv_sha256':current,'meaning':'Frozen evidence snapshot for the manual report narrative; not a benchmark target.'},indent=2),encoding='utf-8')
    evidence=measured_tables();appendix()
    doc=Document();sec=doc.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=Cm(2.5);sec.bottom_margin=Cm(2.3);sec.left_margin=Cm(3);sec.right_margin=Cm(2.3)
    sec.header_distance=Cm(1);sec.footer_distance=Cm(1);sec.different_first_page_header_footer=True
    normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(12);normal.paragraph_format.line_spacing=1.25;normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.widow_control=True
    for name in ['Normal','Heading 1','Heading 2','Heading 3','Caption','List Bullet']:
        style=doc.styles[name];style.font.name='Times New Roman'
        for key in ['ascii','hAnsi','eastAsia','cs']:style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:'+key),'Times New Roman')
    for level,size in [(1,16),(2,14),(3,12)]:
        style=doc.styles[f'Heading {level}'];style.font.size=Pt(size);style.font.bold=True;style.font.color.rgb=RGBColor.from_string('14334D');style.paragraph_format.keep_with_next=True;style.paragraph_format.space_before=Pt(12);style.paragraph_format.space_after=Pt(7)
        if level==1:style.paragraph_format.page_break_before=True
    doc.styles['Caption'].font.size=Pt(10);doc.styles['Caption'].font.italic=True
    header=sec.header.paragraphs[0];header.text='DIABETES MULTI-AGENT INTELLIGENT SUPPORT SYSTEM  |  NHÓM 13 – LỚP 06';header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    for r in header.runs:r.font.size=Pt(8);r.font.color.rgb=RGBColor(90,90,90)
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER;footer.add_run('Trang ');field(footer,'PAGE')
    for text,size,bold in [('HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG',14,True),('KHOA CÔNG NGHỆ THÔNG TIN',13,True),('',12,False),('BÁO CÁO TIỂU LUẬN CUỐI KỲ',17,True),('PHÁT TRIỂN CÁC HỆ THỐNG THÔNG MINH',14,True),('',12,False),('DIABETES MULTI-AGENT\nINTELLIGENT SUPPORT SYSTEM',21,True),('Hệ đa agent hỗ trợ tìm hiểu bệnh tiểu đường',15,True),('',12,False),('Giảng viên hướng dẫn: PGS.TS. Trần Đình Quế',13,False),('Sinh viên: Nguyễn Bá Việt Hùng — B23DCCN358',13,False),('Nhóm 13 — Lớp 06',13,False),('',12,False),('Bản kỹ thuật Phase 08 — nghiệm thu Docker còn BLOCKED',11,True),('Hà Nội, tháng 11 năm 2026',13,False)]:
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(10);r=p.add_run(text);r.font.size=Pt(size);r.bold=bold
    doc.add_heading('QUY ƯỚC VÀ TÌNH TRẠNG NGHIỆM THU',level=1)
    doc.add_paragraph('Báo cáo bám cấu trúc trong hai ảnh yêu cầu của giảng viên và tham khảo hình thức tiểu luận 03. Chỉ dùng code, artifact và output thực có truy vết. Không trình bày synthetic demo như bệnh nhân thật, LLM API như tự train, hoặc verifier acceptance như medical accuracy.')
    doc.add_paragraph('Bản native/HTTPS đã được kiểm chứng; Docker Compose mới parse được, chưa build/start do host không có engine/WSL. Cloud hosting NOT_COMPLETED. Vì còn acceptance chưa chạy, trạng thái cuối Phase 08 là BLOCKED, chưa xác nhận hoàn thành 100% hoặc READY_FOR_DEFENSE.')
    doc.add_paragraph('Các metric lịch sử giữ timestamp/corpus/model/seed tại lần đo; Phase 08 không train lại frozen DL/RL. Benchmark LLM sáu câu mới có ba output LLM được automated verifier chấp nhận, hai clarification và một extractive fallback. Đọc cả mẫu số và các trường hợp không sinh.')
    doc.add_heading('TÓM TẮT',level=1)
    doc.add_paragraph('Đề tài xây dựng MAS điều phối tập trung cho giáo dục về tiểu đường, nối Prediction, Knowledge, RL Decision, Education, Verifier và Safety qua typed messages, bounded feedback và persistence. MLP được train trên Pima; graph/RAG dùng nguồn NIDDK có version; LLM inference qua Groq; Q-learning chọn action giáo dục trong simulator. Kết quả chứng minh tích hợp và audit thực hiện được, nhưng không chứng minh ưu thế phổ quát của DL/RL/MAS hoặc hiệu quả lâm sàng. Bản native/HTTPS đạt software checks; Docker runtime là gate triển khai còn thiếu.')
    doc.add_heading('MỤC LỤC',level=1);field(doc.add_paragraph(),'TOC \\o "1-3" \\h \\z \\u')
    doc.add_heading('DANH MỤC HÌNH',level=1)
    for path in sorted(OUT.glob('0[1-8]_*.md')):
        for caption in re.findall(r'!\[([^\]]+)\]\([^)]+\)',path.read_text(encoding='utf-8')):doc.add_paragraph(caption)
    doc.add_heading('DANH MỤC BẢNG VÀ TỪ VIẾT TẮT',level=1)
    doc.add_paragraph('Bảng 2.1: quyền hạn agent. Bảng 3.1: contracts. Bảng 4.1: feature dictionary. Bảng 4.2: RL actions. Bảng KQ.1–KQ.7: prediction, RAG, MAS, RL, safety, LLM summary và per-question outcomes.')
    doc.add_paragraph('MAS: Multi-Agent System; DL: Deep Learning; KG: Knowledge Graph; RAG: Retrieval-Augmented Generation; RL: Reinforcement Learning; MDP: Markov Decision Process; LLM: Large Language Model; BCE: Binary Cross Entropy; AP: Average Precision; MRR: Mean Reciprocal Rank; ERD: Entity Relationship Diagram; NIDDK: National Institute of Diabetes and Digestive and Kidney Diseases.')
    inputs=sorted(OUT.glob('0[1-8]_*.md'))
    for path in inputs:render_markdown(doc,path.read_text(encoding='utf-8'))
    output=OUT/'tieuluan_final_06_13_hungnbv.docx';doc.save(output)
    manifest={'timestamp':datetime.now(timezone.utc).isoformat(),'author_confirmed':{'name':'Nguyễn Bá Việt Hùng','student_id':'B23DCCN358','group':13,'class':'06','advisor':'PGS.TS. Trần Đình Quế'},'readiness':'BLOCKED_DOCKER_RUNTIME','training_rerun':False,'measured_evidence':evidence,'chapter_sha256':{p.name:sha(p) for p in inputs},'docx_sha256':sha(output),'pdf_status':'PENDING_NATIVE_RENDER'}
    (OUT/'build_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print(output.relative_to(ROOT),output.stat().st_size,'bytes;',len(inputs),'source chapters/appendices')

if __name__=='__main__':main()
