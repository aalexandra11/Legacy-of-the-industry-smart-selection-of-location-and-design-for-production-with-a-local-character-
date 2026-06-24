import streamlit as st
import requests
import folium
import base64
from streamlit_folium import st_folium
from streamlit.components.v1 import html as st_html

st.set_page_config(layout="wide", page_title="Наследие индустрии", page_icon="")

st.markdown("""
<style>

/* ---------- Палитра ---------- */

:root{
    --bg:#FFFDF8;
    --sidebar:#FFF8E7;
    --card:#FFFFFF;
    --gold:#C9A227;
    --gold-dark:#A67C00;
    --border:#E7D7A5;
    --text:#1F2937;
    --text-muted:#6B7280;
}

/* ---------- Основной фон ---------- */

.stApp{
    background:var(--bg);
}

/* ---------- Текст ---------- */

html, body,
p, span, div, label,
h1,h2,h3,h4,h5,h6{
    color:var(--text);
}

/* ---------- Sidebar ---------- */

section[data-testid="stSidebar"]{
    background:var(--sidebar);
    border-right:2px solid var(--border);
}

/* ---------- KPI ---------- */

.kpi{
    background:var(--card);
    color:var(--text);
    padding:16px;
    border-radius:14px;
    border:1px solid var(--border);
    text-align:center;
    box-shadow:0 2px 8px rgba(0,0,0,.05);
    font-size:15px;
}

/* ---------- Карточки ---------- */

.metric-card{
    background:var(--card);
    color:var(--text);
    padding:18px;
    border-radius:14px;
    border:1px solid var(--border);
    margin-bottom:12px;
    box-shadow:0 2px 10px rgba(0,0,0,.05);
}

/* ---------- Кнопки ---------- */

.stButton > button{
    width:100%;
    height:3.2rem;
    background:linear-gradient(135deg, #D4AF37, #B8860B);
    color:white !important;
    border:none;
    border-radius:10px;
    font-weight:600;
}

/* ---------- Поля ---------- */

.stSelectbox,
.stNumberInput,
.stTextInput,
.stMultiSelect,
.stRadio,
.stCheckbox{
    color:var(--text);
}

/* ---------- Табы ---------- */

.stTabs [data-baseweb="tab"]{
    color:var(--text);
    font-weight:500;
}

.stTabs [aria-selected="true"]{
    color:var(--gold-dark);
    font-weight:700;
}

/* ---------- Успех ---------- */

.budget-ok{
    background:#ECFDF3;
    color:#166534;
    padding:12px;
    border-radius:10px;
    margin-bottom:10px;
}

/* ---------- Ошибка ---------- */

.budget-warn{
    background:#FEF2F2;
    color:#991B1B;
    padding:12px;
    border-radius:10px;
    margin-bottom:10px;
}

/* ---------- Expander ---------- */

.streamlit-expanderHeader{
    color:var(--text);
    font-weight:600;
}

/* ---------- Info ---------- */

[data-testid="stInfo"]{
    background:#FFF8E1;
    border-left:5px solid var(--gold);
}

/* ---------- Download ---------- */

[data-testid="stDownloadButton"] button{
    background:linear-gradient(135deg, #D4AF37, #B8860B);
    color:white !important;
}

/* ---------- Карточки KPI ---------- */

.gold-badge{
    background:#FFF5CC;
    border:1px solid #E6C65B;
    border-radius:8px;
    padding:6px 10px;
    display:inline-block;
    font-weight:600;
    color:#8B6914;
}

/* ---------- Скрытие тёмных наследуемых цветов ---------- */

[data-testid="stMarkdownContainer"] *{
    color:inherit !important;
}

</style>
""", unsafe_allow_html=True)

st.title(" Наследие индустрии")
st.subheader("Умный подбор локации для производства сэндвич-панелей на Урале")

