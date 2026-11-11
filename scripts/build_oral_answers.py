"""Build editable DOCX and printable HTML from the 51-answer study guide."""
from pathlib import Path
import html
import json
import re
from docx import Document
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/defense/tra_loi_51_cau_van_dap'


def inline_html(value):
    value = html.escape(value)
    value = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', value)
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)


def runs(paragraph, value):
    for token in re.split(r'(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?://[^)]+\))', value):
        if token.startswith('**') and token.endswith('**'):
            paragraph.add_run(token[2:-2]).bold = True
        elif token.startswith('`') and token.endswith('`'):
            run = paragraph.add_run(token[1:-1]); run.font.name = 'Consolas'; run.font.size = Pt(10)
        else:
            link = re.fullmatch(r'\[([^\]]+)\]\((https?://[^)]+)\)', token)
            paragraph.add_run(f'{link[1]} ({link[2]})' if link else token)


def main():
    source = BASE.with_suffix('.md').read_text(encoding='utf-8')
    numbers = [int(n) for n in re.findall(r'^### Câu (\d+)\.', source, re.M)]
    assert numbers == list(range(1, 52)), 'Missing, duplicate or unordered answer'
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21); section.page_height = Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2); section.right_margin = Cm(1.7)
    normal = doc.styles['Normal']; normal.font.name = 'Times New Roman'; normal.font.size = Pt(12)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12
    for name, size in [('Title', 20), ('Heading 1', 16), ('Heading 2', 14)]:
        doc.styles[name].font.name = 'Times New Roman'; doc.styles[name].font.size = Pt(size)
    header = section.header.paragraphs[0]
    header.text = 'B23DCCN358 | Phát triển các hệ thống thông minh | Ôn tập vấn đáp'
    header.runs[0].font.size = Pt(9)
    footer = section.footer.paragraphs[0]; footer.alignment = 2
    footer.add_run('Trang ')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    output = []
    lines = source.splitlines(); i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line.startswith('```'):
            code = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]); i += 1
            output.append('<pre>' + html.escape('\n'.join(code)) + '</pre>')
            for row in code:
                p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
                run = p.add_run(row); run.font.name = 'Consolas'; run.font.size = Pt(9)
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    rows.append(cells)
                i += 1
            table = doc.add_table(rows=0, cols=len(rows[0])); table.style = 'Table Grid'
            output.append('<table>')
            for index, row in enumerate(rows):
                cells = table.add_row().cells
                output.append('<tr>')
                for cell, text in zip(cells, row):
                    runs(cell.paragraphs[0], text)
                    for run in cell.paragraphs[0].runs: run.font.size = Pt(10)
                    tag = 'th' if index == 0 else 'td'
                    output.append(f'<{tag}>{inline_html(text)}</{tag}>')
                if index == 0:
                    repeat = OxmlElement('w:tblHeader'); table.rows[0]._tr.get_or_add_trPr().append(repeat)
                output.append('</tr>')
            output.append('</table>'); continue
        heading = re.match(r'^(#{1,3}) (.*)', line)
        if heading:
            level = len(heading[1]); title = heading[2]
            p = doc.add_paragraph(style='Title' if level == 1 else f'Heading {level-1}')
            runs(p, title)
            if level == 2: p.paragraph_format.page_break_before = True
            output.append(f'<h{level}>{inline_html(title)}</h{level}>')
        else:
            bullet = re.match(r'^(- |\d+\. )(.*)', line)
            p = doc.add_paragraph(style='List Bullet' if bullet and bullet[1] == '- ' else None)
            value = bullet[2] if bullet and bullet[1] == '- ' else line
            runs(p, value)
            output.append('<p>' + ('• ' if bullet and bullet[1] == '- ' else '') + inline_html(value) + '</p>')
        i += 1
    doc.save(BASE.with_suffix('.docx'))
    css = '''@page{size:A4;margin:18mm 17mm 19mm 20mm}body{font:12pt 'Times New Roman',serif;line-height:1.2;color:#182330}h1{font-size:21pt;color:#153d5c}h2{font-size:16pt;break-before:page;color:#153d5c}h3{font-size:14pt;break-after:avoid;color:#153d5c}p{margin:0 0 7pt;orphans:3;widows:3}table{border-collapse:collapse;width:100%;font-size:10pt;margin:9pt 0}th,td{border:1px solid #9aa7b0;padding:5pt;vertical-align:top;overflow-wrap:anywhere}th{background:#eaf1f5}tr{break-inside:avoid}pre{font:9pt Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f6;padding:8pt}code{font:10pt Consolas,monospace;overflow-wrap:anywhere}a{color:#195d89;text-decoration:none}'''
    BASE.with_suffix('.html').write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><title>Đáp án 51 câu vấn đáp</title><style>'+css+'</style><body>'+''.join(output)+'</body></html>', encoding='utf-8')
    print(json.dumps({'answers': len(numbers), 'characters': len(source), 'docx': str(BASE.with_suffix('.docx')), 'html': str(BASE.with_suffix('.html'))}, ensure_ascii=True))


if __name__ == '__main__':
    main()
