"""
llm_service.py — расширенные промпты под newdata.csv.

Изменения:
• generate_concept_board — использует site_name, полные arch_styles,
  traditional_materials, color_profile, экологию и климат по широте.
• generate_analytics — раскрывает конкретные наименования поставщиков
  с расстояниями, полный текст tax_benefits_list, все соцэконом-индикаторы.
  Структура: 5 развёрнутых абзацев (экономика, логистика, социум, риски, рекомендации).
"""

import json
from models import InvestmentForm
from openai import AsyncOpenAI
from API import api_key

client = AsyncOpenAI(api_key=api_key, base_url="https://openai.api.proxyapi.ru/v1")


def _format_suppliers(sup_list: list) -> str:
    if not sup_list:
        return "данные отсутствуют"
    parts = [f"{s['name']} ({s['distance_km']} км)" for s in sup_list]
    return "; ".join(parts)


def _climate(lat: float) -> str:
    if lat > 59:
        return "субарктический — суровые зимы (до −35°C), короткое лето, вечная мерзлота возможна"
    if lat > 56:
        return "континентальный умеренный — зима холодная (до −25°C), лето тёплое"
    if lat < 46:
        return "тёплый субтропический — мягкая зима, жаркое лето (+35°C)"
    return "умеренно-континентальный — зима до −15°C, лето до +28°C"


async def generate_concept_board(
    region: str,
    form: InvestmentForm,
    cost_data: dict,
    region_row: dict,
):
    site_name = region_row.get("site_name") or region_row.get("district") or region
    lat = float(region_row.get("lat", 55))

    prompt = f"""
Ты — ведущий архитектор-концептуалист промышленных объектов России.
Разработай детальный архитектурный концепт завода сэндвич-панелей.

ПЛОЩАДКА: {site_name}
РЕГИОН: {region}
КЛИМАТ: {_climate(lat)}

АРХИТЕКТУРНЫЕ ТРЕБОВАНИЯ:
- Приоритет инвестора: {form.arch_priority}
- Архитектурные стили региона: {region_row.get('arch_styles', '—')}
- Традиционные материалы: {region_row.get('traditional_materials', '—')}
- Цветовой профиль региона: {region_row.get('color_profile', '—')}
- Экологический класс территории: {region_row.get('ecology_class', '—')} (1-лучший, 5-худший)
- Элементы благоустройства: {', '.join(getattr(form, 'improvement_items', [])) or 'не выбраны'}

ПРОИЗВОДСТВЕННЫЕ ПАРАМЕТРЫ:
- Объём производства: {form.volume_thousand_m2} тыс. м²/год
- Сотрудников: {form.employees} чел.
- Класс опасности объекта: {cost_data.get('hazard_class', 'III')}
- Тип утеплителя: {cost_data.get('insulation_type', 'минвата')}

ЗАДАЧА: разработай УНИКАЛЬНЫЙ концепт, органично вписывающий современное производство
в культурный и природный контекст {region}. Избегай шаблонных решений.

Верни строго JSON без markdown:
{{
  "colors": ["#HEX1", "#HEX2", "#HEX3"],
  "materials": ["материал1", "материал2", "материал3"],
  "style_description": "Развёрнутое описание стиля 4-5 предложений: как архитектура отражает дух {region}, какие исторические или природные мотивы использованы, как обеспечивается визуальная идентичность.",
  "regional_features": "2-3 предложения: конкретные архитектурные приёмы, уникальные для этого региона — орнаменты, пропорции фасадов, материалы кровли и т.д."
}}
"""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=30,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        colors_raw = region_row.get("color_profile", "серый, белый, графитовый")
        mats_raw   = region_row.get("traditional_materials", "сэндвич-панели, стекло")
        return {
            "colors": ["#334155", "#64748b", "#1e293b"],
            "materials": [m.strip() for m in mats_raw.split(",")][:3],
            "style_description": (
                f"Промышленный объект в стиле «{region_row.get('arch_styles', 'современный промышленный')}». "
                f"Цветовая палитра региона: {colors_raw}. "
                f"Фасады выполнены в традиционных материалах: {mats_raw}."
            ),
            "regional_features": f"Архитектурное решение адаптировано под климат ({_climate(lat)}) и культурный контекст {region}.",
        }


