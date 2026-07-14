"""Gera o deck executivo da Fase 2 em PowerPoint.

Uso (a partir desta pasta):
    uv run --with python-pptx python build_slides.py

Mantido versionado para que os slides sejam reproduziveis e faceis de ajustar.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

NAVY = RGBColor(0x1E, 0x27, 0x61)
ICE = RGBColor(0xCA, 0xDC, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MINT = RGBColor(0x00, 0xA8, 0x96)
DARK = RGBColor(0x2B, 0x2B, 0x2B)
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
LIGHTBG = RGBColor(0xF4, 0xF6, 0xFB)

OUT = "pipeline_alfabetizacao_fase2.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5


def slide(bg=WHITE):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(W), Inches(H))
    r.fill.solid()
    r.fill.fore_color.rgb = bg
    r.line.fill.background()
    r.shadow.inherit = False
    r._element.addprevious(r._element)  # mantem ao fundo
    return s


def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=None):
    """runs: lista de paragrafos; cada paragrafo: lista de (texto, size, bold, color, italic)."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if space is not None:
            p.space_after = Pt(space)
        for (txt, size, bold, color, *rest) in para:
            r = p.add_run()
            r.text = txt
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = "Calibri"
            if rest and rest[0]:
                r.font.italic = True
    return tb


def card(s, x, y, w, h, fill=LIGHTBG, line=None):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid()
    c.fill.fore_color.rgb = fill
    if line is None:
        c.line.fill.background()
    else:
        c.line.color.rgb = line
        c.line.width = Pt(1)
    c.shadow.inherit = False
    return c


def circle(s, x, y, d, fill, label, lsize=18, lcolor=WHITE):
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    c.fill.solid()
    c.fill.fore_color.rgb = fill
    c.line.fill.background()
    c.shadow.inherit = False
    tf = c.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(lsize)
    r.font.bold = True
    r.font.color.rgb = lcolor
    r.font.name = "Calibri"
    return c


def title(s, txt, color=NAVY, y=0.55):
    text(s, 0.7, y, 12.0, 1.0, [[(txt, 34, True, color)]])


# ----------------------------------------------------------------------------
# 1. Capa
s = slide(NAVY)
text(s, 0.9, 2.5, 11.5, 2.0, [
    [("Pipeline Hibrido de Alfabetizacao no Brasil", 44, True, WHITE)],
], anchor=MSO_ANCHOR.TOP)
text(s, 0.9, 4.1, 11.5, 1.5, [
    [("Integrando dados publicos para apoiar politicas de alfabetizacao", 20, False, ICE)],
    [("Tech Challenge Fase 2  |  MBA AI Scientist (FIAP / POSTECH)", 15, False, ICE)],
], space=8)
text(s, 0.9, 6.6, 11.5, 0.5, [[("Guilherme Cosme", 14, False, MINT)]])

# ----------------------------------------------------------------------------
# 2. O problema
s = slide(WHITE)
title(s, "O problema")
text(s, 0.7, 1.6, 6.7, 4.8, [
    [("A alfabetizacao ate o final do 2o ano e um marco do desenvolvimento educacional. O pais tem uma meta clara para acompanhar esse direito.", 17, False, DARK)],
    [("O Indicador Crianca Alfabetizada mede o percentual de criancas que atingem o nivel de leitura esperado. Sozinho, ele mostra onde estamos, mas nao explica o porque nem ajuda a agir.", 17, False, DARK)],
    [("Para isso, e preciso juntar fontes que hoje vivem separadas: metas, territorios e desempenho dos alunos.", 17, False, DARK)],
], space=14)
# stat callouts
card(s, 7.9, 1.7, 4.7, 2.0, LIGHTBG)
text(s, 8.1, 1.95, 4.3, 1.6, [
    [("743", 60, True, MINT)],
    [("pontos no Saeb: o corte que define uma crianca alfabetizada", 13, False, GRAY)],
], space=2)
card(s, 7.9, 4.0, 4.7, 2.0, LIGHTBG)
text(s, 8.1, 4.25, 4.3, 1.6, [
    [("2030", 60, True, NAVY)],
    [("meta para todas as criancas alfabetizadas ao fim do 2o ano", 13, False, GRAY)],
], space=2)

# ----------------------------------------------------------------------------
# 3. Dados fragmentados
s = slide(WHITE)
title(s, "O dado certo, hoje, esta espalhado")
fontes = [
    ("UF", "Unidades da federacao e regioes"),
    ("MUN", "Municipios e vinculo com a UF"),
    ("META", "Metas nacional, por UF e por municipio"),
    ("AL", "Desempenho dos alunos por rede"),
]
x0 = 0.7
for i, (sig, desc) in enumerate(fontes):
    x = x0 + i * 3.05
    card(s, x, 1.9, 2.8, 2.3, LIGHTBG)
    circle(s, x + 1.05, 2.15, 0.7, NAVY if i % 2 == 0 else MINT, sig, lsize=14)
    text(s, x + 0.2, 3.05, 2.4, 1.1, [[(desc, 13, False, DARK)]], align=PP_ALIGN.CENTER)
