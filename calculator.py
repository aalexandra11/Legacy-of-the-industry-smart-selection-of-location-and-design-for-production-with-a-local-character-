import math
from models import InvestmentForm

RATE = {
    "cech_sklad":    25_000,
    "abk":           40_000,
    "housing_obsh":  50_000,
    "housing_apt":   70_000,
    "kindergarten":  45_000,
    "canteen":       25_000,
    "medpunkt":      35_000,
    "roads_parking":  3_500,
    "landscaping":      800,
}

SPORT_COSTS = {
    "Стадион":            5_000_000,
    "Бассейн":            8_000_000,
    "Спортзал":           3_000_000,
    "Хоккейная коробка":  2_000_000,
    "Уличные тренажёры":    500_000,
}

STEEL_RATE  = 0.075
MARKET_RATE = 0.16

def get_climate_factor(lat: float) -> float:
    if lat > 58:
        return 1.25
    elif lat < 45:
        return 0.95
    else:
        return 1.0

def _areas(form: InvestmentForm) -> dict:
    v = form.volume_thousand_m2
    e = form.employees
    hp = form.housing_percent
    ht = getattr(form, "housing_type", "общежитие")
    kg = form.kindergarten_places_per_100

    cech_tech  = v * 8.5
    cech_staff = (e / 2) * 20
    cech = max(cech_tech + cech_staff, 500.0)

    sklad = cech * 0.35
    abk   = max(e * 5.0, 120.0)

    parking = e * 0.5 * 25
    roads   = (cech + sklad) * 0.25

    sqm = 25 if ht == "общежитие" else 40
    housing = e * (hp / 100) * sqm if hp > 0 else 0.0

    kinder = (e / 100.0 * kg * 15) if kg > 0 else 0.0

    seats = max(e * 0.4, 20)
    canteen = max(seats * 1.8, 60.0)

    med = max(e * 0.4, 40.0)

    return {
        "cech": cech, "sklad": sklad, "abk": abk,
        "parking": parking, "roads": roads,
        "housing": housing, "kindergarten": kinder,
        "canteen": canteen, "medpunkt": med,
    }

def calculate_areas(form: InvestmentForm, cost_data: dict) -> dict:
    return {k: round(v, 1) for k, v in _areas(form).items()}

