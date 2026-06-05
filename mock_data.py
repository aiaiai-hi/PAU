"""
Данные для дашборда руководителей ВСП.

Здесь генерируется мок-датасет, повторяющий структуру исходного файла заказчика
(столбцы: Рег.директор, Региональный филиал, aggregation_level, Наименование ВСП,
Наименование отклонения, report_week_number / month / quarter, Вес отклонения,
Пораженность %, Средний счётчик (срок жизни), Оценка работы по отклонению,
Интегральная оценка, Позиция в рейтинге, Светофор и т.д.).

Чтобы подключить РЕАЛЬНЫЕ данные — замените функцию load_dataframe() на чтение
вашего .xlsx/.csv (pandas.read_excel / read_csv) и оставьте сигнатуры остальных
функций; они уже делают нужные группировки.
"""
import hashlib
from datetime import date
import numpy as np
import pandas as pd

YEAR = 2026
WEEKS = list(range(16, 31))          # отчётные недели, которые есть в данных
ANCHOR = pd.Timestamp(2026, 5, 1)    # начало недели 21 (как договорились: нед.21 = 01.05–07.05)

# отклонение: (название, вес, пораженность %, оценка, срок жизни, грануляность)
# грануляность: Н — считается понедельно, М — помесячно, К — поквартально
DEVIATIONS = [
    ("Низкая доля операций, подписанных с использованием БМО", 10, 51.4, 9.80, 7.7, "Н"),
    ("Низкая доля оформленных ДБО с активацией",               15, 12.0, 4.10, 3.2, "Н"),
    ("Низкая конверсия продаж ДК СК+",                         15,  1.8, 1.06, 4.1, "М"),
    ("Низкая конверсия продаж накопит. страхования",           15,  0.7, 0.21, 2.2, "М"),
    ("Высокая доля нарушений стандарта ИС СТАТУС",              8, 11.4, 1.88, 3.3, "Н"),
    ("Высокая доля непроизводительного времени",               5,  1.4, 0.27, 3.6, "Н"),
    ("Длительные вакансии сотрудников ВСП",                    1, 13.6, 2.31, 1.0, "К"),
    ("Несоблюдение режима работы ВСП",                         1,  2.0, 0.05, 2.4, "Н"),
    ("Высокая доля жалоб по ВСП",                              11,  0.6, 0.45, 1.1, "М"),
    ("Низкая продуктивность сотрудника",                       17,  0.9, 0.62, 0.6, "Н"),
]
GRAIN_NAME = {"Н": "понедельно", "М": "помесячно", "К": "поквартально"}

BRANCHES = ["Центральный филиал", "Северо-Западный филиал", "Поволжский филиал",
            "Сибирский филиал", "Уральский филиал", "Южный филиал"]
DIRECTORS = ["Иванова Е.А.", "Петров С.В.", "Соколова М.И.",
             "Кузнецов Д.Н.", "Орлова Т.П.", "Васильев А.Р."]
MGRS = ["Морозов", "Лебедева", "Новиков", "Зайцева", "Егоров", "Беляева"]
STREETS = ["Гагарина", "Ленина", "Мира", "Победы", "Советская", "Кирова", "Невский", "Садовая"]
LIGHTS = ["g", "y", "r"]


def _rng(key):
    """Детерминированный генератор от строкового ключа (стабильные «данные»)."""
    h = int(hashlib.md5(str(key).encode("utf-8")).hexdigest()[:8], 16)
    return np.random.default_rng(h)


def week_range(w):
    s = ANCHOR + pd.Timedelta(days=(w - 21) * 7)
    e = s + pd.Timedelta(days=6)
    return s, e


def week_label(w):
    s, e = week_range(w)
    return f"{s.day:02d}.{s.month:02d}–{e.day:02d}.{e.month:02d}"


# ----------------------------- офисы (ВСП) -----------------------------
def _build_offices():
    g = _rng("offices-master")
    rows = []
    for bi, br in enumerate(BRANCHES):
        n = 8 + int(g.integers(0, 7))
        for j in range(n):
            light = "g" if j < n * 0.55 else ("y" if j < n * 0.82 else "r")
            vsp = f"ВСП №{8500 + int(g.integers(0, 1400))} / {STREETS[int(g.integers(0, len(STREETS)))]}"
            rows.append(dict(
                director=DIRECTORS[bi], branch=br,
                manager=MGRS[int(g.integers(0, len(MGRS)))],
                vsp=vsp,
                pilot=("Пилот" if g.random() < 0.4 else "Не пилот"),
                rank=int(g.integers(1, 180)),
                score=int(round(40 + g.random() * 120)),
                light=light,
                delta=int(g.integers(-4, 5)),
            ))
    df = pd.DataFrame(rows)
    df = df.sort_values("rank").reset_index(drop=True)
    return df


OFFICES = _build_offices()


def load_dataframe():
    """Точка подключения реальных данных. Сейчас возвращает мок по структуре файла."""
    return OFFICES.copy()