# ── session_state ─────────────────────────────────────────────────────────────
for k, v in [("api_response", None), ("budget_at_request", 150), ("last_payload", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Сайдбар ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("️ Параметры проекта")

    col1, col2 = st.columns(2)
    with col1:
        vol = st.slider("Объём (тыс. м²/год)", 100, 1000, 350, step=50)
        emp = st.number_input("Сотрудников", 10, 200, 90, step=10)
        budget = st.number_input("Бюджет (млн ₽)", 10, 300, 160, step=10)
    with col2:
        railway = st.checkbox("Нужна Ж/Д ветка", value=False)
        highway = st.slider("Макс. до трассы (км)", 1, 100, 30)

    style = st.selectbox("Архитектурный приоритет",
                         ["Аутентичность региону", "Техно-стиль", "Экодизайн"])
    improve = st.multiselect("Благоустройство (до 3)",
                             ["Аллея", "Сквер", "Беседки", "Сцена", "Тропа", "Пруд", "Арт-объект"],
                             default=["Аллея", "Сквер"])

    st.subheader(" Социальный блок")
    h_per = st.selectbox("Жильё для сотрудников (%)", [0, 30, 50, 70], index=1)
    h_type = st.radio("Тип жилья", ["общежитие", "квартиры"])
    kg = st.selectbox("Мест в детсаду на 100 сотр.", [0, 15, 30, 50], index=1)
    sport = st.multiselect("Спортобъекты (до 2)",
                           ["Уличные тренажёры", "Стадион", "Бассейн", "Спортзал", "Хоккейная коробка"],
                           default=["Уличные тренажёры"])

    find_btn = st.button(" Найти лучшие районы")

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
    }
    # Сохраняем бюджет И payload момента запроса
    st.session_state.budget_at_request = budget
    st.session_state.last_payload = payload
    st.session_state.api_response = None  # сбрасываем старый результат

    with st.spinner("Анализируем 60 районов Урала…"):
        try:
            r = requests.post("http://127.0.0.1:8000/api/analyze", json=payload, timeout=180)
            if r.status_code == 200:
                st.session_state.api_response = r.json()
            else:
                st.error(f"Ошибка API {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Ошибка соединения: {e}")

# ── Результаты ────────────────────────────────────────────────────────────────
if st.session_state.api_response and st.session_state.api_response.get("success"):
    regions = st.session_state.api_response["top_regions"]
    budget_limit = st.session_state.budget_at_request

    if not regions:
        st.warning("Нет подходящих районов. Попробуйте увеличить бюджет или снять ограничение по Ж/Д.")
        st.stop()

    # Карта
    m = folium.Map(location=[55.0, 50.0], zoom_start=4, attributionControl=False)

    pin_colors = ["red", "blue", "green"]
    for i, reg in enumerate(regions):
        folium.Marker(
            [reg["lat"], reg["lon"]],
            popup=f"#{i + 1} {reg['district']} ({reg['region']}) — {reg['score']} баллов",
            tooltip=f"#{i + 1} {reg['district']}",
            icon=folium.Icon(color=pin_colors[i % 3]),
        ).add_to(m)
    st_folium(m, height=360, use_container_width=True)

    tabs = st.tabs([f"#{i + 1} {r['district']}" for i, r in enumerate(regions)])
    for idx, tab in enumerate(tabs):
        with tab:
            reg = regions[idx]
            cost = reg["cost_data"]
            total = cost["total_cost_million_rub"]

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"<div class='kpi'><b>Рейтинг</b><br>{reg['score']}</div>", unsafe_allow_html=True)
            with k2:
                st.markdown(f"<div class='kpi'><b>CAPEX</b><br>{total} млн ₽</div>", unsafe_allow_html=True)
            with k3:
                st.markdown("<div class='kpi'><b>Экономический эффект</b><br>Расчётный</div>", unsafe_allow_html=True)
            with k4:
                st.markdown("<div class='kpi'><b>Окупаемость</b><br>Показать</div>", unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1.3])
            with col1:
                st.subheader(f"{reg['district']}")
                st.caption(f"{reg['region']}  •  Рейтинг: {reg['score']} баллов")

                # Бюджет сравниваем с тем, что было на момент ЗАПРОСА
                if total <= budget_limit:
                    st.markdown(
                        f'<div class="budget-ok"> В бюджете: {total} млн ₽ из {budget_limit} млн ₽</div>',
                        unsafe_allow_html=True)
                else:
                    over = round(total - budget_limit, 2)
                    st.markdown(
                        f'<div class="budget-warn"> Превышение на {over} млн ₽ ({total} из {budget_limit} млн ₽)</div>',
                        unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                <h4> Смета</h4>
                Итого: <b>{total} млн ₽</b><br>
                — Строительство: {cost.get('construction_million_rub')} млн ₽<br>
                — Логистика: {cost.get('logistics_million_rub')} млн ₽<br>
                — Подключение к сетям: {cost.get('connection_million_rub')} млн ₽<br>
                Годовой ФОТ: {cost.get('annual_fot_million_rub')} млн ₽<br>
                Класс опасности: {cost.get('hazard_class')}<br>
                Транспорт: {" Нужен автобус" if cost.get('need_bus') else " Доступен"}
                </div>""", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                <h4> Экономический эффект и льготы</h4>
                Налоговые льготы: {reg.get('tax_benefit')}%<br>
                Льгота по страховым взносам: {reg.get('insurance_benefit')}%<br>
                Средняя зарплата: {reg.get('avg_salary_rub'):,} руб/мес<br>
                <hr>
                <b>Формула рейтинга:</b><br>
                Рейтинг = Инфраструктура + Логистика + Экономика + Кадры
                </div>""", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                <h4>⚡ Инфраструктура</h4>
                Газ: {reg.get('gas_available')} &nbsp;|&nbsp;
                Ж/Д: {reg.get('railway_available')}<br>
                Мощность: {reg.get('free_power_kva')} кВА (нужно: {cost.get('power_required_kva')} кВА)<br>
                До федеральной трассы: {reg.get('federal_road_distance_km')} км<br>
                Промпарк: {reg.get('industrial_park_available')}
                </div>""", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                <h4> Логистика</h4>
                До поставщика стали: {reg.get('steel_distance_km')} км<br>
                До поставщика утеплителя: {reg.get('insulation_distance_km')} км<br>
                До рынка сбыта: {reg.get('market_distance_km')} км<br>
                Энерготариф: {reg.get('energy_tariff_rub_kwh')} руб/кВт·ч
                </div>""", unsafe_allow_html=True)

                # Дублирующий блок "Экономика" УДАЛЁН

                if reg.get("analytics", {}).get("summary"):
                    st.info(reg["analytics"]["summary"])

                if reg.get("pdf_presentation_base64"):
                    st.download_button(
                        " Скачать презентацию PDF",
                        data=base64.b64decode(reg["pdf_presentation_base64"]),
                        file_name=f"{reg['district']}.pdf",
                        mime="application/pdf",
                    )

            with col2:
                concept = reg.get("concept_board", {})
                if concept:
                    st.markdown("** Концепт-борд**")
                    cc = st.columns(3)
                    for ci, color in enumerate(concept.get("colors", [])[:3]):
                        with cc[ci]:
                            st.markdown(
                                f'<div style="background:{color};height:44px;border-radius:6px;'
                                f'display:flex;align-items:center;justify-content:center;'
                                f'color:white;font-size:11px;font-weight:bold">{color}</div>',
                                unsafe_allow_html=True)
                    st.caption(concept.get("style_description", ""))
                    if concept.get("materials"):
                        st.caption(" " + " · ".join(concept.get("materials", [])))
                    if concept.get("regional_features"):
                        st.caption(" " + concept.get("regional_features", ""))

                with st.expander("Источники данных и методика"):
                    st.write("Показать объём данных, источники, критерии рейтинга и выбор Top-3.")
                with st.expander("Технологический стек и LLM"):
                    st.write("Backend, БД, GIS, LLM, генерация PDF, рендеров и 3D.")
                st.markdown("** 3D Генплан участка**")
                if reg.get("three_d_html"):
                    st_html(reg["three_d_html"], height=500, width="100%")

                if reg.get("renders"):
                    st.markdown("** Рендеры фасадов**")
                    for img in reg["renders"]:
                        st.image(img, width=650)

else:
    st.info("Заполните параметры в боковой панели и нажмите «Найти лучшие районы»")