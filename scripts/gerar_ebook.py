#!/usr/bin/env python3
"""Gera a edição PDF, o texto Markdown e o gráfico a partir dos fontes.

Executar na raiz do projeto: python scripts/gerar_ebook.py
"""

from decimal import Decimal
from html import escape
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Preformatted, Spacer,
    Table, TableStyle
)

from analisar_carteira import analisar

ROOT = Path(__file__).resolve().parents[1]
W, H = 160 * mm, 230 * mm
MARGIN = 38
CONTENT_WIDTH = W - MARGIN * 2
NAVY = colors.HexColor('#132b37')
TEAL = colors.HexColor('#276c68')
MINT = colors.HexColor('#91d3b5')
INK = colors.HexColor('#18323c')
MUTED = colors.HexColor('#536b75')
PAPER = colors.HexColor('#faf9f4')
PALE = colors.HexColor('#eaf4ee')


def br(value, digits=2):
    return f'{Decimal(str(value)):,.{digits}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fonts_and_styles():
    font_dir = ROOT / 'assets/fonts'
    for name, filename in [('BookSans', 'DejaVuSans.ttf'),
                           ('BookBold', 'DejaVuSans-Bold.ttf'),
                           ('BookMono', 'DejaVuSansMono.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily('BookSans', normal='BookSans', bold='BookBold',
                                  italic='BookSans', boldItalic='BookBold')
    return {
        'body': ParagraphStyle('Body', fontName='BookSans', fontSize=10.2,
                               leading=14.7, textColor=INK, spaceAfter=9),
        'title': ParagraphStyle('Title', fontName='BookBold', fontSize=25,
                                leading=29, textColor=NAVY, spaceAfter=16),
        'kicker': ParagraphStyle('Kicker', fontName='BookBold', fontSize=8,
                                 leading=11, textColor=TEAL, spaceAfter=8),
        'heading': ParagraphStyle('Heading', fontName='BookBold', fontSize=11.2,
                                  leading=15, textColor=TEAL, spaceBefore=5, spaceAfter=6),
        'small': ParagraphStyle('Small', fontName='BookSans', fontSize=8.2,
                                leading=11.5, textColor=MUTED, spaceAfter=7),
        'cell': ParagraphStyle('Cell', fontName='BookSans', fontSize=9,
                               leading=12.3, textColor=INK),
        'tablehead': ParagraphStyle('TableHead', fontName='BookBold', fontSize=8.2,
                                    leading=11.4, textColor=colors.white),
        'formula': ParagraphStyle('Formula', fontName='BookBold', fontSize=15.4,
                                  leading=20, textColor=NAVY),
        'unit': ParagraphStyle('Unit', fontName='BookSans', fontSize=8.5,
                               leading=11.5, textColor=MUTED),
        'code': ParagraphStyle('Code', fontName='BookMono', fontSize=8.5,
                               leading=11.8, textColor=INK),
        'callout': ParagraphStyle('Callout', fontName='BookSans', fontSize=9.4,
                                  leading=13.6, textColor=INK),
        'calloutlabel': ParagraphStyle('CalloutLabel', fontName='BookBold', fontSize=8,
                                       leading=10, textColor=TEAL, spaceAfter=5)
    }


def table_data(kind, book, data, analysis):
    if kind == 'sumario':
        return ['Página', 'Conteúdo'], [[str(i + 2), s['titulo']]
                for i, s in enumerate(book['secoes']) if i > 0]
    if kind == 'dataset':
        return ['Grupo', 'Exposição', 'Sinistros', 'Custo (R$)'], [
            [r['segmento'], br(r['exposicao_contratos_ano'], 0), str(r['sinistros']),
             br(r['custo_total'])] for r in data]
    if kind == 'indicadores':
        return ['Grupo', 'Sin./100', 'Severidade (R$)', 'Custo/exp. (R$)'], [
            [r['segmento'], br(Decimal(r['frequencia']) * 100),
             br(r['severidade']), br(r['custo_por_exposicao'])]
            for r in analysis['por_segmento']]
    if kind == 'totais':
        total = analysis['carteira']
        return ['Exposição total', 'Sinistros', 'Custo total (R$)'], [[
            br(total['exposicao_contratos_ano'], 0), str(total['sinistros']),
            br(total['custo_total'])]]
    raise ValueError(kind)


def make_table(headers, rows, kind, styles):
    if kind == 'sumario':
        widths = [60, CONTENT_WIDTH - 60]
    elif kind == 'totais':
        widths = [CONTENT_WIDTH * .34, CONTENT_WIDTH * .22, CONTENT_WIDTH * .44]
    else:
        widths = [50, 72, 100, CONTENT_WIDTH - 222]
    cells = [[Paragraph(escape(str(x)), styles['tablehead']) for x in headers]]
    cells += [[Paragraph(escape(str(x)), styles['cell']) for x in row] for row in rows]
    table = Table(cells, colWidths=widths, hAlign='LEFT', repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PALE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6 if kind != 'sumario' else 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6 if kind != 'sumario' else 3.5),
        ('LINEBELOW', (0, -1), (-1, -1), .5, colors.HexColor('#cddbd4'))
    ]))
    table.spaceAfter = 11
    return table


