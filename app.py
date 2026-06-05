"""
Дашборд мониторинга качества работы руководителей ВСП — концепция D.
Запуск:  streamlit run app.py

Структура повторяет согласованный прототип:
  • тёмный сайдбар с фильтрами (Период статистики для «Обзора» + организация);
  • три уровня: Банк / Филиал / Доп. офис (переключатель + проваливание по кнопкам);
  • внутри Филиала и Доп. офиса под-вкладки: Обзор / Детализация по отклонениям / Ассистент;
  • визуализации на Plotly (спидометр, динамика по зонам, карта-хитмап, бары), не таблицы.
"""
import os
from datetime import date

import streamlit as st

import mock_data as M
import viz as V

st.set_page_config(page_title="Мониторинг качества руководителей ВСП",
                   layout="wide", initial_sidebar_state="expanded")

GREEN = "#1A9E4B"; TL_G = "#3bb564"; TL_Y = "#f2c12e"; TL_R = "#e0463a"
PLOT_CFG = {"displayModeBar": False, "responsive": True}

# --------------------------------- стиль ---------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
html, body, [class*="css"] { font-family:'Manrope',system-ui,sans-serif; }
.stApp { background:#f3f6f4; }
.block-container { padding-top:1rem; padding-bottom:2rem; padding-left:1.6rem !important;
   padding-right:1.6rem !important; max-width:1620px; }

/* ---- сайдбар тёмный ---- */
[data-testid="stSidebar"] { background:#0f1a14; }
[data-testid="stSidebar"] * { color:#dce8e1; }
[data-testid="stSidebar"] .side-title { font-weight:800; font-size:15px; color:#fff; margin-bottom:6px; }
[data-testid="stSidebar"] .side-h { color:#8fb3a0; font-size:11px; text-transform:uppercase;
   letter-spacing:1px; font-weight:700; margin:18px 0 6px; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] input { background:#1a2a21 !important; border-color:#2c3d33 !important; color:#eaf2ec !important; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:#9fb8aa; font-weight:600; font-size:12px; }

/* ---- заголовки уровней ---- */
.h1 { font-size:22px; font-weight:800; letter-spacing:-.4px; margin:2px 0 2px; color:#13201a; }
.h-sub { font-size:13px; color:#5a6b62; margin-bottom:10px; }

/* ---- KPI карточки ---- */
.kpi { background:#fff; border:1px solid #e4ebe6; border-radius:14px; padding:11px 16px 12px;
   box-shadow:0 1px 2px rgba(20,40,30,.05),0 6px 22px rgba(20,40,30,.05); }
.kpi .lab { font-size:12px; color:#5a6b62; font-weight:600; line-height:1.2; min-height:30px; }
.kpi .val { font-size:30px; font-weight:800; letter-spacing:-.5px; margin-top:0;
   font-variant-numeric:tabular-nums; font-family:'JetBrains Mono',monospace; }
.kpi .trend { font-size:12px; margin-top:1px; font-weight:700; color:#8a988f; }

/* ---- заголовок карточки ---- */
.card-h { font-weight:800; font-size:14.5px; display:flex; align-items:center; gap:8px; margin-bottom:2px; }
.card-h .sub { font-weight:500; color:#8a988f; font-size:12px; margin-left:auto; }

/* ---- зелёный баннер ---- */
.banner { background:linear-gradient(135deg,#1A9E4B,#157a3a); color:#fff; font-weight:800;
   font-size:15px; padding:14px 18px; border-radius:12px; box-shadow:0 4px 16px rgba(26,158,75,.22);
   margin:6px 0 4px; }

/* ---- блок «Место в рейтинге» (зелёная плашка) ---- */
.rankcard { background:linear-gradient(135deg,#1A9E4B,#157a3a); color:#fff; border-radius:14px;
   padding:18px 22px; height:100%; }
.rankcard .t { font-weight:700; font-size:13px; opacity:.92; }
.rankcard .big { font-size:62px; font-weight:800; line-height:1; letter-spacing:-2px;
   font-family:'JetBrains Mono',monospace; }
.rankcard .of { font-size:17px; opacity:.85; font-weight:600; }
.rankcard .mv { margin-top:10px; font-weight:800; font-size:14px; background:rgba(255,255,255,.16);
   display:inline-block; padding:4px 11px; border-radius:20px; }
.glabel { text-align:center; font-size:12.5px; font-weight:800; text-transform:uppercase;
   letter-spacing:.5px; color:#5a6b62; margin-bottom:-6px; }

/* ---- подсказка-календарь ---- */
.cal-hint { background:#eef6f0; border:1px solid #d3e7da; border-left:4px solid #1A9E4B;
   border-radius:10px; padding:11px 14px; font-size:13px; color:#5a6b62; line-height:1.45; }
.cal-hint b { color:#157a3a; }

/* ---- чипы светофора ---- */
.chip { display:inline-flex; align-items:center; gap:5px; font-size:12px; font-weight:700;
   padding:4px 11px; border-radius:20px; }
.chip .led { width:8px; height:8px; border-radius:50%; }
.chip.g { background:#e6f6ec; color:#1c7d41; } .chip.g .led { background:#3bb564; }

/* ---- вкладки ---- */
.stTabs [data-baseweb="tab-list"] { gap:28px; }
.stTabs [data-baseweb="tab"] { font-weight:700; padding-left:4px; padding-right:4px; }
.stTabs [aria-selected="true"] { color:#157a3a; }

/* демо-плашка ассистента */
.demo { font-size:12px; color:#8a6d1f; background:#fff7e3; border:1px solid #f0e2b4;
   border-radius:9px; padding:8px 12px; }

/* ---- убираем служебный тулбар Streamlit (deploy/share), но НЕ ломаем шапку ---- */
header[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stDecoration"] { display:none !important; }
#MainMenu, footer { visibility:hidden; }

/* ---- сайдбар: гарантированно тёмный фон ---- */
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div { background:#0f1a14 !important; }
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] { background:#0c1812; border:1px solid #2c3d33;
   border-radius:10px; padding:4px; }
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] button p { color:#bcd2c6; }

/* ====== Рейтинг филиалов (HTML) ====== */
.rank-table { font-size:13px; }
.rt-head, .rt-row { display:grid; grid-template-columns:42px 2.3fr .8fr .55fr 2fr .9fr;
   align-items:center; gap:8px; padding:11px 10px; }
.rt-head { color:#8a988f; font-size:11px; text-transform:uppercase; letter-spacing:.4px;
   font-weight:700; border-bottom:1px solid #e4ebe6; }
.rt-row { border-bottom:1px solid #eef2ef; }
.rt-row:last-child { border-bottom:none; }
.rt-row.hl { background:#eef8f1; border-radius:12px; }
.rt-rank { display:grid; place-items:center; width:30px; height:30px; border-radius:9px;
   background:#e8f6ee; color:#157a3a; font-weight:800; font-family:'JetBrains Mono',monospace; }
.rt-name { font-weight:700; color:#13201a; line-height:1.2; }
.rt-name small { display:block; color:#8a988f; font-weight:500; font-size:12px; margin-top:2px; }
.rt-num { font-family:'JetBrains Mono',monospace; font-weight:700; text-align:right; }
.rt-dist { display:flex; gap:6px; flex-wrap:wrap; }
.cnt { display:inline-flex; align-items:center; gap:4px; font-family:'JetBrains Mono',monospace;
   font-weight:700; font-size:12px; padding:3px 9px; border-radius:20px; }
.cnt .led { width:8px; height:8px; border-radius:50%; }
.cnt.g { background:#e6f6ec; color:#1c7d41; } .cnt.g .led { background:#3bb564; }
.cnt.y { background:#fdf6e0; color:#9a7708; } .cnt.y .led { background:#f2c12e; }
.cnt.r { background:#fdeae8; color:#b32d23; } .cnt.r .led { background:#e0463a; }
.rt-delta { font-family:'JetBrains Mono',monospace; font-weight:700; text-align:right; }
.rt-delta.up { color:#e0463a; } .rt-delta.down { color:#3bb564; } .rt-delta.zero { color:#8a988f; }

/* ====== Топ отклонений (HTML) ====== */
.dev-table { font-size:13px; }
.dv-head, .dv-row { display:grid; grid-template-columns:2.6fr .5fr 2.1fr .7fr .55fr;
   align-items:center; gap:10px; padding:12px 10px; }
.dv-head { color:#8a988f; font-size:11px; text-transform:uppercase; letter-spacing:.4px;
   font-weight:700; border-bottom:1px solid #e4ebe6; }
.dv-row { border-bottom:1px solid #eef2ef; }
.dv-row:last-child { border-bottom:none; }
.dv-name { font-weight:600; color:#13201a; line-height:1.25; }
.dv-prev { display:flex; align-items:center; gap:10px; }
.dv-bar { flex:1; height:8px; border-radius:6px; background:#e4ebe6; overflow:hidden; min-width:50px; }
.dv-bar i { display:block; height:100%; border-radius:6px; }
.dv-num { font-family:'JetBrains Mono',monospace; font-weight:700; text-align:right; }

/* ---- бренд-строка ---- */
.brandbar { font-weight:800; font-size:17px; color:#13201a; line-height:1.3; margin:2px 0 6px; }

/* ---- карточка с гарантированно белым фоном (HTML) ---- */
.card { background:#ffffff; border:1px solid #e4ebe6; border-radius:16px; padding:6px 18px 12px;
   box-shadow:0 1px 2px rgba(20,40,30,.05),0 6px 22px rgba(20,40,30,.05);
   height:100%; box-sizing:border-box; }
.card .card-h { margin:8px 0 4px; }

/* ---- белый фон у карточек (bordered containers) ---- */
div[data-testid="stVerticalBlockBorderWrapper"] { background:#ffffff !important; border:1px solid #e4ebe6 !important;
   border-radius:16px; box-shadow:0 1px 2px rgba(20,40,30,.05),0 6px 22px rgba(20,40,30,.05);
   height:100%; box-sizing:border-box; }
div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
   background:#ffffff !important; border-radius:15px; }

/* ====== таблицы множителей / сравнения (HTML) ====== */
.mtab { font-size:13px; }
.mtab .mh, .mtab .mr { display:grid; align-items:center; gap:10px; padding:12px 4px; }
.mtab .mh { color:#8a988f; font-size:11px; text-transform:uppercase; letter-spacing:.4px;
   font-weight:700; border-bottom:1px solid #e4ebe6; }
.mtab .mr { border-bottom:1px solid #eef2ef; }
.mtab .mr:last-child { border-bottom:none; }
.mtab .nm { font-weight:600; color:#13201a; line-height:1.25; }
.mtab .nu { font-family:'JetBrains Mono',monospace; font-weight:700; text-align:right; }
.mtab .pill { display:inline-block; font-family:'JetBrains Mono',monospace; font-weight:700;
   padding:3px 9px; border-radius:7px; }
.mtab .pill.o { background:#fdeee2; color:#b95418; }
.mtab .up { color:#e0463a; } .mtab .down { color:#3bb564; } .mtab .zero { color:#8a988f; }

/* ---- сегментные переключатели: активный = зелёный, неактивный = светлый (верх) ---- */
button[kind="segmented_control"], button[data-testid="stBaseButton-segmented_control"] {
   background:#eef3f0 !important; color:#5a6b62 !important; border:1px solid #e4ebe6 !important;
   font-weight:700 !important; }
button[kind="segmented_controlActive"], button[data-testid="stBaseButton-segmented_controlActive"] {
   background:#1A9E4B !important; color:#ffffff !important; border:1px solid #1A9E4B !important;
   font-weight:800 !important; }
[data-testid="stButtonGroup"] button { padding:10px 22px !important; min-height:42px; }

/* ---- в сайдбаре неактивные кнопки периода — тёмные, активная — зелёная ---- */
section[data-testid="stSidebar"] button[kind="segmented_control"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-segmented_control"] {
   background:#1a2a21 !important; color:#bcd2c6 !important; border:1px solid #2c3d33 !important; }
section[data-testid="stSidebar"] button[kind="segmented_controlActive"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-segmented_controlActive"] {
   background:#1A9E4B !important; color:#ffffff !important; border:1px solid #1A9E4B !important; }

/* ---- равная высота блоков в одной строке ---- */
[data-testid="stHorizontalBlock"] { align-items: stretch; }
[data-testid="stHorizontalBlock"] > [data-testid="column"] { display: flex; flex-direction: column; }
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div { flex: 1; display: flex; flex-direction: column; }
</style>""", unsafe_allow_html=True)

# ------------------------------ состояние ------------------------------
ss = st.session_state
ss.setdefault("level", "Банк")
ss.setdefault("branch", M.BRANCHES[0])
ss.setdefault("office", None)


def seg(label, options, key, default=None):
    """Сегментный переключатель (с откатом на radio для старых версий Streamlit)."""
    default = default or options[0]
    if hasattr(st, "segmented_control"):
        kwargs = {} if key in st.session_state else {"default": default}
        val = st.segmented_control(label, options, key=key, label_visibility="collapsed", **kwargs)
        return val or ss.get(key, default)
    return st.radio(label, options, horizontal=True, key=key, label_visibility="collapsed")


def chip_g(text="Зелёная зона"):
    return f'<span class="chip g"><span class="led"></span>{text}</span>'


# ------------------------------- сайдбар -------------------------------
with st.sidebar:
    st.markdown('<div class="side-title">Фильтры выборки</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-h">Выберите период статистики</div>', unsafe_allow_html=True)
    ptype = seg("Тип периода", ["Неделя", "Месяц", "Квартал"], key="ptype")
    if ptype == "Неделя":
        wk = st.selectbox("Неделя отчёта", M.WEEKS, index=M.WEEKS.index(24),
                          format_func=lambda w: f"Неделя {w} · {M.week_label(w)}")
        ss["sel_week"] = wk
        period_label = f"неделя {wk} ({M.week_label(wk)}.{M.YEAR}) · недельные показатели"
    elif ptype == "Месяц":
        mo = st.selectbox("Месяц", ["Апрель", "Май", "Июнь", "Июль"], index=1)
        period_label = f"{mo} {M.YEAR} · месячные показатели (без недельных)"
    else:
        q = st.selectbox("Квартал", ["1 кв.", "2 кв.", "3 кв.", "4 кв."], index=1)
        period_label = f"{q} {M.YEAR} · квартальные показатели (без недельных и месячных)"
    st.selectbox("Год", ["2026", "2025", "2024"], index=0, key="year")

    st.markdown('<div class="side-h">Организация</div>', unsafe_allow_html=True)
    st.selectbox("Рег. директор", ["Все"] + M.DIRECTORS, key="f_dir")
    st.selectbox("Региональный филиал", ["Все"] + M.BRANCHES, key="f_fil")
    st.selectbox("Рег. менеджер", ["Все"] + M.MGRS, key="f_mgr")
    st.text_input("Поиск по ВСП / коду", placeholder="например, 8842", key="f_search")

    st.markdown('<div class="side-h">Дополнительно</div>', unsafe_allow_html=True)
    st.selectbox("Пилотная группа", ["Все", "Пилот", "Не пилот"], key="f_pilot")
    st.selectbox("Вес отклонения", ["Все", "≥10", "5–9", "1–4"], key="f_weight")
    st.button("Применить", type="primary", width="stretch")


# ------------------------------- helpers UI -------------------------------
def kpi(col, lab, val, trend="", light=""):
    bar = {"g": TL_G, "y": TL_Y, "r": TL_R}.get(light, GREEN)
    col.markdown(
        f'<div class="kpi" style="border-left:4px solid {bar}">'
        f'<div class="lab">{lab}</div><div class="val">{val}</div>'
        f'<div class="trend">{trend}</div></div>', unsafe_allow_html=True)


def card_header(container, title, sub=""):
    container.markdown(f'<div class="card-h">{title}<span class="sub">{sub}</span></div>',
                       unsafe_allow_html=True)


def chart_card(title, fig, sub=""):
    with st.container(border=True):
        card_header(st, title, sub)
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG)


# ------------------------------- уровень БАНК -------------------------------
def _delta_html(d):
    if d == 0:
        return '<div class="rt-delta zero">0</div>'
    if d < 0:   # поднялся в рейтинге — хорошо
        return f'<div class="rt-delta down">▲ {abs(d)}</div>'
    return f'<div class="rt-delta up">▼ {d}</div>'


def html_rank_table(brs):
    head = ('<div class="rt-head"><div>#</div><div>Филиал</div><div class="rt-num">Оценка</div>'
            '<div class="rt-num">ВСП</div><div>Распределение по офисам</div>'
            '<div class="rt-num">Δ&nbsp;позиций</div></div>')
    rows = []
    for i, r in brs.reset_index(drop=True).iterrows():
        hl = " hl" if i == 0 else ""
        dist = (f'<div class="rt-dist">'
                f'<span class="cnt g"><span class="led"></span>{int(r["g"])}</span>'
                f'<span class="cnt y"><span class="led"></span>{int(r["y"])}</span>'
                f'<span class="cnt r"><span class="led"></span>{int(r["r"])}</span></div>')
        rows.append(
            f'<div class="rt-row{hl}">'
            f'<div class="rt-rank">{int(r["rank"])}</div>'
            f'<div class="rt-name">{r["branch"]}<small>{r["director"]}</small></div>'
            f'<div class="rt-num">{int(r["score"])}</div>'
            f'<div class="rt-num">{int(r["offices"])}</div>'
            f'{dist}{_delta_html(int(r["delta"]))}</div>')
    return f'<div class="rank-table">{head}{"".join(rows)}</div>'


def html_dev_list(td):
    head = ('<div class="dv-head"><div>Отклонение</div><div class="dv-num">Вес</div>'
            '<div>Пораженность</div><div class="dv-num">Оценка</div><div class="dv-num">Срок</div></div>')
    rows = []
    for _, d in td.iterrows():
        p = float(d["prevalence"])
        color = "#e0463a" if p > 30 else ("#ec7a3c" if p > 10 else "#1A9E4B")
        w = min(100, p * 1.6 + 8)
        rows.append(
            f'<div class="dv-row">'
            f'<div class="dv-name">{d["name"]}</div>'
            f'<div class="dv-num">{int(d["weight"])}</div>'
            f'<div class="dv-prev"><div class="dv-bar"><i style="width:{w:.0f}%;background:{color}"></i></div>'
            f'<b class="dv-num">{p:.1f}%</b></div>'
            f'<div class="dv-num">{float(d["score"]):.2f}</div>'
            f'<div class="dv-num">{float(d["life"]):.1f}</div></div>')
    return f'<div class="dev-table">{head}{"".join(rows)}</div>'


def _bank_drill():
    v = ss.get("bank_drill")
    if v and v != "— выберите филиал —":
        ss.level = "Филиал"; ss.branch = v; ss.office = None
        ss.bank_drill = "— выберите филиал —"


def view_bank():
    bs = M.bank_summary()
    brs = M.branches_summary()
    st.markdown('<div class="h1">Сводка по Банку</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="h-sub">Агрегированные показатели качества · {bs["offices"]} офисов · '
                f'{bs["obj_mon"]} объектов в мониторинге</div>', unsafe_allow_html=True)

    c = st.columns(4)
    kpi(c[0], "Средняя интегральная оценка", str(bs["avg"]).replace(".", ","), "▲ 2,4 к прошлой неделе")
    kpi(c[1], "Офисов в зелёной зоне", f'{bs["g"]} <span style="font-size:18px;color:#8a988f">/ {bs["offices"]}</span>',
        f'{round(bs["g"]/bs["offices"]*100)}% сети', "g")
    kpi(c[2], "Офисов в жёлтой зоне", bs["y"], "требуют внимания", "y")
    kpi(c[3], "Офисов в красной зоне", bs["r"], "▼ 3 офиса за период", "r")

    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.12, 1])
    with left:
        st.markdown(
            '<div class="card"><div class="card-h">Рейтинг филиалов'
            '<span class="sub">выберите филиал ниже, чтобы провалиться</span></div>'
            + html_rank_table(brs) + '</div>', unsafe_allow_html=True)
        st.selectbox("Провалиться в филиал", ["— выберите филиал —"] + list(brs.branch),
                     key="bank_drill", on_change=_bank_drill, label_visibility="collapsed")
    with right:
        st.markdown(
            '<div class="card"><div class="card-h">Топ отклонений по Банку'
            '<span class="sub">средняя пораженность, %</span></div>'
            + html_dev_list(M.bank_top_deviations()) + '</div>', unsafe_allow_html=True)


# ------------------------- общий блок: ТОП-3 офиса -------------------------
def _delta_cell(d):
    if d > 0:
        return f'<div class="nu up">▲ +{d}</div>'
    if d < 0:
        return f'<div class="nu down">▼ {d}</div>'
    return '<div class="nu zero">0</div>'


def _dyn_cell(v, good_negative=True):
    """Цветная ячейка динамики: good_negative=True → отрицательное зелёное."""
    cls = ("down" if v < 0 else "up") if good_negative else ("up" if v < 0 else "down")
    sign = f"{v:+.2f}".rstrip("0").rstrip(".") if v else "0"
    return f'<div class="nu {cls}">{sign}</div>'


def html_score_table(rows):
    gt = "grid-template-columns:2.5fr .7fr .8fr"
    h = f'<div class="mh" style="{gt}"><div>Отклонение</div><div class="nu">Балл</div><div class="nu">Динамика</div></div>'
    body = "".join(
        f'<div class="mr" style="{gt}"><div class="nm">{r["name"]}</div>'
        f'<div class="nu">{r["score"]:.2f}</div>{_delta_cell(r["delta"])}</div>' for r in rows)
    return f'<div class="mtab">{h}{body}</div>'


def html_compare_table(rows):
    gt = "grid-template-columns:2.2fr .7fr .7fr .7fr"
    h = (f'<div class="mh" style="{gt}"><div>Отклонение</div><div class="nu">Моя</div>'
         f'<div class="nu">По Банку</div><div class="nu">Разница</div></div>')
    body = "".join(
        f'<div class="mr" style="{gt}"><div class="nm">{r["name"]}</div>'
        f'<div class="nu"><span class="pill o">{r["score"]:.2f}</span></div>'
        f'<div class="nu">{r["bank"]:.2f}</div>'
        f'<div class="nu up">{r["diff"]:.2f}</div></div>' for r in rows)
    return f'<div class="mtab">{h}{body}</div>'


def html_weight_table(rows):
    gt = "grid-template-columns:2.7fr .5fr"
    h = f'<div class="mh" style="{gt}"><div>Отклонение</div><div class="nu">Вес</div></div>'
    body = "".join(
        f'<div class="mr" style="{gt}"><div class="nm">{r["name"]}</div>'
        f'<div class="nu">{r["weight"]}</div></div>' for r in rows)
    return f'<div class="mtab">{h}{body}</div>'


def html_life_table(rows):
    gt = "grid-template-columns:2.2fr .7fr .8fr .7fr"
    h = (f'<div class="mh" style="{gt}"><div>Отклонение</div><div class="nu">Моя</div>'
         f'<div class="nu">Динамика</div><div class="nu">По Банку</div></div>')
    body = "".join(
        f'<div class="mr" style="{gt}"><div class="nm">{r["name"]}</div>'
        f'<div class="nu">{r["life"]:.2f}</div>'
        f'<div class="nu down">{r["life_dyn"]:.2f}</div>'
        f'<div class="nu">{r["life_bank"]:.2f}</div></div>' for r in rows)
    return f'<div class="mtab">{h}{body}</div>'


def html_prev_table(rows):
    gt = "grid-template-columns:2.2fr .7fr .8fr .7fr"
    h = (f'<div class="mh" style="{gt}"><div>Отклонение</div><div class="nu">Моя</div>'
         f'<div class="nu">Динамика</div><div class="nu">По Банку</div></div>')
    body = "".join(
        f'<div class="mr" style="{gt}"><div class="nm">{r["name"]}</div>'
        f'<div class="nu"><span class="pill o">{r["prevalence"]:.2f}</span></div>'
        f'{_dyn_cell(r["prevalence_dyn"])}'
        f'<div class="nu">{r["prevalence_bank"]:.2f}</div></div>' for r in rows)
    return f'<div class="mtab">{h}{body}</div>'


def html_prev_simple_table(rows):
    gt = "grid-template-columns:2.2fr .7fr .8fr"
    h = (f'<div class="mh" style="{gt}"><div>Отклонение</div>'
         f'<div class="nu">Моя</div><div class="nu">Динамика</div></div>')
    body = "".join(
        f'<div class="mr" style="{gt}"><div class="nm">{r["name"]}</div>'
        f'<div class="nu"><span class="pill o">{r["prevalence"]:.2f}%</span></div>'
        f'{_dyn_cell(r["prevalence_dyn"])}</div>' for r in rows)
    return f'<div class="mtab">{h}{body}</div>'


def _card_html(title, inner):
    return f'<div class="card"><div class="card-h">{title}</div>{inner}</div>'


def office_top3_block():
    rows = M.office_top3()
    st.markdown('<div class="banner">ТОП-3 отклонения, требующих первоочередного внимания</div>',
                unsafe_allow_html=True)
    # Ряд 1: Оценка | По сравнению с Банком — flex для гарантированной равной высоты
    st.markdown(
        '<div style="display:flex;gap:1rem;align-items:stretch;">'
        f'<div style="flex:1;min-width:0;">{_card_html("Оценка работы по отклонению, балл", html_score_table(rows))}</div>'
        f'<div style="flex:1;min-width:0;">{_card_html("По сравнению с Банком", html_compare_table(rows))}</div>'
        '</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    # Ряд 2: Динамика (белый фон) | Пораженность
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            card_header(st, "Динамика оценки ТОП-3")
            st.plotly_chart(V.top3_dynamics(), width="stretch", config=PLOT_CFG)
    with b:
        st.markdown(_card_html("Пораженность", html_prev_simple_table(rows)), unsafe_allow_html=True)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    # Ряд 3: Вес | Срок жизни — flex для гарантированной равной высоты
    st.markdown(
        '<div style="display:flex;gap:1rem;align-items:stretch;">'
        f'<div style="flex:1;min-width:0;">{_card_html("Вес отклонения", html_weight_table(rows))}</div>'
        f'<div style="flex:1;min-width:0;">{_card_html("Срок жизни (повтор.)", html_life_table(rows))}</div>'
        '</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    # Ряд 4: Пораженность отклонением, % (половина ширины)
    c1, _c2 = st.columns(2)
    with c1:
        st.markdown(_card_html("Пораженность отклонением, %", html_prev_table(rows)), unsafe_allow_html=True)


# ----------------------- общий блок: детализация -----------------------
def detail_view(scope_key, label, topN):
    c1, c2, _ = st.columns([1, 1, 2])
    cs = c1.date_input("Начало периода", value=date(2026, 5, 1), key=scope_key + "_cs")
    ce = c2.date_input("Конец периода", value=date(2026, 5, 31), key=scope_key + "_ce")
    cs_s, ce_s = str(cs), str(ce)
    st.markdown(f'<div class="cal-hint">Выберите период, за который показать отклонения. '
                f'В карте — все показатели: недельные (Н), месячные (М), квартальные (К) — '
                f'за <b>{cs.strftime("%d.%m.%Y")} – {ce.strftime("%d.%m.%Y")}</b>.</div>',
                unsafe_allow_html=True)
    st.write("")

    cols, rows, wcount = M.detail_matrix(scope_key, cs_s, ce_s)
    chart_card(f"Карта отклонений за период", V.heatmap(cols, rows), sub=label)

    a, b = st.columns(2)
    with a:
        reg = M.regular_deviations(rows, wcount, 6)
        with st.container(border=True):
            card_header(st, "Регулярные отклонения", "частота в ТОП-3 по неделям периода")
            if reg:
                st.plotly_chart(V.freq_bar(reg, wcount), width="stretch", config=PLOT_CFG)
            else:
                st.caption("Нет регулярных отклонений за период.")
    with b:
        stab = M.stable_deviations(rows, 6)
        with st.container(border=True):
            card_header(st, "Стабильно в норме", "ни разу не в ТОП-3")
            if stab:
                for r in stab:
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'padding:7px 2px;border-bottom:1px solid #eef2ef;font-size:13px">'
                        f'<span>{r["name"]}</span>{chip_g("в норме")}</div>', unsafe_allow_html=True)
            else:
                st.caption("—")

    byW, byM, byQ = M.top_by_period(rows, topN)
    chart_card(f"ТОП-{topN} по периодам", V.top_periods(byW, byM, byQ, topN), sub=label)


# ------------------------------- УРОВЕНЬ ОФИСА -------------------------------
def office_overview(vsp, ptype):
    score = 58
    dates, ranks = M.office_dynamics(vsp)
    left, right = st.columns([1, 1])
    with left:
        with st.container(border=True):
            card_header(st, "Интегральная оценка и место в рейтинге")
            rc, gc = st.columns([1, 1.15])
            rc.markdown(
                '<div class="rankcard"><div class="t">Место в рейтинге</div>'
                '<div class="big">19</div><div class="of">из 179</div>'
                '<div class="mv">▼ −3 позиции</div></div>', unsafe_allow_html=True)
            with gc:
                st.markdown('<div class="glabel">Интегральная оценка</div>', unsafe_allow_html=True)
                st.plotly_chart(V.gauge(score), width="stretch", config=PLOT_CFG)
                st.markdown(f'<div style="text-align:center;margin-top:-8px">{chip_g()}</div>',
                            unsafe_allow_html=True)
    with right:
        chart_card("Динамика рейтинга внутри зон интегральной оценки",
                   V.dynamics(dates, ranks))
    office_top3_block()


def view_office(ptype, period_label):
    if not ss.office:
        ss.office = M.offices_of_branch(ss.branch).vsp.iloc[0]
    vsp = ss.office
    bc1, bc2 = st.columns([0.16, 0.84])
    if bc1.button("← К филиалу", width="stretch"):
        ss.level = "Филиал"; st.rerun()
    bc2.markdown(f'<div class="h1">{vsp}</div>', unsafe_allow_html=True)

    tabs = st.tabs(["Обзор", "Детализация по отклонениям", "Ассистент"])
    with tabs[0]:
        st.markdown(f'<div class="h-sub">Обзор · период: {period_label}</div>', unsafe_allow_html=True)
        office_overview(vsp, ptype)
    with tabs[1]:
        st.markdown('<div class="h-sub">Все показатели за период из календаря ниже</div>',
                    unsafe_allow_html=True)
        detail_view("off:" + vsp, "по доп. офису", 3)
    with tabs[2]:
        chat_view("доп. офис " + vsp)


# ------------------------------- УРОВЕНЬ ФИЛИАЛА -------------------------------
def branch_overview(branch, ptype):
    brs = M.branches_summary().set_index("branch").loc[branch]
    c = st.columns(4)
    kpi(c[0], "Позиция филиала", f'{int(brs["rank"])} / 6',
        f'{"▲" if brs["delta"]<=0 else "▼"} {abs(int(brs["delta"]))} поз.')
    kpi(c[1], "Зелёная зона", int(brs["g"]), "", "g")
    kpi(c[2], "Жёлтая зона", int(brs["y"]), "", "y")
    kpi(c[3], "Красная зона", int(brs["r"]), "", "r")

    st.write("")
    # ТОП-5 проседающих по филиалу (из карты отклонений) + сравнение с Банком
    cols, rows, wc = M.detail_matrix("br:" + branch, "2026-05-01", "2026-05-31")
    top5 = sorted(rows, key=lambda r: -r["avg"])[:5]
    a, b = st.columns(2)
    with a:
        chart_card("ТОП-5 отклонений филиала",
                   V.hbar([r["name"] for r in top5], [r["avg"] for r in top5],
                          fmt="{:.2f}", xtitle="средний балл по офисам"),
                   sub="среднее по офисам")
    with b:
        items = ["Низкая доля операций, подписанных с использованием БМО",
                 "Длительные вакансии сотрудников ВСП",
                 "Высокая доля нарушений стандарта ИС СТАТУС"]
        cmp = M.comparison_with_bank(items)
        chart_card("Сравнение с Банком",
                   V.comparison(cmp.name.tolist(), cmp.mine.tolist(), cmp.bank.tolist()),
                   sub="Моя / По Банку")

    # доп. офисы филиала — визуализация + проваливание
    offs = M.offices_of_branch(branch)
    with st.container(border=True):
        card_header(st, "Доп. офисы филиала", "оценка и светофор · кнопка — детальная карточка")
        st.plotly_chart(V.office_scores(offs), width="stretch", config=PLOT_CFG)
        st.caption("Открыть доп. офис:")
        ocols = st.columns(3)
        for i, row in offs.iterrows():
            label = f'{row["rank"]}. {row["vsp"].split(" / ")[0]}'
            if ocols[i % 3].button(label, key="drill_o_" + row["vsp"], width="stretch"):
                ss.level = "Доп. офис"; ss.office = row["vsp"]; st.rerun()


def view_branch(ptype, period_label):
    branch = ss.branch
    bc1, bc2 = st.columns([0.14, 0.86])
    if bc1.button("← К банку", width="stretch"):
        ss.level = "Банк"; st.rerun()
    sel = bc2.selectbox("Филиал", M.BRANCHES, index=M.BRANCHES.index(branch),
                        label_visibility="collapsed")
    if sel != branch:
        ss.branch = sel; ss.office = None; st.rerun()

    st.markdown(f'<div class="h1">{branch}</div>', unsafe_allow_html=True)
    director = M.branches_summary().set_index("branch").loc[branch, "director"]

    tabs = st.tabs(["Обзор", "Детализация по отклонениям", "Ассистент"])
    with tabs[0]:
        st.markdown(f'<div class="h-sub">Руководитель: {director} · период: {period_label}</div>',
                    unsafe_allow_html=True)
        branch_overview(branch, ptype)
    with tabs[1]:
        st.markdown('<div class="h-sub">Все показатели за период из календаря ниже</div>',
                    unsafe_allow_html=True)
        detail_view("br:" + branch, "по филиалу", 5)
    with tabs[2]:
        chat_view("филиал " + branch)


# ------------------------------- АССИСТЕНТ -------------------------------
def assistant_reply(scope, q):
    """Реальный ответ через Claude API, если задан ANTHROPIC_API_KEY; иначе демо-эвристика."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()
            ctx = M.assistant_context(scope)
            msg = client.messages.create(
                model=os.environ.get("CLAUDE_MODEL", "claude-opus-4-8"),
                max_tokens=600,
                system=("Ты ассистент по мониторингу качества работы руководителей ВСП. "
                        "Отвечай кратко, по-русски, опираясь только на переданные данные."),
                messages=[{"role": "user", "content": f"Данные объекта:\n{ctx}\n\nВопрос: {q}"}],
            )
            return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        except Exception:
            return M.assistant_answer(scope, q)
    return M.assistant_answer(scope, q)


def chat_view(scope):
    key = "chat:" + scope
    if key not in ss:
        ss[key] = [("assistant", f"Здравствуйте! Помогу разобраться со статистикой по «{scope}». "
                                 "Спросите, что проседает, как дела на фоне Банка или что в норме.")]
    st.markdown('<div class="demo">Демо-ассистент: отвечает по данным объекта. '
                'Подключите ANTHROPIC_API_KEY — и он будет отвечать через Claude по всему срезу данных.</div>',
                unsafe_allow_html=True)
    st.write("")
    chips = ["Что больше всего проседает?", "Сравнение с Банком", "Что в норме?",
             "Как дела с вакансиями?", "Моё место в рейтинге?"]
    ccols = st.columns(len(chips))
    pending = None
    for i, ch in enumerate(chips):
        if ccols[i].button(ch, key=key + "_chip" + str(i), width="stretch"):
            pending = ch
    for who, text in ss[key]:
        st.chat_message(who, avatar="🟢" if who == "assistant" else None).write(text)
    typed = st.chat_input("Ваш вопрос…", key=key + "_in")
    q = typed or pending
    if q:
        ss[key].append(("user", q))
        ss[key].append(("assistant", assistant_reply(scope, q)))
        st.rerun()


# ------------------------------- ROUTER -------------------------------
st.markdown('<div class="brandbar">🟢&nbsp; Рейтинг ПАУ. Интегральная оценка качества работы '
            'руководителя с отклонениями ИС СТАТУС</div>', unsafe_allow_html=True)
level = seg("Уровень", ["Банк", "Филиал", "Доп. офис"], key="level")
st.divider()

if level == "Банк":
    view_bank()
elif level == "Филиал":
    view_branch(ptype, period_label)
else:
    view_office(ptype, period_label)