text(s, 0.7, 4.7, 11.9, 1.5, [
    [("Integradas, essas fontes deixam de ser numeros soltos e passam a responder onde concentrar esforco, onde estao as maiores desigualdades e o que esta melhorando ao longo do tempo.", 17, False, DARK)],
])

# ----------------------------------------------------------------------------
# 4. A solucao
s = slide(NAVY)
title(s, "A solucao", color=WHITE)
text(s, 0.7, 1.5, 11.9, 0.9, [[("Uma pipeline de dados que integra essas fontes de forma automatica, confiavel e barata, na nuvem.", 19, False, ICE)]])
pilares = [
    ("Hibrida", "Ingestao em lote e em tempo quase real"),
    ("Medalhao", "Camadas de bruto, tratado e analitico"),
    ("Serverless", "Paga pelo uso, sobe e destroi em minutos"),
    ("Governada", "Qualidade validada a cada rodada"),
]
for i, (t, d) in enumerate(pilares):
    x = 0.7 + i * 3.05
    card(s, x, 2.9, 2.8, 2.7, RGBColor(0x2A, 0x34, 0x75))
    circle(s, x + 1.15, 3.2, 0.5, MINT, str(i + 1), lsize=16)
    text(s, x + 0.25, 3.95, 2.3, 1.5, [
        [(t, 19, True, WHITE)],
        [(d, 13, False, ICE)],
    ], align=PP_ALIGN.CENTER, space=6)

# ----------------------------------------------------------------------------
# 5. Arquitetura
s = slide(WHITE)
title(s, "Arquitetura da solucao")
etapas = [
    ("Fontes", "Base dos Dados\ne eventos", ICE, NAVY),
    ("Bronze", "dado bruto", LIGHTBG, NAVY),
    ("Silver", "limpo e\nintegrado", LIGHTBG, NAVY),
    ("Gold", "analitico", MINT, WHITE),
    ("Consumo", "Athena, BI\ne ML", ICE, NAVY),
]
bw, gap = 2.15, 0.35
x = 0.7
for i, (t, d, fill, fg) in enumerate(etapas):
    card(s, x, 2.3, bw, 1.8, fill)
    text(s, x + 0.1, 2.5, bw - 0.2, 1.5, [
        [(t, 18, True, fg)],
        [(d.replace("\n", " "), 12, False, fg if fill == MINT else GRAY)],
    ], align=PP_ALIGN.CENTER, space=4)
    if i < len(etapas) - 1:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.02), Inches(2.95), Inches(gap - 0.04), Inches(0.5))
        ar.fill.solid(); ar.fill.fore_color.rgb = NAVY; ar.line.fill.background(); ar.shadow.inherit = False
    x += bw + gap
text(s, 0.7, 4.7, 11.9, 1.6, [
    [("Step Functions orquestra as etapas e o EventBridge dispara na agenda. Um gate de qualidade barra dado ruim antes da camada analitica, e o CloudWatch acompanha latencia, volume e falhas.", 16, False, DARK)],
])

# ----------------------------------------------------------------------------
# 6. Ingestao hibrida
s = slide(WHITE)
title(s, "Ingestao hibrida")
card(s, 0.7, 1.7, 5.85, 4.6, LIGHTBG)
circle(s, 1.0, 2.0, 0.6, NAVY, "B", lsize=18)
text(s, 1.8, 2.05, 4.6, 0.6, [[("Batch", 22, True, NAVY)]])
text(s, 1.0, 2.95, 5.3, 3.1, [
    [("Para dados estaveis, que mudam em lotes.", 15, True, DARK)],
    [("Metas, municipios e tabelas de referencia.", 14, False, GRAY)],
    [("Roda como job Glue agendado, gravando no bruto.", 14, False, GRAY)],
], space=12)
card(s, 6.8, 1.7, 5.85, 4.6, LIGHTBG)
circle(s, 7.1, 2.0, 0.6, MINT, "S", lsize=18)
text(s, 7.9, 2.05, 4.6, 0.6, [[("Streaming", 22, True, MINT)]])
text(s, 7.1, 2.95, 5.3, 3.1, [
    [("Para as novas medicoes de desempenho.", 15, True, DARK)],
    [("Chegam como eventos via Kinesis.", 14, False, GRAY)],
    [("Uma Lambda grava no bruto em tempo quase real.", 14, False, GRAY)],
], space=12)