def make_chart(analysis):
    rows = analysis['por_segmento']
    labels = [r['segmento'] for r in rows]
    values = [float(r['custo_por_exposicao']) for r in rows]
    total = float(analysis['carteira']['custo_por_exposicao'])
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, ax = plt.subplots(figsize=(6.8, 2.5), facecolor='#faf9f4')
    ax.set_facecolor('#faf9f4')
    bars = ax.barh(labels, values, color=['#276c68', '#529b89', '#91d3b5', '#183b45'],
                   height=.56, zorder=3)
    ax.invert_yaxis()
    ax.axvline(total, color='#b5754c', linestyle='--', linewidth=1.6,
               label=f'Carteira: R$ {br(total)}', zorder=4)
    for bar, value in zip(bars, values):
        ax.text(value + 9, bar.get_y() + bar.get_height() / 2,
                f'R$ {br(value, 0)}', va='center', fontsize=12, color='#18323c',
                bbox={'facecolor': '#faf9f4', 'edgecolor': 'none', 'pad': 1},
                zorder=5)
    ax.set_xlim(0, 480)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: br(x, 0)))
    ax.set_xlabel('Custo observado por contrato-ano (R$)', fontsize=11)
    ax.grid(axis='x', alpha=.18, zorder=0)
    ax.tick_params(axis='both', length=0, labelcolor='#536b75')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(loc='upper right', frameon=False, fontsize=10)
    fig.subplots_adjust(left=.06, right=.98, top=.94, bottom=.22)
    target = ROOT / 'assets/custo_por_exposicao.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=220)
    plt.close(fig)


