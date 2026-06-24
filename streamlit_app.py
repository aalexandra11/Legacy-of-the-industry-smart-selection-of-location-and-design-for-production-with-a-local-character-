import streamlit as st
import requests
import folium
import base64
import pandas as pd
import io
import plotly.graph_objects as go
from streamlit_folium import st_folium
from folium import Element
import urllib.parse

st.set_page_config(layout="wide", page_title="Наследие индустрии", initial_sidebar_state="expanded")

# Подключаем шрифты Google
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@400;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

THEME_CSS = """
<style>
/* ========== БАЗОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ СВЕТЛОЙ ТЕМЫ ========== */
:root, [data-theme="light"] {
    --base-bg:      #F5F5F5;
    --card-bg:      #FFFFFF;
    --card-border:  #E0E0E0;
    --text:         #2C2C2C;
    --text-dim:     #4F4F4F;
    --text-muted:   #7A7A7A;
    --sidebar-bg:   #EBEBEB;
    --border:       #D1D1D1;
    --accent:       #0B2B40;
    --accent-light: #1E6F9F;
    --gold:         #D4AF37;
    --gold-light:   #E6C358;
    --chip-g-bg:    #E0F2E9; --chip-g-text: #1E6F3F;
    --chip-r-bg:    #FCE4E4; --chip-r-text: #B91C1C;
    --chip-b-bg:    #E2EAF4; --chip-b-text: #1A4C7A;
    --chip-gold-bg: #FEF5E7; --chip-gold-text: #8B6914;
    --rank1: #D4AF37; --rank2: #7A8B9B; --rank3: #A67C52;
    --button-bg:    #F0F0F0;
    --button-text:  #2C2C2C;
    --button-hover: #E0E0E0;
    --button-border: #CCCCCC;
}

/* ========== ТЁМНАЯ ТЕМА ========== */
[data-theme="dark"] {
    --base-bg:      #0A1A24;
    --card-bg:      #122B38;
    --card-border:  #1E3A4A;
    --text:         #F0F4F8;
    --text-dim:     #C9D9E8;
    --text-muted:   #8DA3B5;
    --sidebar-bg:   #07141C;
    --border:       #1E3A4A;
    --accent:       #1E6F9F;
    --accent-light: #3A8BBF;
    --gold:         #E6C358;
    --gold-light:   #F1D978;
    --chip-g-bg:    #0F2E24; --chip-g-text: #9DD8B8;
    --chip-r-bg:    #3A1818; --chip-r-text: #F4A2A2;
    --chip-b-bg:    #123A5A; --chip-b-text: #9AC4E6;
    --chip-gold-bg: #3A2E0F; --chip-gold-text: #F7D44A;
    --rank1: #E6C358; --rank2: #A0AAB5; --rank3: #CD9B6B;
    --button-bg:    #1E6F9F;
    --button-text:  #FFFFFF;
    --button-hover: #3A8BBF;
    --button-border: #2C5A7A;
}

/* Базовые стили */
html, body { font-size: 17px !important; }
body { background: var(--base-bg) !important; color: var(--text) !important; }

/* ========== КРУПНАЯ ШАПКА ========== */
.main-header {
    margin-bottom: 2rem;
    text-align: center;
}
.main-header .section-label {
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 0.25rem;
}
.main-header h1 {
    font-size: 4rem !important;
    font-weight: 800 !important;
    font-family: 'Bebas Neue', 'Manrope', sans-serif;
    letter-spacing: 0.05em;
    color: var(--text);
    margin: 0;
    line-height: 1.1;
}
.main-header .subtitle {
    font-size: 1.2rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
}

/* Остальные общие стили */
.stMarkdown p, .stMarkdown li, .stMarkdown span,
p, span, li, label { font-size: 1.05rem !important; color: var(--text) !important; line-height: 1.65 !important; }

h1 { font-size: 2.4rem !important; font-weight: 800 !important; color: var(--text) !important; }
h2 { font-size: 1.9rem !important; font-weight: 700 !important; color: var(--text) !important; }
h3 { font-size: 1.5rem !important; font-weight: 700 !important; color: var(--text) !important; }
h4 { font-size: 1.2rem !important; font-weight: 700 !important; margin: 0 0 .8rem 0 !important; color: var(--text) !important; }

/* Сайдбар */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: var(--text-dim) !important;
}
[data-testid="stSidebar"] input[type="number"],
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"],
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] div,
[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] div {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--gold) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--button-bg) !important;
    color: var(--button-text) !important;
    border: 1px solid var(--button-border) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--button-hover) !important;
}

/* Основные кнопки */
.stButton > button {
    background: var(--button-bg) !important;
    color: var(--button-text) !important;
    border: 1px solid var(--button-border) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--button-hover) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.2) !important;
}

/* Карточки */
.card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 1.35rem 1.5rem;
    margin-bottom: 1.1rem;
}
.card h4 { border-bottom: 2px solid var(--border); padding-bottom: .5rem; margin-bottom: .9rem !important; }

.card-row {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding: .45rem 0; border-bottom: 1px solid var(--border);
}
.card-label { color: var(--text-muted); font-size: 0.95rem; }
.card-val   { color: var(--text); font-size: 1.0rem; font-weight: 700; text-align: right; }

.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .6rem; margin-bottom: .8rem; }
.stat-item { background: var(--base-bg); border: 1px solid var(--border); border-radius: 9px; padding: .65rem .8rem; }
.si-label  { font-size: .82rem; color: var(--text-muted); }
.si-val    { font-size: 1.15rem; font-weight: 800; color: var(--text); font-family: 'JetBrains Mono', monospace; }

/* Чипсы */
.chip     { display:inline-block; padding:.28rem .75rem; border-radius:6px; font-size:.88rem; font-weight:700; margin:.2rem .2rem 0 0; }
.chip-g   { background:var(--chip-g-bg); color:var(--chip-g-text); }
.chip-r   { background:var(--chip-r-bg); color:var(--chip-r-text); }
.chip-b   { background:var(--chip-b-bg); color:var(--chip-b-text); }
.chip-gold { background:var(--chip-gold-bg); color:var(--chip-gold-text); }

/* Баннеры рангов */
.rank-banner {
    display: flex; align-items: center; gap: 1.4rem;
    background: var(--card-bg); border: 2px solid var(--rank1);
    border-radius: 16px; padding: 1.2rem 1.5rem; margin-bottom: 1.3rem;
}
.rank-banner.r2 { border-color: var(--rank2); }
.rank-banner.r3 { border-color: var(--rank3); }
.rank-num  { font-family:'Bebas Neue',sans-serif; font-size:3.8rem; line-height:1; color:var(--rank1); min-width:60px; }
.rank-score { margin-left:auto; text-align:center; background:var(--base-bg); border:1px solid var(--border); border-radius:10px; padding:.7rem 1.1rem; }
.snum  { font-family:'JetBrains Mono',monospace; font-size:2rem; font-weight:800; color:var(--gold); }
.slabel { font-size:.75rem; color:var(--text-muted); }

/* Бюджет */
.budget-ok   { background:var(--chip-g-bg); color:var(--chip-g-text); border-radius:10px; padding:.7rem 1.2rem; margin-bottom:1rem; }
.budget-warn { background:var(--chip-r-bg); color:var(--chip-r-text); border-radius:10px; padding:.7rem 1.2rem; margin-bottom:1rem; }

/* Аналитика */
.ana-box { background:var(--card-bg); border-left:4px solid var(--accent); border-radius:12px; padding:1.2rem 1.4rem; margin-bottom:1rem; }
.at { font-weight:800; font-size:1.05rem; color:var(--gold); margin-bottom:.6rem; }

/* KPI */
.kpi-row { display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.2rem; }
.kpi-box { flex:1; min-width:140px; background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:.9rem 1.1rem; text-align:center; }
.kpi-val { font-size:1.7rem; font-weight:800; color:var(--gold); font-family:'JetBrains Mono',monospace; }
.kpi-lbl { font-size:.8rem; color:var(--text-muted); }

/* Секции в сайдбаре */
.sb-section { background:var(--base-bg); border:1px solid var(--border); border-radius:10px; padding:.9rem 1rem; margin-bottom:.9rem; }
.sb-title { font-size:.82rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em; color:var(--text-muted); margin-bottom:.6rem; }

/* Цветовые образцы */
.color-swatch {
    width: 100%;
    height: 56px;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    border: 1px solid var(--border);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2);
}
.color-label {
    font-size: 0.85rem;
    text-align: center;
    color: var(--text-muted);
    font-family: monospace;
}

.footer { text-align:center; font-size:.82rem; color:var(--text-muted); padding:2rem 0 1rem; border-top:1px solid var(--border); margin-top:2rem; }

/* Переопределение чипсов мультиселекта и других элементов на золотой */
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"],
.stMultiSelect [data-baseweb="tag"] {
    background-color: var(--gold-light) !important;
    color: var(--accent) !important;
    border: 1px solid var(--gold) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] button,
.stMultiSelect [data-baseweb="tag"] button {
    color: var(--accent) !important;
    opacity: 0.8 !important;
}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] button:hover,
.stMultiSelect [data-baseweb="tag"] button:hover {
    color: var(--accent) !important;
    opacity: 1 !important;
}
[data-theme="dark"] [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"],
[data-theme="dark"] .stMultiSelect [data-baseweb="tag"] {
    background-color: var(--gold) !important;
    color: var(--accent-light) !important;
    border-color: var(--gold-light) !important;
}
[data-theme="dark"] [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] button,
[data-theme="dark"] .stMultiSelect [data-baseweb="tag"] button {
    color: var(--accent-light) !important;
}

/* Слайдеры – ползунок и активная часть */
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--gold) !important;
}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[data-testid="stMarkdown"] {
    color: var(--gold) !important;
}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[aria-valuenow] ~ div {
    background: var(--gold-light) !important;
}

/* Чекбоксы и радио – активное состояние */
[data-testid="stSidebar"] .stCheckbox [role="checkbox"][aria-checked="true"],
.stCheckbox [role="checkbox"][aria-checked="true"] {
    border-color: var(--gold) !important;
    background-color: var(--gold) !important;
}
[data-testid="stSidebar"] .stCheckbox [role="checkbox"][aria-checked="true"]:hover,
.stCheckbox [role="checkbox"][aria-checked="true"]:hover {
    border-color: var(--gold-light) !important;
    background-color: var(--gold-light) !important;
}
/* Радио кнопки */
[data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"],
.stRadio [role="radio"][aria-checked="true"] {
    border-color: var(--gold) !important;
}
[data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"] div,
.stRadio [role="radio"][aria-checked="true"] div {
    background-color: var(--gold) !important;
}

/* Focus-состояния для полей ввода */
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus,
[data-testid="stSidebar"] select:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 0.2rem rgba(212, 175, 55, 0.25) !important;
}
[data-theme="dark"] [data-testid="stSidebar"] input:focus,
[data-theme="dark"] [data-testid="stSidebar"] textarea:focus,
[data-theme="dark"] [data-testid="stSidebar"] select:focus {
    box-shadow: 0 0 0 0.2rem rgba(230, 195, 88, 0.25) !important;
}

/* Убираем красный из предупреждений */
.stAlert, .stException {
    border-left-color: var(--gold) !important;
}
.stAlert svg, .stException svg {
    fill: var(--gold) !important;
}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)

# Заголовок (шапка) крупным текстом
st.markdown("""
<div class="main-header">
  <div class="section-label">Платформа анализа промышленных площадок РФ</div>
  <h1>НАСЛЕДИЕ ИНДУСТРИИ</h1>
  <div class="subtitle">Умный подбор локации для завода сэндвич-панелей – топ-3 площадки с детальной аналитикой</div>