def calculate_totals(region_row: dict, form: InvestmentForm) -> dict:
    a = _areas(form)
    ht = getattr(form, "housing_type", "общежитие")
    sport_items = getattr(form, "sport_items", [])

    constr_index = float(region_row.get("construction_cost_index", 1.0))
    labour_index = float(region_row.get("labour_cost_index", 1.0))
    lat = float(region_row.get("lat", 55.0))
    climate_factor = get_climate_factor(lat)

    rent = float(region_row.get("rent_1room_rub", 15000))
    base_rent = 15000.0
    rent_coef = rent / base_rent
    land_cost_ha = 3.0 * rent_coef * constr_index
    total_build_area = sum(a.values())
    land_area_ha = max(1.0, total_build_area / 10000 * 3)
    land_cost_million = land_cost_ha * land_area_ha

    h_rate = RATE["housing_obsh"] if ht == "общежитие" else RATE["housing_apt"]
    sport_rub = sum(SPORT_COSTS.get(s, 0) for s in sport_items)

    labour_part = (
        (a["cech"] + a["sklad"]) * RATE["cech_sklad"]
        + a["abk"] * RATE["abk"]
        + a["housing"] * h_rate
        + a["kindergarten"] * RATE["kindergarten"]
        + a["canteen"] * RATE["canteen"]
        + a["medpunkt"] * RATE["medpunkt"]
        + total_build_area * RATE["landscaping"]
        + sport_rub
    )
    mechanized_part = (a["parking"] + a["roads"]) * RATE["roads_parking"]
    construction_rub = (labour_part * labour_index + mechanized_part) * constr_index * climate_factor

    power_kva = max(form.volume_thousand_m2 * 2.6, 220)
    conn_cost = float(region_row.get("connection_cost_rub_kva", 6200))
    connection_rub = power_kva * conn_cost

    volume_m2 = form.volume_thousand_m2 * 1000
    steel_km = float(region_row.get("steel_distance_km", 300))
    market_km = float(region_row.get("market_distance_km", 300))
    logistics_rub = volume_m2 * (steel_km * STEEL_RATE + market_km * MARKET_RATE)

    total_mln = (construction_rub + connection_rub + logistics_rub) / 1_000_000 + land_cost_million

    hazard = "II" if getattr(form, "insulation_type", "минвата").lower() == "ппу" else "III"
    need_bus = form.employees > 110 and market_km > 170
    avg_sal = float(region_row.get("avg_salary_rub", 50_000))

    return {
        "total_cost_million_rub": round(total_mln, 2),
        "construction_million_rub": round(construction_rub / 1_000_000, 2),
        "logistics_million_rub": round(logistics_rub / 1_000_000, 2),
        "connection_million_rub": round(connection_rub / 1_000_000, 2),
        "land_cost_million_rub": round(land_cost_million, 2),
        "annual_fot_million_rub": round(form.employees * avg_sal * 12 / 1_000_000, 2),
        "power_required_kva": round(power_kva, 1),
        "hazard_class": hazard,
        "need_bus": need_bus,
        "closest_steel_supplier": region_row.get("closest_steel_supplier", ""),
        "closest_insulation_supplier": region_row.get("closest_insulation_supplier", ""),
        "steel_suppliers_list": region_row.get("steel_suppliers_list", []),
        "insulation_suppliers_list": region_row.get("insulation_suppliers_list", []),
        "tax_benefits_list": region_row.get("tax_benefits_list", ""),
        "area_cech_m2": round(a["cech"]),
        "area_sklad_m2": round(a["sklad"]),
        "area_abk_m2": round(a["abk"]),
        "area_total_m2": round(total_build_area),
        "climate_factor": round(climate_factor, 2),
        "labour_cost_index": labour_index,
    }