def branches_summary():
    rows = []
    for bi, br in enumerate(BRANCHES):
        sub = OFFICES[OFFICES.branch == br]
        rows.append(dict(
            branch=br, director=DIRECTORS[bi], rank=bi + 1,
            score=int(round(70 + _rng("brscore" + br).random() * 80)),
            offices=len(sub),
            g=int((sub.light == "g").sum()),
            y=int((sub.light == "y").sum()),
            r=int((sub.light == "r").sum()),
            delta=int(_rng("brdelta" + br).integers(-3, 4)),
        ))
    return pd.DataFrame(rows).sort_values("rank").reset_index(drop=True)


def bank_summary():
    g = int((OFFICES.light == "g").sum())
    y = int((OFFICES.light == "y").sum())
    r = int((OFFICES.light == "r").sum())
    return dict(offices=len(OFFICES), g=g, y=y, r=r,
                avg=round(95 + _rng("bank").random() * 20, 1),
                obj_mon=1840, obj_dev=455)


def bank_top_deviations():
    df = pd.DataFrame([dict(name=d[0], weight=d[1], prevalence=d[2], score=d[3], life=d[4])
                       for d in DEVIATIONS])
    return df.sort_values("prevalence", ascending=False).reset_index(drop=True)


def offices_of_branch(branch):
    return OFFICES[OFFICES.branch == branch].sort_values("rank").reset_index(drop=True)


# ----------------------------- уровень офиса -----------------------------
def office_dynamics(vsp):
    """8 точек позиции в рейтинге по неделям (для графика динамики по зонам)."""
    g = _rng("dyn" + vsp)
    dates = [week_label(w).split("–")[0] for w in [18, 19, 20, 21, 22, 23, 24, 25]]
    ranks = [int(np.clip(15 + g.integers(-3, 35), 5, 170)) for _ in range(8)]
    return dates, ranks


def office_top_deviations(vsp, period_type, n=3):
    """ТОП-N отклонений нужной грануляности за выбранный период (для «Обзора»)."""
    gran = {"Неделя": "Н", "Месяц": "М", "Квартал": "К"}[period_type]
    rows = []
    for d in DEVIATIONS:
        if d[5] != gran:
            continue
        val = round(d[3] * (0.6 + _rng(f"otd{vsp}{d[0]}{period_type}").random() * 0.9), 2)
        rows.append(dict(name=d[0], score=val, weight=d[1], prevalence=d[2], life=d[4],
                         delta=round(_rng("dl" + vsp + d[0]).uniform(-1.5, 1.5), 1)))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("score", ascending=False).head(n).reset_index(drop=True)


def comparison_with_bank(items):
    """items: список названий отклонений -> сравнение Моя/Банк/Разница."""
    base = {d[0]: d[3] for d in DEVIATIONS}
    rows = []
    for name in items:
        mine = base.get(name, 1.0)
        bank = round(mine * 0.78, 2)
        rows.append(dict(name=name, mine=round(mine, 2), bank=bank,
                         diff=round(mine - bank, 2)))
    return pd.DataFrame(rows)


def multipliers(items):
    base = {d[0]: d for d in DEVIATIONS}
    rows = []
    for name in items:
        d = base.get(name)
        if not d:
            continue
        rows.append(dict(name=name, weight=d[1], prevalence=d[2],
                         prevalence_bank=round(d[2] * 0.7, 2),
                         life=d[4], life_bank=round(d[4] * 0.8, 2)))
    return pd.DataFrame(rows)


# ----------------------- детализация по отклонениям -----------------------
def _quarter_of(month):          # month 1..12 -> 0..3
    return (month - 1) // 3


def period_columns(cs, ce):
    """Колонки карты за период: недели месяца -> месяц -> (в конце квартала) квартал."""
    a, z = pd.Timestamp(cs), pd.Timestamp(ce)
    weeks = [w for w in WEEKS if (week_range(w)[1] >= a and week_range(w)[0] <= z)]
    months = []
    d = pd.Timestamp(a.year, a.month, 1)
    while d <= z:
        months.append((d.year, d.month))
        d = d + pd.offsets.MonthBegin(1)
    cols = []
    for i, (yy, mm) in enumerate(months):
        for w in weeks:
            ws = week_range(w)[0]
            if ws.month == mm and ws.year == yy:
                cols.append(("Н", f"Н{w}"))
        cols.append(("М", f"М{mm}"))
        nxt = months[i + 1] if i + 1 < len(months) else None
        if (nxt is None) or _quarter_of(nxt[1]) != _quarter_of(mm) or nxt[0] != yy:
            cols.append(("К", f"К{_quarter_of(mm) + 1}"))
    return cols