async def generate_analytics(
    region: str,
    form: InvestmentForm,
    cost_data: dict,
    region_row: dict,
):
    site_name = region_row.get("site_name") or region_row.get("district") or region

    steel_str = _format_suppliers(
        cost_data.get("steel_suppliers_list") or region_row.get("steel_suppliers_list", [])
    )
    insul_str = _format_suppliers(
        cost_data.get("insulation_suppliers_list") or region_row.get("insulation_suppliers_list", [])
    )
    tax_full = cost_data.get("tax_benefits_list") or region_row.get("tax_benefits_list", "Не указаны")
    budget_ok = cost_data["total_cost_million_rub"] <= form.budget_million_rub

    # Расчёт экономии
    ann_fot     = cost_data.get("annual_fot_million_rub", 0)
    est_profit  = ann_fot * 3
    tax_save    = round(est_profit * float(region_row.get("tax_benefit", 0)) / 100, 2)
    ins_save    = round(ann_fot * float(region_row.get("insurance_benefit", 0)) / 100, 2)
    total_save  = round(tax_save + ins_save, 2)

    avg_sal  = float(region_row.get("avg_salary_rub", 1))
    rent     = float(region_row.get("rent_1room_rub", 0))
    rent_pct = round(rent / max(avg_sal, 1) * 100, 1)

    pwr_free = float(region_row.get("free_power_kva", 0))
    pwr_need = float(cost_data.get("power_required_kva", 0))
    pwr_delta = pwr_free - pwr_need

    prompt = f"""
Ты — старший аналитик инвестиционной компании. Напиши детальное аналитическое заключение
по проекту размещения завода сэндвич-панелей. Используй ТОЛЬКО предоставленные цифры.

ОБЪЕКТ АНАЛИЗА: {site_name} ({region})

═══ ФИНАНСЫ ПРОЕКТА ═══
Бюджет инвестора: {form.budget_million_rub} млн руб.
Общая смета: {cost_data['total_cost_million_rub']} млн руб. — {'✅ УКЛАДЫВАЕТСЯ' if budget_ok else f'⚠️ ПРЕВЫШЕНИЕ на {round(cost_data["total_cost_million_rub"]-form.budget_million_rub,1)} млн'}
  • Строительство: {cost_data['construction_million_rub']} млн руб. ({round(cost_data['construction_million_rub']/max(cost_data['total_cost_million_rub'],1)*100,1)}%)
  • Логистика: {cost_data['logistics_million_rub']} млн руб. ({round(cost_data['logistics_million_rub']/max(cost_data['total_cost_million_rub'],1)*100,1)}%)
  • Подключение к сетям: {cost_data['connection_million_rub']} млн руб.
Годовой ФОТ: {ann_fot} млн руб. / Рабочих мест: {form.employees} чел.
Класс опасности: {cost_data['hazard_class']} / Нужен автобус: {'Да' if cost_data.get('need_bus') else 'Нет'}

═══ ПОСТАВЩИКИ СЫРЬЯ (конкретные данные площадки) ═══
Поставщики стали: {steel_str}
  Ближайший: {cost_data.get('closest_steel_supplier','—')} — {region_row.get('steel_distance_km','—')} км
Поставщики утеплителя: {insul_str}
  Ближайший: {cost_data.get('closest_insulation_supplier','—')} — {region_row.get('insulation_distance_km','—')} км
До рынка сбыта: {region_row.get('market_distance_km','—')} км

═══ НАЛОГОВЫЕ ЛЬГОТЫ (полный текст) ═══
{tax_full}
Расчётная ежегодная экономия: {total_save} млн руб/год
  • На налоге на прибыль: {tax_save} млн руб/год
  • На страховых взносах: {ins_save} млн руб/год

═══ ИНФРАСТРУКТУРА ПЛОЩАДКИ ═══
Газ: {region_row.get('gas_available','—')} / Уровень газификации: {region_row.get('gasification_percent','—')}%
Свободная мощность: {pwr_free} кВА (нужно: {pwr_need} кВА → {'резерв' if pwr_delta>=0 else 'дефицит'} {abs(pwr_delta):.0f} кВА)
Тариф эл-энергии: {region_row.get('energy_tariff_rub_kwh','—')} руб/кВт·ч
Ж/Д: {region_row.get('railway_available','—')} / До фед. трассы: {region_row.get('federal_road_distance_km','—')} км
Плотность дорог: {region_row.get('road_density_km_per_1000km2','—')} км/1000 км²

═══ СОЦИАЛЬНО-ЭКОНОМИЧЕСКИЙ ПАСПОРТ ═══
Население: {region_row.get('population_thousands','—')} тыс. чел. / Урбанизация: {region_row.get('urban_population_percent','—')}%
Средняя зарплата: {avg_sal:,.0f} руб/мес / Аренда 1-комн: {rent:,.0f} руб/мес ({rent_pct}% зарплаты)
Безработица: {region_row.get('unemployment_rate_percent','—')}%
ВРП на душу: {region_row.get('grp_per_capita_rub','—')} руб.
Инвестиции в осн. капитал: {region_row.get('investment_capital_million_rub','—')} млн руб.
Индекс пром. производства: {region_row.get('industrial_production_index_percent','—')}%
Индекс качества среды: {region_row.get('quality_index','—')} / 360
Профильные колледжи: {region_row.get('has_college','—')} / Колледжей в регионе: {region_row.get('colleges_count','—')}
Мест в детсадах/100 детей: {region_row.get('kindergarten_places_per_100','—')}
Мед. учреждений/100 тыс.: {region_row.get('medical_institutions_per_100k','—')}
Розн. оборот на душу: {region_row.get('retail_turnover_per_capita_rub','—')} руб.

═══ ЗАДАНИЕ ═══
Напиши аналитическое заключение из 5 развёрнутых абзацев (каждый 3-4 предложения):

1. ЭКОНОМИЧЕСКАЯ ЭФФЕКТИВНОСТЬ — бюджет, смета, налоговые льготы, расчётная экономия, ФОТ.
2. ЛОГИСТИКА И СНАБЖЕНИЕ — конкретные поставщики стали и утеплителя с расстояниями,
   логистические риски дальних поставок, анализ рынка сбыта.
3. ИНФРАСТРУКТУРА — газ, электроэнергия (достаточность мощности), транспорт, риски дефицита.
4. СОЦИАЛЬНЫЙ ПОТЕНЦИАЛ — кадры, безработица, жильё (соотношение аренды к зарплате),
   детсады, медицина, качество жизни как фактор привлечения специалистов.
5. КЛЮЧЕВЫЕ РИСКИ И РЕКОМЕНДАЦИИ — 3-4 конкретных риска и рекомендации по их митигации,
   исходя из данных выше.

Пиши деловым русским языком, конкретно, без общих фраз.
"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=35,
        )
        summary = response.choices[0].message.content.strip()
    except Exception:
        summary = (
            f"Площадка {site_name} ({region}): смета {cost_data['total_cost_million_rub']} млн руб. "
            f"{'укладывается' if budget_ok else 'превышает'} бюджет {form.budget_million_rub} млн руб. "
            f"Создаётся {form.employees} рабочих мест, годовой ФОТ — {ann_fot} млн руб. "
            f"Налоговые льготы: {tax_full}. "
            f"Ближайший поставщик стали: {cost_data.get('closest_steel_supplier','—')} "
            f"({region_row.get('steel_distance_km','—')} км). "
            f"Ежегодная экономия на льготах: {total_save} млн руб. "
            f"Энерготариф {region_row.get('energy_tariff_rub_kwh','—')} руб/кВт·ч, "
            f"газ {'доступен' if str(region_row.get('gas_available','Нет')).lower()=='да' else 'отсутствует'}."
        )

    return {
        "summary":     summary,
        "hazard_class": cost_data["hazard_class"],
        "budget_ok":    budget_ok,
    }