</div>
""", unsafe_allow_html=True)

API = "http://127.0.0.1:8000"

# Инициализация сессии
for k, v in [("api_response", None), ("all_alternatives", None),
             ("budget_at_request", 150), ("last_payload", None),
             ("renders", {}), ("dark_mode", True)]:
    if k not in st.session_state:
        st.session_state[k] = v


# Функция для переключения темы
def set_theme(dark):
    st.session_state.dark_mode = dark
    # JavaScript для установки атрибута data-theme и сохранения в sessionStorage
    js_code = f"""
    <script>
        document.documentElement.setAttribute('data-theme', '{'dark' if dark else 'light'}');
        sessionStorage.setItem('dark_mode', '{str(dark).lower()}');
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)


# ========== БОКОВАЯ ПАНЕЛЬ ==========
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Bebas Neue',sans-serif;font-size:1.9rem;letter-spacing:.08em;color:var(--gold);margin-bottom:1.1rem;padding-bottom:.7rem;border-bottom:2px solid var(--border);">
    ПАРАМЕТРЫ ПРОЕКТА
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-title">Производство</div>', unsafe_allow_html=True)
    vol = st.number_input("Объём выпуска, тыс. м²/год", min_value=100, max_value=1000, value=350, step=50)
    emp = st.number_input("Численность сотрудников", min_value=10, max_value=500, value=90, step=5)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-title">Финансы</div>', unsafe_allow_html=True)
    budget = st.number_input("Инвестиционный бюджет, млн руб.", min_value=10, max_value=2000, value=220, step=10)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-title">Логистика</div>', unsafe_allow_html=True)
    railway = st.checkbox("Требуется ж/д ветка", value=False)
    highway = st.number_input("Макс. расстояние до трассы, км", min_value=1, max_value=200, value=30, step=5)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-title">Архитектура и среда</div>', unsafe_allow_html=True)
    style = st.selectbox("Архитектурный приоритет",
                         ["Аутентичность региону", "Техно-стиль", "Экодизайн"])
    improve = st.multiselect("Элементы благоустройства (до 3)",
                             ["Аллея", "Сквер", "Беседки", "Сцена", "Тропа", "Пруд", "Арт-объект"],
                             default=["Аллея", "Сквер"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-title">Социальный блок</div>', unsafe_allow_html=True)
    h_per = st.selectbox("Жильё для сотрудников (%)", [0, 30, 50, 70], index=1)
    h_type = st.radio("Тип жилья", ["общежитие", "квартиры"])
    kg = st.selectbox("Мест в детсаду на 100 сотр.", [0, 15, 30, 50], index=1)
    sport = st.multiselect("Спортивные объекты (до 2)",
                           ["Уличные тренажёры", "Стадион", "Бассейн", "Спортзал", "Хоккейная коробка"],
                           default=["Уличные тренажёры"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-title">Отображение</div>', unsafe_allow_html=True)
    dark_toggle = st.checkbox("", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        set_theme(dark_toggle)
    st.markdown('</div>', unsafe_allow_html=True)

    find_btn = st.button("Найти лучшие площадки", use_container_width=True, type="primary")

# При первой загрузке устанавливаем тему из session_state
if not st.session_state.get("theme_initialized"):
    set_theme(st.session_state.dark_mode)
    st.session_state.theme_initialized = True

# ========== ЗАПРОС К API ==========
if find_btn:
    payload = {
        "volume_thousand_m2": vol,
        "employees": emp,
        "budget_million_rub": budget,
        "need_railway": railway,
        "max_distance_to_highway_km": highway,
        "arch_priority": style,
        "improvement_items": improve[:3],
        "housing_percent": h_per,
        "housing_type": h_type,
        "kindergarten_places_per_100": kg,
        "sport_items": sport[:2],
        "insulation_type": "ППС",
    }
    st.session_state.budget_at_request = budget
    st.session_state.last_payload = payload
    st.session_state.api_response = None
    st.session_state.all_alternatives = None
    st.session_state.renders = {}

    with st.spinner("Анализируем площадки… до 60 секунд"):
        try:
            r_top = requests.post(f"{API}/api/analyze", json=payload, timeout=180)
            if r_top.status_code == 200:
                d = r_top.json()
                if d.get("success") and d.get("top_regions"):
                    st.session_state.api_response = d
                else:
                    st.error(f"Ошибка топ-3: {d}")
            else:
                st.error(f"Ошибка /analyze: {r_top.status_code}")

            r_all = requests.post(f"{API}/api/all_alternatives", json=payload, timeout=60)
            if r_all.status_code == 200:
                da = r_all.json()
                if da.get("success"):
                    st.session_state.all_alternatives = da["all_regions"]
            else:
                st.warning(f"/api/all_alternatives: {r_all.status_code}")

            if st.session_state.api_response:
                st.success("Анализ завершён!")
        except requests.exceptions.ConnectionError:
            st.error(f"Нет соединения с {API}. Запущен ли бэкенд?")
        except Exception as e:
            st.error(f"Ошибка: {e}")


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def dm():
    return st.session_state.get("dark_mode", True)


def plotly_layout(dark=True, **kw):
    txt = "#E8EDF5" if dark else "#2C2C2C"
    grid = "#1E2A3A" if dark else "#D1D1D1"
    bg = "rgba(0,0,0,0)"
    title = "#E6C358" if dark else "#D4AF37"
    d = dict(
        paper_bgcolor=bg, plot_bgcolor=bg,
        font=dict(family="Manrope,sans-serif", color=txt, size=15),
        margin=dict(l=60, r=60, t=80, b=80),
        title=dict(font=dict(size=18, color=title)),
        xaxis=dict(tickfont=dict(size=14, color=txt), gridcolor=grid, linecolor=grid),
        yaxis=dict(tickfont=dict(size=14, color=txt), gridcolor=grid, linecolor=grid),
        legend=dict(font=dict(size=14, color=txt), bgcolor="rgba(0,0,0,0)"),
    )
    d.update(kw)
    return d


PCOLS = ["#D4AF37", "#7A8B9B", "#A67C52"]
FILL_C = ["rgba(212,175,55,0.13)", "rgba(122,139,155,0.13)", "rgba(166,124,82,0.13)"]
PCOLS_LIGHT = ["#B8860B", "#5A6B7A", "#8B5A2B"]
FILL_LIGHT = ["rgba(184,134,11,0.10)", "rgba(90,107,122,0.10)", "rgba(139,90,43,0.10)"]


def pc():  return PCOLS if dm() else PCOLS_LIGHT


def fc():  return FILL_C if dm() else FILL_LIGHT


def dl(**kw): return plotly_layout(dark=dm(), **kw)


def chip(text, kind="neu"):
    return f'<span class="chip chip-{kind}">{text}</span>'


def yn_chip(val):
    ok = str(val).strip().lower() in ("да", "yes")
    return chip("Да", "g") if ok else chip("Нет", "r")


def kpi_box(val, label):
    return f'<div class="kpi-box"><div class="kpi-val">{val}</div><div class="kpi-lbl">{label}</div></div>'


def render_suppliers(sup_list):
    if not sup_list:
        return '<span style="color:var(--text-muted)">нет данных</span>'
    out = ""
    for s in sup_list:
        dist_km = s.get("distance_km", "?")
        name = s.get("name", "?")
        color = "var(--chip-g-text)" if int(dist_km) < 200 else (
            "var(--gold)" if int(dist_km) < 500 else "var(--chip-r-text)")
        out += f"""<div class="sup-block">
            <div class="sup-name">{name}</div>
            <div class="sup-dist" style="color:{color};">▸ {dist_km} км</div>
        </div>"""
    return out


# ========== ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ==========
if st.session_state.api_response and st.session_state.api_response.get("success"):
    top_regions = st.session_state.api_response["top_regions"]
    all_regions = st.session_state.all_alternatives or []
    budget_limit = st.session_state.budget_at_request
    payload_sent = st.session_state.last_payload or {}

    if not top_regions:
        st.warning("Нет подходящих площадок.")
        st.stop()

    # Карта
    st.markdown('<div class="section-label">Расположение лучших площадок</div>', unsafe_allow_html=True)
    tile = "CartoDB dark_matter" if dm() else "CartoDB positron"
    m = folium.Map(location=[55.0, 50.0], zoom_start=4, tiles=tile, attributionControl=False)
    legend_html = f'''<div style="position:fixed;bottom:24px;left:24px;z-index:1000;
        background:{"#0A1A24" if dm() else "#FFFFFF"}dd;border:1px solid #4B5563;padding:14px 18px;
        border-radius:12px;font-family:'Manrope',sans-serif;font-size:15px;color:{"#F0F4F8" if dm() else "#2C2C2C"};">
        <div style="font-weight:800;margin-bottom:8px;color:{"#E6C358" if dm() else "#D4AF37"};">ТОП-3 ПЛОЩАДКИ</div>
        <div style="margin:4px 0;"><span style="color:#D4AF37;font-size:20px;">●</span>&nbsp; 1 место</div>
        <div style="margin:4px 0;"><span style="color:#7A8B9B;font-size:20px;">●</span>&nbsp; 2 место</div>
        <div style="margin:4px 0;"><span style="color:#A67C52;font-size:20px;">●</span>&nbsp; 3 место</div>
    </div>'''
    m.get_root().html.add_child(Element(legend_html))
    # Фильтруем регионы без координат (упавшие при обработке)
    top_regions = [r for r in top_regions if "lat" in r and "lon" in r and not r.get("error")]
    for i, reg in enumerate(top_regions):
        folium.CircleMarker(
            [reg["lat"], reg["lon"]], radius=22,
            color=pc()[i], fill=True, fill_color=pc()[i],
            fill_opacity=.85, weight=3,
            popup=folium.Popup(f"<b>#{i + 1} {reg.get('site_name', '')}</b><br>{reg['region']}<br>"
                               f"<b>Рейтинг:</b> {reg['score']}<br>"
                               f"<b>Смета:</b> {reg.get('cost_data', {}).get('total_cost_million_rub', '—')} млн руб.",
                               max_width=300),
            tooltip=f"#{i + 1} {reg.get('site_name', '')} — {reg['score']} баллов"
        ).add_to(m)
    st_folium(m, height=580, width="100%", returned_objects=[])

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # Вкладки
    tab1, tab2, tab3 = st.tabs(["Топ-3 площадки", "Сравнение лидеров", "Все варианты"])

    if not top_regions:
        st.error("Не удалось обработать ни одну площадку. Проверьте логи бэкенда.")
        st.stop()

    # ========== ВКЛАДКА 1: ТОП-3 ==========
    with tab1:
        RC = ["", "r2", "r3"]
        RL = ["1 МЕСТО", "2 МЕСТО", "3 МЕСТО"]
        RCOLS = ["var(--rank1)", "var(--rank2)", "var(--rank3)"]

        subtabs = st.tabs([f"#{i + 1} {top_regions[i].get('site_name') or top_regions[i].get('district') or top_regions[i].get('region', f'Регион {i+1}')}"
                           for i in range(len(top_regions))])

        for idx, subtab in enumerate(subtabs):
            with subtab:
                reg = top_regions[idx]
                cost = reg.get("cost_data", {})
                areas = reg.get("areas", {})
                total = cost.get("total_cost_million_rub", 0)
                concept = reg.get("concept_board", {})
                ana = reg.get("analytics", {})

                st.markdown(f"""
                <div class="rank-banner {RC[idx]}">
                  <div class="rank-num">{idx + 1}</div>
                  <div class="rank-info">
                    <div style="font-size:.82rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:{RCOLS[idx]};margin-bottom:.3rem;">{RL[idx]}</div>
                    <h2 style="margin:0 0 .2rem 0;">{reg.get('site_name', reg['district'])}</h2>
                    <div class="rsub">{reg['region']} &nbsp;·&nbsp; ID: {reg.get('site_id', '—')} &nbsp;·&nbsp; Рейтинг: {reg['score']} баллов</div>
                  </div>
                  <div class="rank-score"><div class="snum">{reg['score']}</div><div class="slabel">из ~130</div></div>
                </div>""", unsafe_allow_html=True)

                # KPI строка
                kpi_html = '<div class="kpi-row">'
                kpi_html += kpi_box(f"{total} млн", "Смета проекта")
                kpi_html += kpi_box(f"{cost.get('annual_fot_million_rub', '—')} млн", "Годовой ФОТ")
                kpi_html += kpi_box(f"{reg.get('tax_benefit', '—')}%", "Налог. льгота")
                kpi_html += kpi_box(f"{reg.get('steel_distance_km', '—')} км", "До поставщика стали")
                kpi_html += kpi_box(f"{reg.get('energy_tariff_rub_kwh', '—')} руб", "Тариф эл-эн.")
                kpi_html += kpi_box(f"{reg.get('avg_salary_rub', 0):,}".replace(",", " ") + " ₽", "Ср. зарплата / мес")
                kpi_html += '</div>'
                st.markdown(kpi_html, unsafe_allow_html=True)

                # Бюджет
                if isinstance(total, (int, float)):
                    if total <= budget_limit:
                        econ = round(budget_limit - total, 1)
                        st.markdown(
                            f'<div class="budget-ok">В бюджете: <b>{total} млн руб.</b> из {budget_limit} млн — экономия {econ} млн руб. ({round(econ / budget_limit * 100, 1)}%)</div>',
                            unsafe_allow_html=True)
                    else:
                        over = round(total - budget_limit, 1)
                        st.markdown(
                            f'<div class="budget-warn">Превышение бюджета на <b>{over} млн руб.</b> ({round(over / budget_limit * 100, 1)}%) — смета {total} из {budget_limit} млн руб.</div>',
                            unsafe_allow_html=True)

                col_l, col_r = st.columns([0.44, 0.56], gap="large")

                with col_l:
                    # Смета
                    constr = cost.get('construction_million_rub', 0)
                    logist = cost.get('logistics_million_rub', 0)
                    conn = cost.get('connection_million_rub', 0)
                    land = cost.get('land_cost_million_rub', 0)
                    fot = cost.get('annual_fot_million_rub', 0)
                    total_c = cost.get('total_cost_million_rub', 0)
                    constr_pct = round(constr / max(total_c, 1) * 100, 1)
                    logist_pct = round(logist / max(total_c, 1) * 100, 1)
                    conn_pct = round(conn / max(total_c, 1) * 100, 1)
                    st.markdown(f"""
                    <div class="card"><h4>Смета проекта</h4>
                    <div class="stat-grid">
                      <div class="stat-item"><div class="si-label">ИТОГО</div><div class="si-val">{total_c} млн</div></div>
                      <div class="stat-item"><div class="si-label">ФОТ / год</div><div class="si-val">{fot} млн</div></div>
                      <div class="stat-item"><div class="si-label">Строительство</div><div class="si-val">{constr} млн</div></div>
                      <div class="stat-item"><div class="si-label">Логистика</div><div class="si-val">{logist} млн</div></div>
                      <div class="stat-item"><div class="si-label">Подключение сетей</div><div class="si-val">{conn} млн</div></div>
                      <div class="stat-item"><div class="si-label">Земля</div><div class="si-val">{land} млн</div></div>
                    </div>
                    <div class="card-row"><span class="card-label">Доля строительства</span><span class="card-val">{constr_pct}%</span></div>
                    <div class="card-row"><span class="card-label">Доля логистики</span><span class="card-val">{logist_pct}%</span></div>
                    <div class="card-row"><span class="card-label">Доля подключений</span><span class="card-val">{conn_pct}%</span></div>
                    <div class="card-row"><span class="card-label">Класс опасности</span><span class="card-val">{cost.get('hazard_class', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Тип утеплителя</span><span class="card-val">{cost.get('insulation_type', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Транспорт сотрудников</span><span class="card-val">{"Нужен автобус" if cost.get('need_bus') else "Доступен пешком"}</span></div>
                    </div>""", unsafe_allow_html=True)

                    # Площади
                    total_area = cost.get('area_total_m2', sum(areas.values()))
                    kg_row = f'<div class="card-row"><span class="card-label">Детский сад</span><span class="card-val">{areas.get("kindergarten", "—")} м²</span></div>' if areas.get(
                        "kindergarten", 0) else ""
                    hous_row = f'<div class="card-row"><span class="card-label">Жильё сотрудников</span><span class="card-val">{areas.get("housing", "—")} м²</span></div>' if areas.get(
                        "housing", 0) else ""
                    st.markdown(f"""
                    <div class="card"><h4>Площади объектов</h4>
                    <div class="card-row"><span class="card-label">Производственный цех</span><span class="card-val">{areas.get('cech', '—')} м²</span></div>
                    <div class="card-row"><span class="card-label">Складской комплекс</span><span class="card-val">{areas.get('sklad', '—')} м²</span></div>
                    <div class="card-row"><span class="card-label">АБК (офис + раздевалки)</span><span class="card-val">{areas.get('abk', '—')} м²</span></div>
                    <div class="card-row"><span class="card-label">Столовая</span><span class="card-val">{areas.get('canteen', '—')} м²</span></div>
                    <div class="card-row"><span class="card-label">Медпункт</span><span class="card-val">{areas.get('medpunkt', '—')} м²</span></div>
                    <div class="card-row"><span class="card-label">Парковка</span><span class="card-val">{areas.get('parking', '—')} м²</span></div>
                    <div class="card-row"><span class="card-label">Дороги на территории</span><span class="card-val">{areas.get('roads', '—')} м²</span></div>
                    {hous_row}{kg_row}
                    <div class="card-row" style="margin-top:.5rem;padding-top:.7rem;border-top:2px solid var(--border);">
                      <span class="card-label" style="font-weight:800;">ИТОГО застройки</span>
                      <span class="card-val" style="font-size:1.25rem;color:var(--gold);">{total_area} м²</span>
                    </div></div>""", unsafe_allow_html=True)

                    # Инфраструктура
                    gas_ok = str(reg.get("gas_available", "")).strip().lower() in ("да", "yes")
                    rw_ok = str(reg.get("railway_available", "")).strip().lower() in ("да", "yes")
                    park_ok = str(reg.get("industrial_park_available", "")).strip().lower() in ("да", "yes")
                    pwr_f = reg.get("free_power_kva", 0)
                    pwr_n = cost.get("power_required_kva", 0)
                    pwr_ok = pwr_f >= pwr_n
                    pwr_delta = pwr_f - pwr_n
                    st.markdown(f"""
                    <div class="card"><h4>Инфраструктура площадки</h4>
                    <div class="card-row"><span class="card-label">Газоснабжение</span>{yn_chip(reg.get("gas_available", ""))}</div>
                    <div class="card-row"><span class="card-label">Железная дорога</span>{yn_chip(reg.get("railway_available", ""))}</div>
                    <div class="card-row"><span class="card-label">Промышленный парк</span>{yn_chip(reg.get("industrial_park_available", ""))}</div>
                    <div class="card-row"><span class="card-label">Свободная мощность</span><span class="card-val" style="color:{'var(--chip-g-text)' if pwr_ok else 'var(--chip-r-text)'};">{pwr_f} кВА</span></div>
                    <div class="card-row"><span class="card-label">Требуется мощность</span><span class="card-val">{pwr_n} кВА</span></div>
                    <div class="card-row"><span class="card-label">Резерв / дефицит</span><span class="card-val" style="color:{'var(--chip-g-text)' if pwr_ok else 'var(--chip-r-text)'};">{'+' if pwr_ok else ''}{pwr_delta} кВА</span></div>
                    <div class="card-row"><span class="card-label">До федеральной трассы</span><span class="card-val">{reg.get('federal_road_distance_km', '—')} км</span></div>
                    <div class="card-row"><span class="card-label">Тариф электроэнергии</span><span class="card-val">{reg.get('energy_tariff_rub_kwh', '—')} руб./кВт·ч</span></div>
                    <div class="card-row"><span class="card-label">Уровень газификации</span><span class="card-val">{reg.get('gasification_percent', '—')}%</span></div>
                    </div>""", unsafe_allow_html=True)

                    # Поставщики стали
                    steel_list = reg.get("steel_suppliers_list", [])
                    st.markdown(f"""
                    <div class="card"><h4>Поставщики стали</h4>
                    <div class="card-row"><span class="card-label">Ближайший</span><span class="card-val" style="font-size:.95rem;">{reg.get('closest_steel_supplier', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Расстояние до ближайшего</span><span class="card-val">{reg.get('steel_distance_km', '—')} км</span></div>
                    <div>{render_suppliers(steel_list)}</div>
                    </div>""", unsafe_allow_html=True)

                    # Поставщики утеплителя
                    insul_list = reg.get("insulation_suppliers_list", [])
                    st.markdown(f"""
                    <div class="card"><h4>Поставщики утеплителя</h4>
                    <div class="card-row"><span class="card-label">Ближайший</span><span class="card-val" style="font-size:.95rem;">{reg.get('closest_insulation_supplier', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Расстояние до ближайшего</span><span class="card-val">{reg.get('insulation_distance_km', '—')} км</span></div>
                    <div>{render_suppliers(insul_list)}</div>
                    </div>""", unsafe_allow_html=True)

                    # Рынок сбыта
                    st.markdown(f"""
                    <div class="card"><h4>Рынок сбыта и логистика</h4>
                    <div class="card-row"><span class="card-label">Расстояние до рынка сбыта</span><span class="card-val">{reg.get('market_distance_km', '—')} км</span></div>
                    <div class="card-row"><span class="card-label">Затраты на логистику</span><span class="card-val">{cost.get('logistics_million_rub', '—')} млн руб.</span></div>
                    <div class="card-row"><span class="card-label">Доля логистики в смете</span><span class="card-val">{round(cost.get('logistics_million_rub', 0) / max(cost.get('total_cost_million_rub', 1), 1) * 100, 1)}%</span></div>
                    <div class="card-row"><span class="card-label">Плотность дорог в регионе</span><span class="card-val">{reg.get('road_density', '—')} км/1000 км²</span></div>
                    </div>""", unsafe_allow_html=True)

                    # Экономика и рынок труда
                    avg_sal = reg.get('avg_salary_rub', 0)
                    rent = reg.get('rent_1room_rub', 0)
                    rent_pct = round(rent / max(avg_sal, 1) * 100, 1) if avg_sal else "—"
                    st.markdown(f"""
                    <div class="card"><h4>Экономика и рынок труда</h4>
                    <div class="card-row"><span class="card-label">Средняя зарплата</span><span class="card-val">{avg_sal:,} руб./мес</span></div>
                    <div class="card-row"><span class="card-label">Аренда 1-комн. квартиры</span><span class="card-val">{rent:,} руб./мес</span></div>
                    <div class="card-row"><span class="card-label">Доля аренды от зарплаты</span><span class="card-val">{rent_pct}%</span></div>
                    <div class="card-row"><span class="card-label">ВРП на душу населения</span><span class="card-val">{reg.get('grp_per_capita_rub', 0):,} руб.</span></div>
                    <div class="card-row"><span class="card-label">Уровень безработицы</span><span class="card-val">{reg.get('unemployment_rate_percent', '—')}%</span></div>
                    <div class="card-row"><span class="card-label">Население региона</span><span class="card-val">{reg.get('population_thousands', '—')} тыс. чел.</span></div>
                    <div class="card-row"><span class="card-label">Плотность населения</span><span class="card-val">{reg.get('population_density', '—')} чел./км²</span></div>
                    <div class="card-row"><span class="card-label">Урбанизация</span><span class="card-val">{reg.get('urban_population_percent', '—')}%</span></div>
                    <div class="card-row"><span class="card-label">Инвестиции в осн. капитал</span><span class="card-val">{reg.get('investment_capital_million_rub', 0):,} млн</span></div>
                    <div class="card-row"><span class="card-label">Индекс промпроизводства</span><span class="card-val">{reg.get('industrial_production_index', '—')}%</span></div>
                    </div>""", unsafe_allow_html=True)

                    # Социальная инфраструктура
                    kg_places = reg.get('kindergarten_places_per_100',
                                        payload_sent.get('kindergarten_places_per_100', '—'))
                    st.markdown(f"""
                    <div class="card"><h4>Социальная инфраструктура</h4>
                    <div class="card-row"><span class="card-label">Профильные колледжи</span>{yn_chip(reg.get('has_college', ''))}</div>
                    <div class="card-row"><span class="card-label">Колледжей в регионе</span><span class="card-val">{reg.get('colleges_count', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Индекс качества среды</span><span class="card-val">{reg.get('quality_index', '—')} / 360</span></div>
                    <div class="card-row"><span class="card-label">Экологический класс</span><span class="card-val">{reg.get('ecology_class', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Мест в детсадах / 100 детей</span><span class="card-val">{kg_places}</span></div>
                    <div class="card-row"><span class="card-label">Мед. учреждений / 100 тыс.</span><span class="card-val">{reg.get('medical_institutions_per_100k', '—')}</span></div>
                    <div class="card-row"><span class="card-label">Розн. оборот на душу</span><span class="card-val">{reg.get('retail_turnover_per_capita_rub', 0):,} руб.</span></div>
                    """, unsafe_allow_html=True)

                    # Спортивные объекты (золотые чипсы)
                    if reg.get("sport_items"):
                        sport_chips = "".join(chip(item, "gold") for item in reg["sport_items"])
                        st.markdown(
                            f'<div class="card-row"><span class="card-label">Спортобъекты</span><div>{sport_chips}</div></div>',
                            unsafe_allow_html=True)

                    # Элементы благоустройства (золотые чипсы)
                    if reg.get("improvement_items"):
                        improve_chips = "".join(chip(item, "gold") for item in reg["improvement_items"])
                        st.markdown(
                            f'<div class="card-row"><span class="card-label">Благоустройство</span><div>{improve_chips}</div></div>',
                            unsafe_allow_html=True)

                    # Налоговые льготы
                    tax_b = reg.get("tax_benefit", 0)
                    ins_b = reg.get("insurance_benefit", 0)
                    ann_fot = cost.get("annual_fot_million_rub", 0)
                    est_profit = ann_fot * 3
                    tax_save = round(est_profit * tax_b / 100, 2)
                    ins_save = round(ann_fot * ins_b / 100, 2)
                    total_save = round(tax_save + ins_save, 2)
                    st.markdown(f"""
                    <div class="card"><h4>Налоговые льготы</h4>
                    <div class="card-row"><span class="card-label">Снижение налога на прибыль</span><span class="card-val">{tax_b} п.п. ({20 - tax_b:.1f}% вместо 20%)</span></div>
                    <div class="card-row"><span class="card-label">Льгота страх. взносов</span><span class="card-val">{ins_b}%</span></div>
                    <div class="card-row"><span class="card-label">Экономия на налоге / год</span><span class="card-val" style="color:var(--chip-g-text);">{tax_save} млн руб.</span></div>
                    <div class="card-row"><span class="card-label">Экономия на страх. / год</span><span class="card-val" style="color:var(--chip-g-text);">{ins_save} млн руб.</span></div>
                    <div class="card-row"><span class="card-label">Итого ежегодная экономия</span><span class="card-val" style="font-size:1.15rem;color:var(--gold);">{total_save} млн руб.</span></div>
                    <div style="margin-top:.8rem;padding:.7rem;background:var(--base-bg);border-radius:8px;border:1px solid var(--border);">{reg.get('tax_benefits_list', '—')}</div>
                    </div>""", unsafe_allow_html=True)

                    if reg.get("pdf_presentation_base64"):
                        st.download_button("Скачать презентацию PDF",
                                           data=base64.b64decode(reg["pdf_presentation_base64"]),
                                           file_name=f"{reg.get('site_id', 'site')}_{reg['region']}.pdf",
                                           mime="application/pdf", width='stretch')

                with col_r:
                    st.markdown('<div class="section-label">3D-модель генерального плана</div>', unsafe_allow_html=True)
                    if reg.get("three_d_html"):
                        html_content = reg["three_d_html"]
                        encoded = urllib.parse.quote(html_content, safe='')
                        st.iframe(f'data:text/html,{encoded}', height=620, width='stretch')
                    else:
                        st.info("3D-модель не загружена")

                    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
                    st.markdown('<div class="section-label">Рендеры фасадов</div>', unsafe_allow_html=True)
                    rk = f"renders_top_{idx}"
                    if st.session_state.renders.get(rk):
                        cols_r = st.columns(2)
                        for ri, img in enumerate(st.session_state.renders[rk]):
                            with cols_r[ri % 2]:
                                st.image(img, width='stretch')
                    else:
                        if st.button("Сгенерировать рендеры (4 вида)", key=f"render_{idx}", width='stretch'):
                            with st.spinner("Генерация рендеров…"):
                                rp = {
                                    "region": reg["region"],
                                    "site_name": reg.get("site_name", ""),
                                    "district": reg.get("district", ""),
                                    "concept_board": concept, "areas": areas,
                                    "employees": reg.get("employees", 90),
                                    "volume_thousand_m2": reg.get("volume_thousand_m2", 350),
                                    "housing_percent": payload_sent.get("housing_percent", 30),
                                    "housing_type": payload_sent.get("housing_type", "общежитие"),
                                    "kindergarten_places_per_100": payload_sent.get("kindergarten_places_per_100", 15),
                                    "sport_items": payload_sent.get("sport_items", []),
                                    "improvement_items": payload_sent.get("improvement_items", []),
                                    "arch_priority": payload_sent.get("arch_priority", "Техно-стиль"),
                                    "region_row": {k: reg.get(k, "") for k in
                                                   ["lat", "energy_tariff_rub_kwh", "arch_styles", "color_profile",
                                                    "steel_distance_km", "market_distance_km",
                                                    "traditional_materials"]},
                                }
                                try:
                                    resp = requests.post(f"{API}/api/renders", json=rp, timeout=180)
                                    if resp.status_code == 200:
                                        st.session_state.renders[rk] = resp.json().get("renders", [])
                                        # Запрашиваем обновлённый PDF с рендерами
                                        try:
                                            pdf_resp = requests.post(
                                                f"{API}/api/pdf_with_renders",
                                                json={
                                                    "site_id": reg.get("site_id", ""),
                                                    "region": reg["region"],
                                                    "renders": st.session_state.renders[rk],
                                                },
                                                timeout=60,
                                            )
                                            if pdf_resp.status_code == 200:
                                                pdata = pdf_resp.json()
                                                if pdata.get("pdf_base64"):
                                                    # Обновляем PDF в session_state
                                                    top_regions[idx]["pdf_presentation_base64"] = pdata["pdf_base64"]
                                                    st.session_state.api_response["top_regions"][idx]["pdf_presentation_base64"] = pdata["pdf_base64"]
                                        except Exception as pe:
                                            print(f"PDF update error: {pe}")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Ошибка рендеров: {e}")

                    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
                    if concept:
                        st.markdown('<div class="section-label">Архитектурный концепт-борд</div>',
                                    unsafe_allow_html=True)
                        cols_sw = st.columns(min(3, len(concept.get("colors", ["#333"]))))
                        for ci, clr in enumerate(concept.get("colors", [])[:3]):
                            with cols_sw[ci]:
                                st.markdown(
                                    f'<div class="color-swatch" style="background:{clr};"></div><div class="color-label">{clr}</div>',
                                    unsafe_allow_html=True)
                        if concept.get("style_description"):
                            st.markdown(
                                f'<div class="cs"><div class="ct">Стилистика</div><div>{concept["style_description"]}</div></div>',
                                unsafe_allow_html=True)
                        if concept.get("regional_features"):
                            st.markdown(
                                f'<div class="cs"><div class="ct">Интеграция в контекст региона</div><div>{concept["regional_features"]}</div></div>',
                                unsafe_allow_html=True)
                        if concept.get("materials"):
                            mats = "".join(chip(m, "b") for m in concept["materials"])
                            st.markdown(f'<div class="cs"><div class="ct">Рекомендуемые материалы</div>{mats}</div>',
                                        unsafe_allow_html=True)

                    st.markdown("<div style='height:.5rem;'></div>", unsafe_allow_html=True)
                    if ana.get("summary"):
                        st.markdown('<div class="section-label">Аналитическое заключение ИИ</div>',
                                    unsafe_allow_html=True)
                        st.markdown(
                            f'<div class="ana-box"><div class="at">Вывод по площадке</div><div>{ana["summary"]}</div></div>',
                            unsafe_allow_html=True)

    # ========== ВКЛАДКА 2: СРАВНЕНИЕ ==========
    with tab2:
        st.markdown('<div class="section-label">Детальное сравнение трёх лучших площадок</div>', unsafe_allow_html=True)
        names = [r.get("site_name", r["district"]) for r in top_regions]
        shorts = [n[:28] + ("…" if len(n) > 28 else "") for n in names]

        # Радар
        st.markdown("### Нормированное сравнение (радар-диаграмма)")
        raw_rows = []
        for reg in top_regions:
            infra = sum([1 if str(reg.get("gas_available", "")).lower() in ("да", "yes") else 0,
                         1 if str(reg.get("railway_available", "")).lower() in ("да", "yes") else 0,
                         1 if str(reg.get("industrial_park_available", "")).lower() in ("да", "yes") else 0])
            raw_rows.append({
                "Смета": reg.get("cost_data", {}).get("total_cost_million_rub", 0),
                "До стали": reg.get("steel_distance_km", 500),
                "До утеплителя": reg.get("insulation_distance_km", 500),
                "Рынок сбыта": reg.get("market_distance_km", 500),
                "Налог. льгота": reg.get("tax_benefit", 0),
                "Инфраструктура": infra,
                "Кач. среды": reg.get("quality_index", 0),
                "Зарплата": reg.get("avg_salary_rub", 0),
            })
        df_raw = pd.DataFrame(raw_rows, index=shorts)
        inv_cols = {"Смета", "До стали", "До утеплителя", "Рынок сбыта"}
        df_norm = pd.DataFrame()
        for col in df_raw.columns:
            mn, mx = df_raw[col].min(), df_raw[col].max()
            if mx > mn:
                df_norm[col] = (1 - (df_raw[col] - mn) / (mx - mn)) if col in inv_cols else (df_raw[col] - mn) / (
                            mx - mn)
            else:
                df_norm[col] = pd.Series([0.5] * len(df_raw), index=df_raw.index)
        fig_r = go.Figure()
        cats_base = list(df_norm.columns)
        for i, name in enumerate(shorts):
            vals = list(df_norm.loc[name].values) + [df_norm.loc[name].values[0]]
            cats = cats_base + [cats_base[0]]
            fig_r.add_trace(go.Scatterpolar(r=vals, theta=cats, fill="toself", name=name,
                                            line=dict(color=pc()[i], width=3), fillcolor=fc()[i], opacity=0.95))
        fig_r.update_layout(**dl(title_text="Нормированные показатели площадок", height=620),
                            polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 1])))
        st.plotly_chart(fig_r, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Смета против бюджета")
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(name="Смета проекта", x=shorts,
                               y=[r.get("cost_data", {}).get("total_cost_million_rub", 0) for r in top_regions],
                               marker=dict(color=pc()),
                               text=[f"{r.get('cost_data', {}).get('total_cost_million_rub', 0):.1f} млн" for r in
                                     top_regions],
                               textposition="outside"))
        line_color = "#1E6F9F" if dm() else "#0B2B40"
        fig_b.add_hline(y=budget_limit, line_dash="dash", line_color=line_color,
                        annotation_text=f"Бюджет: {budget_limit} млн руб.")
        fig_b.update_layout(**dl(title_text="Смета проекта vs Инвестиционный бюджет, млн руб.", height=500),
                            showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Расстояния: сырьё и рынок сбыта")
        fig_l = go.Figure()
        for (key, label), clr in zip([("steel_distance_km", "До стали"), ("insulation_distance_km", "До утеплителя"),
                                      ("market_distance_km", "Рынок сбыта")], pc()):
            fig_l.add_trace(go.Bar(name=label, x=shorts, y=[r.get(key, 0) for r in top_regions], marker_color=clr,
                                   text=[f"{r.get(key, 0)} км" for r in top_regions], textposition="outside"))
        fig_l.update_layout(**dl(title_text="Расстояния до сырья и рынка сбыта, км", height=520), barmode="group")
        st.plotly_chart(fig_l, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Экономические показатели")
        ce1, ce2, ce3 = st.columns(3)


        def _small_bar(col, vals, title, fmt="{}"):
            fig = go.Figure(go.Bar(x=shorts, y=vals, marker=dict(color=pc()), text=[fmt.format(v) for v in vals],
                                   textposition="outside"))
            fig.update_layout(**dl(title_text=title, height=400), showlegend=False)
            col.plotly_chart(fig, use_container_width=True)


        _small_bar(ce1, [r.get("tax_benefit", 0) for r in top_regions], "Налоговая льгота (%)", "{}%")
        _small_bar(ce2, [r.get("avg_salary_rub", 0) for r in top_regions], "Средняя зарплата, руб./мес", "{:,.0f}")
        _small_bar(ce3, [r.get("energy_tariff_rub_kwh", 0) for r in top_regions], "Тариф эл-эн., руб./кВт·ч", "{} руб")
        ce4, ce5, ce6 = st.columns(3)
        _small_bar(ce4, [r.get("grp_per_capita_rub", 0) for r in top_regions], "ВРП на душу нас., руб.", "{:,.0f}")
        _small_bar(ce5, [r.get("unemployment_rate_percent", 0) for r in top_regions], "Безработица, %", "{}%")
        _small_bar(ce6, [r.get("quality_index", 0) for r in top_regions], "Индекс кач. среды", "{}/360")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Детальная таблица показателей")
        cdf = pd.DataFrame(
            [{"Площадка": r.get("site_name", r["district"]), "Регион": r["region"], "Рейтинг": r["score"],
              "Смета, млн руб.": r.get("cost_data", {}).get("total_cost_million_rub", 0),
              "ФОТ/год, млн руб.": r.get("cost_data", {}).get("annual_fot_million_rub", 0),
              "До стали, км": r.get("steel_distance_km", 0), "До утеплителя, км": r.get("insulation_distance_km", 0),
              "Рынок сбыта, км": r.get("market_distance_km", 0), "Налог. льгота, %": r.get("tax_benefit", 0),
              "Страх. льгота, %": r.get("insurance_benefit", 0),
              "Тариф эл., руб./кВт·ч": r.get("energy_tariff_rub_kwh", 0),
              "Зарплата, руб./мес": r.get("avg_salary_rub", 0), "Безработица, %": r.get("unemployment_rate_percent", 0),
              "ВРП/душу, руб.": r.get("grp_per_capita_rub", 0),
              "Газ": "Да" if str(r.get("gas_available", "")).lower() in ("да", "yes") else "Нет",
              "Ж/Д": "Да" if str(r.get("railway_available", "")).lower() in ("да", "yes") else "Нет",
              "Пром. парк": "Да" if str(r.get("industrial_park_available", "")).lower() in ("да", "yes") else "Нет"} for
             r in top_regions])
        st.dataframe(cdf, use_container_width=True, hide_index=True, height=240)

    # ========== ВКЛАДКА 3: ВСЕ ВАРИАНТЫ ==========
    with tab3:
        if not all_regions:
            st.warning("Нет данных. Убедитесь, что бэкенд поддерживает /api/all_alternatives")
        else:
            st.markdown(f'<div class="section-label">Все рассмотренные площадки — {len(all_regions)} объектов</div>',
                        unsafe_allow_html=True)
            with st.expander("Фильтры и сортировка", expanded=True):
                fc1, fc2, fc3, fc4 = st.columns(4)
                with fc1:
                    max_cost = int(max((r.get("total_cost_million_rub", 0) for r in all_regions), default=1000))
                    cost_range = st.slider("Смета (млн руб.)", 0, max_cost + 1, (0, max_cost + 1), step=10)
                with fc2:
                    max_steel = int(max((r.get("steel_distance_km", 0) for r in all_regions), default=2000))
                    steel_range = st.slider("До поставщика стали (км)", 0, max_steel + 1, (0, max_steel + 1), step=50)
                with fc3:
                    gas_f = st.selectbox("Газ", ["Все", "Да", "Нет"])
                    rw_f = st.selectbox("Ж/Д", ["Все", "Да", "Нет"])
                with fc4:
                    sort_c = st.selectbox("Сортировка", ["Рейтинг — по убыванию", "Смета — по возрастанию",
                                                         "До стали — по возрастанию", "Рынок сбыта — по возрастанию",
                                                         "Налог. льгота — по убыванию"])
            flt = [r for r in all_regions if
                   cost_range[0] <= r.get("total_cost_million_rub", 0) <= cost_range[1] and steel_range[0] <= r.get(
                       "steel_distance_km", 0) <= steel_range[1]]
            if gas_f != "Все": flt = [r for r in flt if str(r.get("gas_available", "")).lower() == gas_f.lower()]
            if rw_f != "Все": flt = [r for r in flt if str(r.get("railway_available", "")).lower() == rw_f.lower()]
            sk_map = {"Рейтинг — по убыванию": ("score", True),
                      "Смета — по возрастанию": ("total_cost_million_rub", False),
                      "До стали — по возрастанию": ("steel_distance_km", False),
                      "Рынок сбыта — по возрастанию": ("market_distance_km", False),
                      "Налог. льгота — по убыванию": ("tax_benefit", True)}
            sk, sr = sk_map[sort_c]
            flt = sorted(flt, key=lambda r: r.get(sk, 0), reverse=sr)
            st.caption(f"Показано {len(flt)} из {len(all_regions)} площадок")
            if flt:
                st.markdown("### Смета vs. Рейтинг — все площадки")
                fig_s = go.Figure()
                nt3 = [r for r in flt if not r.get("in_top3")]
                t3 = [r for r in flt if r.get("in_top3")]
                fig_s.add_trace(
                    go.Scatter(x=[r.get("total_cost_million_rub", 0) for r in nt3], y=[r.get("score", 0) for r in nt3],
                               mode="markers", name="Остальные площадки", marker=dict(color="#7A8B9B", size=11),
                               text=[r.get("site_name", "") for r in nt3],
                               hovertemplate="<b>%{text}</b><br>Смета: %{x:.1f} млн<br>Рейтинг: %{y:.1f}<extra></extra>"))
                for ii, reg in enumerate(t3):
                    fig_s.add_trace(go.Scatter(x=[reg.get("total_cost_million_rub", 0)], y=[reg.get("score", 0)],
                                               mode="markers+text",
                                               name=f"#{ii + 1} {reg.get('site_name', '')}",
                                               marker=dict(color=pc()[ii % 3], size=24, symbol="star"),
                                               text=[f"#{ii + 1}"], textposition="top center"))
                line_color = "#1E6F9F" if dm() else "#0B2B40"
                fig_s.add_vline(x=budget_limit, line_dash="dash", line_color=line_color,
                                annotation_text=f"Бюджет: {budget_limit} млн")
                fig_s.update_layout(**dl(title_text="Смета vs. Рейтинг площадок (★ = Топ-3)", height=560),
                                    xaxis_title="Смета, млн руб.", yaxis_title="Рейтинг")
                st.plotly_chart(fig_s, use_container_width=True)

            st.markdown("### Полная таблица вариантов")
            df_a = pd.DataFrame([{"Площадка": r.get("site_name", r.get("district", "")), "Регион": r.get("region", ""),
                                  "Рейтинг": round(r.get("score", 0), 2), "Топ-3": "★" if r.get("in_top3") else "",
                                  "Смета, млн руб.": r.get("total_cost_million_rub", 0),
                                  "В бюджете": "Да" if r.get("total_cost_million_rub",
                                                             0) <= budget_limit else f"Нет (+{round(r.get('total_cost_million_rub', 0) - budget_limit, 0):.0f} млн)",
                                  "Газ": "Да" if str(r.get("gas_available", "")).lower() in ("да", "yes") else "Нет",
                                  "Ж/Д": "Да" if str(r.get("railway_available", "")).lower() in ("да",
                                                                                                 "yes") else "Нет",
                                  "До стали, км": r.get("steel_distance_km", 0),
                                  "До утеплителя, км": r.get("insulation_distance_km", 0),
                                  "До рынка сбыта, км": r.get("market_distance_km", 0),
                                  "Налог. льгота, %": r.get("tax_benefit", 0),
                                  "Земля, млн руб.": r.get("land_cost_million_rub", 0),
                                  "Ближ. поставщик стали": r.get("closest_steel_supplier", "")} for r in flt])
            st.dataframe(df_a, use_container_width=True, hide_index=True, height=min(60 + len(df_a) * 52, 900))
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as w:
                df_a.to_excel(w, index=False, sheet_name="Площадки")
            st.download_button("Скачать таблицу в Excel", data=out.getvalue(), file_name="all_sites.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               width='stretch')

    st.markdown(
        '<div class="footer">Наследие индустрии v4.0 · Данные: Росстат, Минстрой, реестры ОЭЗ/ТОР · newdata.csv</div>',
        unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:6rem 2rem;color:var(--text-muted);">
      <div style="font-size:5rem;margin-bottom:1.2rem;">⚙</div>
      <div style="font-size:1.7rem;font-weight:800;color:var(--text);margin-bottom:.6rem;">Заполните параметры и запустите анализ</div>
      <div style="font-size:1.05rem;max-width:520px;margin:0 auto;">Система проанализирует все площадки из базы данных и покажет лучшие 3 варианта с детальной аналитикой, 3D-моделью генплана и рендерами фасадов.</div>
    </div>""", unsafe_allow_html=True)