def cover_page(canvas, doc, book):
    canvas.setTitle(book['titulo'])
    canvas.setAuthor(book['autor'])
    canvas.setSubject(book['subtitulo'])
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor('#244553'))
    for y in range(60, int(H), 56):
        canvas.line(0, y, W, y)
    for x in range(42, int(W), 56):
        canvas.line(x, 0, x, H)
    canvas.setFillColor(MINT)
    canvas.roundRect(MARGIN, H - 69, 141, 25, 12, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont('BookBold', 8)
    canvas.drawString(MARGIN + 14, H - 60, 'E-BOOK / PROJETO DIO')
    canvas.setFillColor(colors.HexColor('#f6f8ef'))
    canvas.setFont('BookBold', 42)
    canvas.drawString(MARGIN - 2, H - 162, 'DO DADO')
    canvas.drawString(MARGIN - 2, H - 215, 'À DECISÃO')
    canvas.setFillColor(colors.HexColor('#b8d1d3'))
    canvas.setFont('BookSans', 12)
    canvas.drawString(MARGIN, H - 258, 'Ciência de dados aplicada à atuária')
    canvas.drawString(MARGIN, H - 280, 'Um guia prático com Python')
    y0 = 190
    for index, height in enumerate([40, 90, 24, 155]):
        x = MARGIN + index * 65
        canvas.setFillColor([TEAL, colors.HexColor('#529b89'), MINT,
                             colors.HexColor('#c1dce0')][index])
        canvas.roundRect(x, y0, 43, height, 5, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#b8d1d3'))
    canvas.setFont('BookSans', 9)
    canvas.drawString(MARGIN, y0 - 27, 'PERGUNTA  /  DADOS  /  INDICADORES  /  DECISÃO')
    canvas.setStrokeColor(colors.HexColor('#496773'))
    canvas.line(MARGIN, 112, W - MARGIN, 112)
    canvas.setFillColor(MINT)
    canvas.setFont('BookBold', 11)
    canvas.drawString(MARGIN, 85, book['autor'].upper())
    canvas.setFillColor(colors.HexColor('#b8d1d3'))
    canvas.setFont('BookSans', 8.6)
    canvas.drawString(MARGIN, 63, 'Projeto educacional desenvolvido com apoio de IA')
    canvas.drawString(MARGIN, 46, book['edicao'])


def body_page(canvas, doc, book):
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.setFont('BookBold', 7)
    canvas.drawString(MARGIN, H - 27, 'DO DADO À DECISÃO')
    canvas.setFillColor(MUTED)
    canvas.setFont('BookSans', 7)
    canvas.drawRightString(W - MARGIN, H - 27, 'DADOS + ATUÁRIA + PYTHON')
    canvas.setStrokeColor(colors.HexColor('#d2ded4'))
    canvas.line(MARGIN, H - 38, W - MARGIN, H - 38)
    canvas.line(MARGIN, 35, W - MARGIN, 35)
    canvas.setFillColor(MUTED)
    canvas.setFont('BookSans', 7.1)
    canvas.drawString(MARGIN, 22, 'Paulo Bernardo | Outubro de 2026')
    canvas.drawRightString(W - MARGIN, 22, f'{doc.page:02d} / {len(book["secoes"]) + 1:02d}')


def block_flowables(block, book, data, analysis, styles):
    kind = block['tipo']
    if kind in ('p', 'h'):
        return [Paragraph(escape(block['texto']), styles['body' if kind == 'p' else 'heading'])]
    if kind == 'bullets':
        style = ParagraphStyle('Bullet', parent=styles['body'], leftIndent=10,
                               firstLineIndent=0, bulletIndent=0, spaceAfter=6)
        return [Paragraph(escape(x), style, bulletText='•') for x in block['itens']]
    if kind == 'callout':
        cell = [Paragraph(escape(block['rotulo'].upper()), styles['calloutlabel']),
                Paragraph(escape(block['texto']), styles['callout'])]
        table = Table([[cell]], colWidths=[CONTENT_WIDTH], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PALE),
            ('LINEBEFORE', (0, 0), (0, -1), 3, MINT),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
        ]))
        table.spaceAfter = 10
        return [table]
    if kind == 'formula':
        cell = [Paragraph(escape(block['texto']), styles['formula']),
                Paragraph(escape(block['unidade']), styles['unit'])]
        table = Table([[cell]], colWidths=[CONTENT_WIDTH], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), .5, colors.HexColor('#d2ded4')),
            ('LEFTPADDING', (0, 0), (-1, -1), 11),
            ('RIGHTPADDING', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7)
        ]))
        table.spaceAfter = 9
        return [table]
    if kind in ('sumario', 'dataset', 'indicadores', 'totais'):
        headers, rows = table_data(kind, book, data, analysis)
        return [make_table(headers, rows, kind, styles)]
    if kind == 'grafico':
        image = Image(str(ROOT / block['arquivo']), width=CONTENT_WIDTH,
                      height=CONTENT_WIDTH * 2.5 / 6.8)
        image.spaceAfter = 4
        return [image, Paragraph('Fonte: carteira sintética do projeto. Valores observados.',
                                  styles['small'])]
    if kind == 'codigo':
        code = Preformatted(block['texto'], styles['code'])
        table = Table([[code]], colWidths=[CONTENT_WIDTH], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf0ee')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
        ]))
        table.spaceAfter = 11
        return [table]
    if kind == 'referencias':
        result = []
        for ref in book['referencias']:
            text = (f"[{ref['id']}] <link href={escape(ref['url'], quote=True)!r} "
                    f"color='#276c68'>{escape(ref['titulo'])}</link>. "
                    f"{escape(ref['nota'])}")
            result.append(Paragraph(text, styles['small']))
        return result
    raise ValueError(f'Tipo de bloco desconhecido: {kind}')