def score_regions(regions_list: list, form: InvestmentForm) -> list:
    scored = []
    budget = form.budget_million_rub

    for r in regions_list:
        cost = calculate_totals(r, form)
        total = cost["total_cost_million_rub"]
        score = 100.0
        breakdown = {
            "initial": 100.0,
            "budget_penalty": 0.0, "budget_bonus": 0.0, "railway_penalty": 0.0,
            "highway_penalty": 0.0, "tariff_penalty": 0.0, "power_penalty": 0.0,
            "tax_bonus": 0.0, "insurance_bonus": 0.0, "steel_logistics_penalty": 0.0,
            "insulation_logistics_penalty": 0.0, "market_penalty": 0.0,
            "gas_bonus": 0.0, "industrial_park_bonus": 0.0, "quality_bonus": 0.0,
            "college_bonus": 0.0, "ecology_bonus": 0.0, "ecology_penalty": 0.0,
            "climate_penalty": 0.0, "land_cost_penalty": 0.0,
            "unemployment_bonus": 0.0, "investment_bonus": 0.0,
            "industrial_growth_bonus": 0.0, "gasification_bonus": 0.0,
            "road_density_bonus": 0.0, "college_density_bonus": 0.0,
            "retail_activity_bonus": 0.0
        }

        if total > budget:
            overrun_pct = (total - budget) / budget * 100
            penalty = min(overrun_pct, 70)
            breakdown["budget_penalty"] = -penalty
            score -= penalty
        else:
            bonus = min((budget - total) / budget * 15, 12)
            breakdown["budget_bonus"] = bonus
            score += bonus

        if form.need_railway and str(r.get("railway_available", "Нет")).strip().lower() != "да":
            breakdown["railway_penalty"] = -35
            score -= 35

        road_dist = float(r.get("federal_road_distance_km", 15))
        if road_dist > form.max_distance_to_highway_km:
            penalty = min((road_dist - form.max_distance_to_highway_km) / 5 * 4, 25)
            breakdown["highway_penalty"] = -penalty
            score -= penalty

        tariff = float(r.get("energy_tariff_rub_kwh", 5.5))
        tariff_penalty = (tariff - 3.8) * 5.5
        if tariff_penalty > 0:
            breakdown["tariff_penalty"] = -tariff_penalty
            score -= tariff_penalty

        free_kva = float(r.get("free_power_kva", 0))
        need_kva = cost["power_required_kva"]
        if free_kva < need_kva:
            breakdown["power_penalty"] = -28
            score -= 28
        elif free_kva >= need_kva * 1.5:
            breakdown["power_penalty"] = 5
            score += 5

        raw_tax_benefit = float(r.get("tax_benefit", 0))
        overrun_pct = max(0, (total - budget) / budget * 100) if total > budget else 0
        tax_mult = max(0.0, 1.0 - overrun_pct / 100.0) if overrun_pct > 0 else 1.0
        effective_tax = raw_tax_benefit * tax_mult
        tax_bonus = effective_tax * 1.15
        breakdown["tax_bonus"] = tax_bonus
        score += tax_bonus

        raw_ins = float(r.get("insurance_benefit", 0))
        ins_mult = max(0.0, 1.0 - overrun_pct / 100.0) if overrun_pct > 0 else 1.0
        effective_ins = raw_ins * ins_mult
        if effective_ins > 0:
            ins_bonus = 10 * (effective_ins / max(raw_ins, 0.01))
            breakdown["insurance_bonus"] = ins_bonus
            score += ins_bonus

        steel_km = float(r.get("steel_distance_km", 500))
        steel_penalty = min(steel_km / 100, 12)
        breakdown["steel_logistics_penalty"] = -steel_penalty
        score -= steel_penalty

        ins_km = float(r.get("insulation_distance_km", 500))
        ins_penalty = min(ins_km / 100, 8)
        breakdown["insulation_logistics_penalty"] = -ins_penalty
        score -= ins_penalty

        mkt = float(r.get("market_distance_km", 500))
        if mkt > 500:
            mkt_penalty = min((mkt - 500) / 100 * 4, 16)
            breakdown["market_penalty"] = -mkt_penalty
            score -= mkt_penalty

        if str(r.get("gas_available", "Нет")).strip().lower() == "да":
            breakdown["gas_bonus"] = 8
            score += 8
        else:
            breakdown["gas_bonus"] = -5
            score -= 5

        if str(r.get("industrial_park_available", "Нет")).strip().lower() == "да":
            breakdown["industrial_park_bonus"] = 6
            score += 6

        quality = float(r.get("quality_index", 170))
        quality_bonus = min(quality / 22, 10)
        breakdown["quality_bonus"] = quality_bonus
        score += quality_bonus

        if str(r.get("has_college", "Нет")).strip().lower() == "да":
            breakdown["college_bonus"] = 5
            score += 5

        eco = int(float(r.get("ecology_class", 3)))
        if eco == 1:
            breakdown["ecology_bonus"] = 5
            score += 5
        elif eco >= 4:
            breakdown["ecology_penalty"] = -10
            score -= 10

        climate_factor = cost["climate_factor"]
        if climate_factor > 1.1:
            penalty = (climate_factor - 1.0) * 20
            breakdown["climate_penalty"] = -penalty
            score -= penalty

        land_cost = cost.get("land_cost_million_rub", 0)
        if land_cost > 10:
            penalty = min((land_cost - 10) * 0.5, 15)
            breakdown["land_cost_penalty"] = -penalty
            score -= penalty

        # Новые критерии
        unemployment = float(r.get("unemployment_rate_percent", 5.0))
        if unemployment < 2.5:
            unemployment_bonus = 7
        elif unemployment < 4.0:
            unemployment_bonus = 3
        elif unemployment > 8.0:
            unemployment_bonus = -5
        else:
            unemployment_bonus = 0
        breakdown["unemployment_bonus"] = unemployment_bonus
        score += unemployment_bonus

        invest_billion = float(r.get("investment_capital_million_rub", 0)) / 1000
        if invest_billion > 500:
            invest_bonus = 8
        elif invest_billion > 200:
            invest_bonus = 4
        elif invest_billion < 50:
            invest_bonus = -3
        else:
            invest_bonus = 0
        breakdown["investment_bonus"] = invest_bonus
        score += invest_bonus

        ind_growth = float(r.get("industrial_production_index_percent", 100)) - 100
        if ind_growth > 10:
            growth_bonus = 6
        elif ind_growth > 3:
            growth_bonus = 3
        elif ind_growth < -5:
            growth_bonus = -4
        else:
            growth_bonus = 0
        breakdown["industrial_growth_bonus"] = growth_bonus
        score += growth_bonus

        gasification = float(r.get("gasification_percent", 70))
        if gasification > 85:
            gasification_bonus = 6
        elif gasification > 70:
            gasification_bonus = 3
        else:
            gasification_bonus = 0
        breakdown["gasification_bonus"] = gasification_bonus
        score += gasification_bonus

        road_density = float(r.get("road_density_km_per_1000km2", 100))
        if road_density > 300:
            road_bonus = 7
        elif road_density > 200:
            road_bonus = 4
        elif road_density < 100:
            road_bonus = -3
        else:
            road_bonus = 0
        breakdown["road_density_bonus"] = road_bonus
        score += road_bonus

        colleges = float(r.get("colleges_count", 30))
        if colleges > 70:
            college_density_bonus = 6
        elif colleges > 45:
            college_density_bonus = 3
        else:
            college_density_bonus = 0
        breakdown["college_density_bonus"] = college_density_bonus
        score += college_density_bonus

        retail_per_capita = float(r.get("retail_turnover_per_capita_rub", 300000)) / 1000
        if retail_per_capita > 600:
            retail_bonus = 5
        elif retail_per_capita > 400:
            retail_bonus = 3
        else:
            retail_bonus = 0
        breakdown["retail_activity_bonus"] = retail_bonus
        score += retail_bonus

        final_score = max(round(score, 1), 0.0)

        reasons = []
        if total > budget:
            reasons.append(f"Превышение бюджета на {(total-budget)/budget*100:.1f}%")
        if breakdown["railway_penalty"] < 0:
            reasons.append("Отсутствует ж/д ветка")
        if breakdown["highway_penalty"] < 0:
            reasons.append(f"Трасса далеко ({road_dist} км)")
        if breakdown["tariff_penalty"] < 0:
            reasons.append(f"Высокий тариф ({tariff} руб/кВт·ч)")
        if breakdown["power_penalty"] < 0:
            reasons.append(f"Недостаточно мощности ({need_kva} кВА)")
        if breakdown["steel_logistics_penalty"] < -5:
            reasons.append(f"Сталь издалека ({steel_km} км)")
        if breakdown["insulation_logistics_penalty"] < -3:
            reasons.append(f"Утеплитель издалека ({ins_km} км)")
        if breakdown["market_penalty"] < 0:
            reasons.append(f"Рынок далеко ({mkt} км)")
        if breakdown["gas_bonus"] < 0:
            reasons.append("Нет газа в промзоне")
        if breakdown["climate_penalty"] < 0:
            reasons.append(f"Суровый климат (коэф. {climate_factor})")
        if unemployment_bonus < 0:
            reasons.append("Высокий уровень безработицы")
        if invest_bonus < 0:
            reasons.append("Низкая инвестиционная активность региона")
        if growth_bonus < 0:
            reasons.append("Спад промышленного производства")
        if road_bonus < 0:
            reasons.append("Низкая плотность автодорог")
        if not reasons:
            reasons.append("Соответствует всем критериям")

        r_copy = dict(r)
        r_copy["score"] = final_score
        r_copy["_cost_preview"] = cost
        r_copy["scoring_breakdown"] = breakdown
        r_copy["rejection_reasons"] = reasons
        scored.append(r_copy)

    return sorted(scored, key=lambda x: x["score"], reverse=True)