import json
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
for name, file in [('TNR', 'Times New Roman.ttf'),
                   ('TNR-Bold', 'Times New Roman Bold.ttf'),
                   ('TNR-Italic', 'Times New Roman Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily('TNR', normal='TNR', bold='TNR-Bold', italic='TNR-Italic')
body = ParagraphStyle('body', fontName='TNR', fontSize=14, leading=21,
                      alignment=TA_JUSTIFY, firstLineIndent=12.5*mm,
                      spaceAfter=5, allowWidows=0, allowOrphans=0)
h1 = ParagraphStyle('h1', parent=body, fontName='TNR-Bold', alignment=TA_CENTER,
                    firstLineIndent=0, spaceAfter=14, keepWithNext=True)
h2 = ParagraphStyle('h2', parent=body, fontName='TNR-Bold', alignment=TA_LEFT,
                    firstLineIndent=0, spaceBefore=10, spaceAfter=8, keepWithNext=True)
center = ParagraphStyle('center', parent=body, alignment=TA_CENTER, firstLineIndent=0)
left = ParagraphStyle('left', parent=body, alignment=TA_LEFT, firstLineIndent=0)
bib = ParagraphStyle('bib', parent=body, alignment=TA_LEFT, firstLineIndent=0, spaceAfter=10)

class Contents(TableOfContents):
    def wrap(self, width, height):
        entries = self._lastEntries or [(0, 'Содержание', 0, None)]
        rows = [[p(text, left), p(str(page), left)] for _, text, page, _ in entries]
        self._table = Table(rows, colWidths=[width-30, 30], rowHeights=32,
                            style=[('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                   ('RIGHTPADDING', (0, 0), (-1, -1), 0)])
        return self._table.wrapOn(self.canv, width, height)


class Report(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'h1':
            text = flowable.getPlainText()
            self.notify('TOCEntry', (0, text, self.page))


def footer(canvas, doc):
    canvas.setTitle('Учебная практика КТ1 - Сборка и тестирование серверного оборудования')
    canvas.setAuthor('Новожилов Василий Алексеевич')
    if doc.page > 1:
        canvas.setFont('TNR', 14)
        canvas.drawCentredString(A4[0]/2, 12*mm, str(doc.page))


def p(text, style=body):
    return Paragraph(escape(text), style)

out = ROOT / 'submission'
out.mkdir(exist_ok=True)
story = []
for text in ['МИНОБРНАУКИ РОССИИ',
             'Федеральное государственное бюджетное образовательное учреждение высшего образования',
             '«МИРЭА - Российский технологический университет»', '(РТУ МИРЭА)']:
    story.append(p(text, center))
story.append(Spacer(1, 24*mm))
story.append(Paragraph('<b>ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ</b>', center))
story.append(p('КТ1 Исследовательский этап', center))
story.append(Spacer(1, 8*mm))
story.append(p('Тема', center))
story.append(Paragraph('<b>Сборка и тестирование серверного оборудования</b>', center))
story.append(Spacer(1, 13*mm))
for text in ['Выполнил: Новожилов Василий Алексеевич', 'Группа: ИКБО-10-24',
             'Место практики: ООО «Бюджетные и Финансовые Технологии»',
             'Руководитель от университета: Синицын Анатолий Васильевич',
             'Руководитель от предприятия: Жиркова М. И.']:
    story.append(p(text, left))
story.append(Spacer(1, 20*mm))
story.append(p('Москва 2026', center))
story.append(PageBreak())
story.append(Paragraph('Содержание', ParagraphStyle('toc-title', parent=h1)))
toc = Contents()
toc.levelStyles = [ParagraphStyle('toc', parent=left, leading=32, spaceBefore=0, spaceAfter=0)]
story.append(toc)

for block in (ROOT/'docs/report.txt').read_text().strip().split('\n\n'):
    if block.startswith('# '):
        story.extend([PageBreak(), p(block[2:], h1)])
    elif block.startswith('## '):
        story.append(p(block[3:], h2))
    else:
        story.append(p(block.replace('\n', ' ')))
story.extend([PageBreak(), p('Список использованных источников', h1)])
sources = json.loads((ROOT/'docs/sources.json').read_text())
for source in sources:
    text = f"{source['id']}. {source['reference']} - URL: {source['url']} (дата обращения: 05.10.2026)."
    story.append(p(text, bib))
report = out/'Отчет_ИКБО-10-24_НовожиловВА_КТ1.pdf'
doc = Report(str(report), pagesize=A4, leftMargin=30*mm, rightMargin=10*mm,
             topMargin=20*mm, bottomMargin=20*mm, title='Учебная практика КТ1',
             author='Новожилов Василий Алексеевич')
doc.multiBuild(story, onFirstPage=footer, onLaterPages=footer)
original = ROOT/'tmp/research/combined-metrics.pdf'
if original.exists():
    reader = PdfReader(original)
    writer = PdfWriter()
    for page in [0, 23]:
        writer.add_page(reader.pages[page])
    writer.add_metadata({'/Title': 'Chhetri et al. 2022 - original pages 1 and 24',
                         '/Author': 'Chhetri, Dehury, Lind, Srirama, Fensel',
                         '/Subject': 'Source excerpt, DOI 10.3390/bdcc6010026, CC BY 4.0'})
    (out/'translation').mkdir(exist_ok=True)
    with (out/'translation/original.pdf').open('wb') as stream:
        writer.write(stream)
print(report)
print('Pages:', len(PdfReader(report).pages))