def export_markdown(book, data, analysis):
    text = f"# {book['titulo']}\n\n**{book['subtitulo']}**\n\n"
    text += f"Autoria: {book['autor']}. {book['edicao']}. Projeto educacional com apoio de IA.\n\n"
    fence = chr(96) * 3
    for section in book['secoes']:
        text += f"## {section['titulo']}\n\n"
        for block in section['blocos']:
            kind = block['tipo']
            if kind == 'p': text += block['texto'] + '\n\n'
            elif kind == 'h': text += '### ' + block['texto'] + '\n\n'
            elif kind == 'bullets': text += '\n'.join('- ' + x for x in block['itens']) + '\n\n'
            elif kind == 'callout': text += f"**{block['rotulo']}:** {block['texto']}\n\n"
            elif kind == 'formula': text += f"**{block['texto']}**\n\n{block['unidade']}.\n\n"
            elif kind in ('sumario', 'dataset', 'indicadores', 'totais'):
                headers, rows = table_data(kind, book, data, analysis)
                text += '| ' + ' | '.join(headers) + ' |\n'
                text += '| ' + ' | '.join('---' for _ in headers) + ' |\n'
                for row in rows: text += '| ' + ' | '.join(row) + ' |\n'
                text += '\n'
            elif kind == 'grafico':
                text += f"![Custo por exposição](../{block['arquivo']})\n\n"
            elif kind == 'codigo':
                text += fence + ('bash' if block.get('curto') else 'python') + '\n'
                text += block['texto'] + '\n' + fence + '\n\n'
            elif kind == 'referencias':
                for ref in book['referencias']:
                    text += f"[{ref['id']}] [{ref['titulo']}]({ref['url']}). {ref['nota']}\n\n"
    (ROOT / 'conteudo/ebook.md').write_text(text, encoding='utf-8')


def main():
    book = json.loads((ROOT / 'conteudo/ebook.json').read_text(encoding='utf-8'))
    data = json.loads((ROOT / 'dados/carteira_sintetica.json').read_text(encoding='utf-8'))
    analysis = analisar(data)
    output = ROOT / 'output'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'analise_resultados.json').write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    make_chart(analysis)
    export_markdown(book, data, analysis)
    styles = fonts_and_styles()
    target = output / 'Do_Dado_a_Decisao.pdf'
    doc = BaseDocTemplate(str(target), pagesize=(W, H),
                          title=book['titulo'], author=book['autor'])
    frame = Frame(MARGIN, 46, CONTENT_WIDTH, H - 104, leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0, id='main')
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[frame],
                     onPage=lambda c, d: cover_page(c, d, book)),
        PageTemplate(id='body', frames=[frame],
                     onPage=lambda c, d: body_page(c, d, book))
    ])
    story = [NextPageTemplate('body'), Spacer(1, 1), PageBreak()]
    for index, section in enumerate(book['secoes']):
        flowables = [Paragraph(escape(section['kicker']), styles['kicker']),
                     Paragraph(escape(section['titulo']), styles['title'])]
        for block in section['blocos']:
            flowables.extend(block_flowables(block, book, data, analysis, styles))
        story.append(KeepTogether(flowables))
        if index < len(book['secoes']) - 1:
            story.append(PageBreak())
    doc.build(story)
    print(json.dumps({'pdf': str(target), 'paginas_previstas': len(book['secoes']) + 1,
                       'tamanho_bytes': target.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