def detail_matrix(scope_key, cs, ce):
    """Карта отклонений: строки = отклонения, колонки = периоды (Н/М/К).
    Возвращает (cols, rows, week_count)."""
    cols = period_columns(cs, ce)
    rows = []
    for d in DEVIATIONS:
        grain, base = d[5], d[3]
        cells = []
        for (t, lab) in cols:
            if t == grain:
                v = max(0.0, round(base * (0.4 + _rng(f"{scope_key}{d[0]}{lab}{cs}{ce}").random() * 1.3), 2))
            else:
                v = None
            cells.append(v)
        vals = [v for v in cells if v is not None]
        avg = round(sum(vals) / len(vals), 2) if vals else 0.0
        rows.append(dict(
            name=d[0], grain=grain, cells=cells, avg=avg, freq=0,
            week_val=round(base * (0.6 + _rng("w" + scope_key + d[0] + str(cs)).random() * 0.8), 2),
            month_val=round(base * (0.6 + _rng("m" + scope_key + d[0] + str(cs)).random() * 0.8), 2),
            quart_val=round(base * (0.6 + _rng("q" + scope_key + d[0] + str(cs)).random() * 0.8), 2),
        ))
    week_idx = [i for i, (t, _) in enumerate(cols) if t == "Н"]
    for ci in week_idx:
        present = [(i, rows[i]["cells"][ci]) for i in range(len(rows)) if rows[i]["cells"][ci] is not None]
        present.sort(key=lambda x: -x[1])
        for i, _ in present[:3]:
            rows[i]["freq"] += 1
    return cols, rows, len(week_idx)


def regular_deviations(rows, week_count, top=6):
    reg = [r for r in rows if r["freq"] > 0]
    reg.sort(key=lambda r: (-r["freq"], -r["avg"]))
    return reg[:top]


def stable_deviations(rows, top=6):
    st = [r for r in rows if r["freq"] == 0 and r["grain"] == "Н"]
    st.sort(key=lambda r: r["avg"])
    return st[:top]


def top_by_period(rows, top):
    byW = sorted(rows, key=lambda r: -r["week_val"])[:top]
    byM = sorted(rows, key=lambda r: -r["month_val"])[:top]
    byQ = sorted(rows, key=lambda r: -r["quart_val"])[:top]
    return ([(r["name"], r["week_val"]) for r in byW],
            [(r["name"], r["month_val"]) for r in byM],
            [(r["name"], r["quart_val"]) for r in byQ])


# ----------------------------- ассистент -----------------------------
def assistant_context(scope):
    cols, rows, wc = detail_matrix(scope, "2026-05-01", "2026-05-31")
    reg = regular_deviations(rows, wc, 3)
    stab = stable_deviations(rows, 3)
    lines = [f"Объект: {scope}.",
             "Регулярные отклонения (чаще всего в ТОП-3):"]
    for r in reg:
        lines.append(f"- {r['name']}: средний балл {r['avg']}, в ТОП-3 {r['freq']} из {wc} нед.")
    lines.append("Стабильно в норме: " + ("; ".join(r["name"] for r in stab) or "—"))
    return "\n".join(lines)


def assistant_answer(scope, q):
    """Эвристический демо-ответ по данным объекта (без обращения к модели)."""
    cols, rows, wc = detail_matrix(scope, "2026-05-01", "2026-05-31")
    reg = regular_deviations(rows, wc, 3)
    stab = "; ".join(r["name"] for r in stable_deviations(rows, 3)) or "явных стабильных нет"
    ql = q.lower()
    if any(k in ql for k in ["банк", "сравн"]):
        return ("Сравнение с Банком: БМО 9,80 против 7,51 (хуже на 2,29); "
                "длительные вакансии 2,31 против 1,95; нарушения ИС СТАТУС 1,79 против 1,80 — на уровне Банка.")
    if any(k in ql for k in ["норм", "хорош", "стабильн", "не проседа"]):
        return f"Стабильно в норме: {stab}. Эти отклонения за период ни разу не попадали в ТОП-3."
    if "вакан" in ql:
        return ("Длительные вакансии сотрудников ВСП: вес 1 — влияние на рейтинг низкое, "
                "но показатель держится в проблемной зоне и тянет смежные (нагрузка, режим работы). "
                "Закрытие вакансий снизит риск по ним.")
    if any(k in ql for k in ["рейтинг", "место", "позици"]):
        return "Текущее место: 19 из 179 (▼ −3 позиции за период). Интегральная оценка — зелёная зона. Сильнее всего тянет вниз БМО (вес 10)."
    if any(k in ql for k in ["топ", "хуже", "проседа", "проблем", "внимани"]):
        body = "\n".join(f"{i+1}. {r['name']} — ср. балл {r['avg']}, в ТОП-3 {r['freq']} из {wc} нед."
                         for i, r in enumerate(reg))
        return f"ТОП-3 проблемных отклонений:\n{body}\n\nГлавный приоритет — первое: высокий вес и стабильно в ТОП."
    top = reg[0]["name"] if reg else "—"
    return (f"Кратко по «{scope}»: чаще всего проседает «{top}». Стабильно в норме: {stab}. "
            "Спросите про «сравнение с Банком», «вакансии» или «что в норме».")
