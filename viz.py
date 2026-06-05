"""Plotly-визуализации в фирменной зелёной гамме (вместо «голых» таблиц)."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

GREEN = "#1A9E4B"; GREEN_D = "#157a3a"
INK = "#13201a"; INK2 = "#5a6b62"; INK3 = "#8a988f"; LINE = "#e4ebe6"
TL_G = "#3bb564"; TL_Y = "#f2c12e"; TL_O = "#ec7a3c"; TL_R = "#e0463a"
FONT = "Manrope, system-ui, sans-serif"
MONO = "JetBrains Mono, monospace"
HEAT_SCALE = [[0, "#3bb564"], [0.16, "#bfe3a0"], [0.34, "#f2d65a"],
              [0.55, "#f3b06b"], [0.78, "#ec7a3c"], [1.0, "#d83a2e"]]


def sev(v):
    if v is None:
        return "#eef1ef"
    if v >= 6:
        return TL_R
    if v >= 3:
        return TL_O
    if v >= 1:
        return TL_Y
    return TL_G


def _base(fig, h=260, legend=False, top=10):
    fig.update_layout(
        height=h, margin=dict(l=10, r=14, t=top, b=10),
        paper_bgcolor="#ffffff", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=13),
        showlegend=legend,
        legend=dict(orientation="h", y=1.14, x=0, font=dict(size=12)),
    )
    return fig


def gauge(score, vmax=180):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"font": {"size": 46, "color": INK, "family": MONO}},
        gauge={
            "axis": {"range": [0, vmax], "tickvals": [0, 60, 120, 180],
                     "tickcolor": LINE, "tickfont": {"size": 10, "color": INK3}},
            "bar": {"color": "rgba(0,0,0,0)"},
            "borderwidth": 0,
            "steps": [
                {"range": [0, 60], "color": TL_G},
                {"range": [60, 120], "color": TL_Y},
                {"range": [120, 180], "color": TL_O},
            ],
            "threshold": {"line": {"color": INK, "width": 6}, "thickness": 0.82, "value": score},
        }))
    return _base(fig, h=230)


def dynamics(dates, ranks):
    """Стек-бары по зонам (зелёная/жёлтая/красная) + линия позиции с подписями."""
    green = [r for r in ranks]
    yellow = [max(0, 90 - r) for r in ranks]
    orange = [80 for _ in ranks]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=green, name="Зелёная зона", marker_color="#9bc53d", width=0.55,
                         hovertemplate="%{x}<br>зелёная: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(x=dates, y=yellow, name="Жёлтая зона", marker_color="#f2d65a", width=0.55,
                         hoverinfo="skip"))
    fig.add_trace(go.Bar(x=dates, y=orange, name="Красная зона", marker_color="#ef9d6b", width=0.55,
                         hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=dates, y=ranks, mode="lines+markers+text", name="Позиция",
        text=[str(r) for r in ranks], textposition="top center",
        textfont=dict(family=MONO, size=13, color=INK),
        line=dict(color="#2b5d8a", width=2.5),
        marker=dict(size=9, color="#2b5d8a", line=dict(color="white", width=1.5)),
        hovertemplate="%{x}: место %{y}<extra></extra>"))
    fig.update_layout(barmode="stack", bargap=0.35)
    fig.update_yaxes(range=[0, 185], visible=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(family=MONO, size=11, color=INK2))
    return _base(fig, h=330, legend=True)


def top3_dynamics():
    """Мультилайн «Динамика оценки ТОП-3» (как на скрине эталона)."""
    dates = ["29.05", "04.06", "12.06", "18.06"]
    series = [
        ("Доля операций с БМО", "#2b8fd6", [9.0, 8.8, 8.6, 9.8]),
        ("Длительные вакансии", "#e0463a", [2.6, 2.5, 3.4, 1.9]),
        ("Нарушения ИС СТАТУС", "#6b7a72", [1.9, 1.9, 1.9, 1.8]),
        ("Непроизводит. время", "#ec9a3c", [0.6, 2.5, 0.3, 0.4]),
    ]
    fig = go.Figure()
    for name, c, d in series:
        fig.add_trace(go.Scatter(x=dates, y=d, mode="lines+markers", name=name,
                                 line=dict(color=c, width=2.6), marker=dict(size=7, color=c),
                                 hovertemplate=name + ": %{y}<extra></extra>"))
    fig.update_yaxes(range=[0, 11], showgrid=True, gridcolor=LINE, zeroline=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(family=MONO, size=11, color=INK2))
    return _base(fig, h=330, legend=True)


def hbar(names, values, colors=None, fmt="{:.1f}", suffix="", xtitle=None, height=None):
    colors = colors or [sev(v) for v in values]
    height = height or max(150, 46 + 30 * len(names))
    fig = go.Figure(go.Bar(
        x=values, y=names, orientation="h", marker_color=colors,
        text=[fmt.format(v) + suffix for v in values], textposition="outside",
        textfont=dict(family=MONO, size=12), cliponaxis=False))
    fig.update_yaxes(autorange="reversed", automargin=True, tickfont=dict(size=12))
    fig.update_xaxes(showgrid=True, gridcolor=LINE, zeroline=False,
                     title=xtitle, title_font=dict(size=11, color=INK3))
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")
    return _base(fig, h=height)


def comparison(names, mine, bank):
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=mine, orientation="h", name="Моя",
                         marker_color=TL_O, text=[f"{v:.2f}" for v in mine],
                         textposition="outside", cliponaxis=False))
    fig.add_trace(go.Bar(y=names, x=bank, orientation="h", name="По Банку",
                         marker_color="#9bbcab", text=[f"{v:.2f}" for v in bank],
                         textposition="outside", cliponaxis=False))
    fig.update_yaxes(autorange="reversed", automargin=True)
    fig.update_xaxes(showgrid=True, gridcolor=LINE, zeroline=False)
    fig.update_layout(barmode="group")
    return _base(fig, h=max(200, 60 + 52 * len(names)), legend=True)


def zones_donut(g, y, r):
    fig = go.Figure(go.Pie(
        labels=["Зелёная", "Жёлтая", "Красная"], values=[g, y, r], hole=0.62,
        marker_colors=[TL_G, TL_Y, TL_R], sort=False,
        textinfo="value", textfont=dict(family=MONO, size=15, color="white")))
    return _base(fig, h=250, legend=True)


def branches_distribution(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df.branch, x=df.g, orientation="h", name="Зелёная", marker_color=TL_G))
    fig.add_trace(go.Bar(y=df.branch, x=df.y, orientation="h", name="Жёлтая", marker_color=TL_Y))
    fig.add_trace(go.Bar(y=df.branch, x=df.r, orientation="h", name="Красная", marker_color=TL_R))
    fig.update_yaxes(autorange="reversed", automargin=True)
    fig.update_xaxes(showgrid=True, gridcolor=LINE, zeroline=False, title="доп. офисов",
                     title_font=dict(size=11, color=INK3))
    fig.update_layout(barmode="stack")
    return _base(fig, h=max(230, 60 + 42 * len(df)), legend=True)


def heatmap(cols, rows):
    x = [lab for (_, lab) in cols]
    y = [r["name"] for r in rows]
    z = [[(v if v is not None else None) for v in r["cells"]] for r in rows]
    text = [[(f"{v:.1f}" if v is not None else "") for v in r["cells"]] for r in rows]
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y, text=text, texttemplate="%{text}",
        textfont=dict(family=MONO, size=11, color="white"),
        colorscale=HEAT_SCALE, zmin=0, zmax=8, showscale=False, xgap=3, ygap=3,
        hovertemplate="%{y}<br>%{x}: %{z}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", automargin=True, tickfont=dict(size=11))
    fig.update_xaxes(side="top", tickfont=dict(family=MONO, size=11), fixedrange=True)
    fig.update_layout(plot_bgcolor="#eef1ef")
    return _base(fig, h=max(300, 70 + 33 * len(rows)), top=24)


def freq_bar(rows, total):
    names = [r["name"] for r in rows]
    freqs = [r["freq"] for r in rows]
    vals = [(f / total * 100 if total else 0) for f in freqs]
    colors = [TL_R if f >= total * 0.6 else TL_O for f in freqs]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker_color=colors,
        text=[f"{f}/{total}" for f in freqs], textposition="outside",
        textfont=dict(family=MONO, size=12), cliponaxis=False))
    fig.update_xaxes(range=[0, 105], showgrid=True, gridcolor=LINE, zeroline=False,
                     title="% недель в ТОП-3", title_font=dict(size=11, color=INK3))
    fig.update_yaxes(autorange="reversed", automargin=True, tickfont=dict(size=12))
    return _base(fig, h=max(200, 50 + 40 * len(names)))


def top_periods(byW, byM, byQ, topN):
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.22,
                        subplot_titles=("Неделя (среднее)", "Месяц", "Квартал"))
    for c, data in enumerate([byW, byM, byQ], start=1):
        names = [d[0] for d in data]
        vals = [d[1] for d in data]
        fig.add_trace(go.Bar(
            x=vals, y=names, orientation="h",
            marker_color=[sev(v) for v in vals],
            text=[f"{v:.2f}" for v in vals], textposition="outside",
            textfont=dict(family=MONO, size=11), cliponaxis=False), row=1, col=c)
    fig.update_yaxes(autorange="reversed", automargin=True, tickfont=dict(size=10))
    fig.update_xaxes(showgrid=True, gridcolor=LINE, zeroline=False)
    for ann in fig.layout.annotations:
        ann.font = dict(family=FONT, size=12, color=GREEN_D)
    return _base(fig, h=max(250, 90 + 48 * topN), top=34)


def office_scores(df):
    """Горизонтальные бары оценок доп. офисов филиала, цвет по светофору."""
    cmap = {"g": TL_G, "y": TL_Y, "r": TL_R}
    names = [f"{r.rank}. {r.vsp}" for r in df.itertuples()]
    vals = [r.score for r in df.itertuples()]
    colors = [cmap[r.light] for r in df.itertuples()]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=colors,
                           text=[str(v) for v in vals], textposition="outside",
                           textfont=dict(family=MONO, size=11), cliponaxis=False))
    fig.update_yaxes(autorange="reversed", automargin=True, tickfont=dict(size=11))
    fig.update_xaxes(showgrid=True, gridcolor=LINE, zeroline=False, title="оценка",
                     title_font=dict(size=11, color=INK3))
    return _base(fig, h=max(220, 50 + 34 * len(df)))