# ----------------------------------------------------------------------------
# 7. Camadas medalhao
s = slide(WHITE)
title(s, "Camadas de dados")
camadas = [
    ("Bronze", "Dado bruto, como veio da fonte, com historico preservado.", RGBColor(0xB0,0x7A,0x3C)),
    ("Silver", "Limpo, padronizado e, o ponto central, integrado entre as fontes.", RGBColor(0x8A,0x90,0x9C)),
    ("Gold", "Indicador por municipio, metas vs resultado e evolucao no tempo.", MINT),
]
for i, (t, d, col) in enumerate(camadas):
    x = 0.7 + i * 4.05
    card(s, x, 1.9, 3.8, 3.8, LIGHTBG)
    circle(s, x + 0.3, 2.2, 0.55, col, str(i + 1), lsize=16)
    text(s, x + 0.3, 3.0, 3.2, 2.5, [
        [(t, 22, True, NAVY)],
        [(d, 15, False, DARK)],
    ], space=10)

# ----------------------------------------------------------------------------
# 8. Qualidade
s = slide(WHITE)
title(s, "Qualidade e confianca")
text(s, 0.7, 1.55, 7.0, 1.2, [[("Um gate automatico valida as camadas. Se algo critico falha, a pipeline para antes de um numero errado chegar a um relatorio.", 17, False, DARK)]])
checks = ["Duplicidade", "Valores ausentes", "Chaves de relacionamento", "Consistencia entre tabelas"]
for i, c in enumerate(checks):
    yy = 2.95 + i * 0.95
    circle(s, 0.7, yy, 0.55, MINT, "ok", lsize=12)
    text(s, 1.5, yy + 0.05, 6.0, 0.6, [[(c, 17, True, NAVY)]])
card(s, 8.2, 2.6, 4.4, 2.3, LIGHTBG)
text(s, 8.4, 2.9, 4.0, 1.8, [
    [("11", 60, True, MINT)],
    [("checagens executadas a cada rodada, validadas com a pipeline rodando de ponta a ponta", 13, False, GRAY)],
], space=2)

# ----------------------------------------------------------------------------
# 9. Monitoramento e FinOps
s = slide(WHITE)
title(s, "Monitoramento e custo")
card(s, 0.7, 1.7, 5.85, 4.6, LIGHTBG)
text(s, 1.0, 2.0, 5.3, 4.0, [
    [("Monitoramento", 20, True, NAVY)],
    [("Metricas de latencia, volume e falhas no CloudWatch.", 15, False, DARK)],
    [("Alarmes e alertas por SNS, com painel de acompanhamento.", 15, False, DARK)],
], space=12)
card(s, 6.8, 1.7, 5.85, 4.6, LIGHTBG)
text(s, 7.1, 2.0, 5.3, 4.0, [
    [("FinOps", 20, True, MINT)],
    [("Serverless de ponta a ponta: custo quase zero quando ocioso.", 15, False, DARK)],
    [("Parquet com particionamento e ciclo de vida no S3.", 15, False, DARK)],
    [("Ambiente efemero: sobe, processa e destroi.", 15, False, DARK)],
], space=11)

# ----------------------------------------------------------------------------
# 10. Valor e IA
s = slide(WHITE)
title(s, "Valor e potencial de IA")
itens = [
    ("Antecipar", "Prever quais municipios tendem a ficar abaixo da meta e agir antes do resultado consolidado."),
    ("Enxergar desigualdade", "Comparar regioes e redes e identificar grupos em maior vulnerabilidade educacional."),
    ("Decidir com dados", "Priorizar recurso onde ha maior distancia da meta e medir o efeito das acoes no tempo."),
]
for i, (t, d) in enumerate(itens):
    yy = 1.8 + i * 1.6
    circle(s, 0.7, yy, 0.7, NAVY if i != 2 else MINT, str(i + 1), lsize=18)
    text(s, 1.7, yy, 10.8, 1.4, [
        [(t, 19, True, NAVY)],
        [(d, 15, False, DARK)],
    ], space=4)

# ----------------------------------------------------------------------------
# 11. Fechamento
s = slide(NAVY)
text(s, 0.9, 2.6, 11.5, 2.5, [
    [("Dados publicos viram informacao acionavel", 34, True, WHITE)],
    [("Uma pipeline moderna, barata e confiavel, que transforma o indicador de alfabetizacao em apoio a politica publica e ja abre a porta para inteligencia artificial.", 18, False, ICE)],
], space=14)
text(s, 0.9, 6.4, 11.5, 0.6, [[("Obrigado", 20, True, MINT)]])

prs.save(OUT)
print(f"salvo em {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
