import re
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data.csv"

def _parse_min_distance(supplier_str: str) -> float:
    if not supplier_str or pd.isna(supplier_str):
        return 500.0
    distances = [int(m) for m in re.findall(r'[–-]\s*(\d+)\s*км', str(supplier_str))]
    return float(min(distances)) if distances else 500.0

def _parse_closest_supplier_name(supplier_str: str, closest_km: float) -> str:
    if not supplier_str or pd.isna(supplier_str):
        return ""
    for part in str(supplier_str).split(";"):
        m = re.search(r'[–-]\s*(\d+)\s*км', part)
        if m and int(m.group(1)) == int(closest_km):
            return re.sub(r'\s*[–-].*', '', part).strip()
    return str(supplier_str).split(";")[0].split("–")[0].strip()

def _parse_all_suppliers(supplier_str: str) -> list[dict]:
    result = []
    if not supplier_str or pd.isna(supplier_str):
        return result
    for part in str(supplier_str).split(";"):
        part = part.strip()
        m = re.search(r'[–-]\s*(\d+)\s*км', part)
        if m:
            name = re.sub(r'\s*[–-].*', '', part).strip()
            result.append({"name": name, "distance_km": int(m.group(1))})
    return result

def _parse_tax_benefit(tax_str: str) -> float:
    if not tax_str or pd.isna(tax_str):
        return 0.0
    tax_str = str(tax_str)
    if re.search(r'\b0\s*%\s*налог\s*на\s*прибыль', tax_str, re.IGNORECASE):
        return 20.0
    rates = [float(m.replace(',', '.')) for m in re.findall(r'(\d+[.,]\d+|\d+)\s*%', tax_str)]
    if not rates:
        return 0.0
    valid = [r for r in rates if r <= 25]
    if not valid:
        return 0.0
    min_rate = min(valid)
    benefit = round(20.0 - min_rate, 2)
    return max(benefit, 0.0)

def load_regions() -> list[dict]:
    df = pd.read_csv(DATA_PATH)

    numeric_direct = [
        "energy_tariff_rub_kwh", "avg_salary_rub", "ecology_class",
        "free_power_kva", "distance_to_substation_km", "connection_cost_rub_kva",
        "kindergarten_places_per_100", "quality_index", "rent_1room_rub",
        "market_distance_km", "federal_road_distance_km", "insurance_benefit_percent",
        "lat", "lon", "construction_cost_index", "labour_cost_index",
        "population_thousands", "population_density_per_km2", "urban_population_percent",
        "grp_per_capita_rub", "unemployment_rate_percent", "investment_capital_million_rub",
        "industrial_production_index_percent", "gasification_percent",
        "road_density_km_per_1000km2", "colleges_count", "medical_institutions_per_100k",
        "retail_turnover_per_capita_rub"
    ]
    for col in numeric_direct:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ("gas_available", "has_college", "railway_available", "industrial_park_available"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    records = []
    for _, row in df.iterrows():
        r = row.to_dict()

        steel_str = str(r.get("steel_suppliers", ""))
        insul_str = str(r.get("insulation_suppliers", ""))

        steel_dist = _parse_min_distance(steel_str)
        insul_dist = _parse_min_distance(insul_str)

        r["steel_distance_km"]       = steel_dist
        r["insulation_distance_km"]  = insul_dist

        r["closest_steel_supplier"]      = _parse_closest_supplier_name(steel_str, steel_dist)
        r["closest_insulation_supplier"] = _parse_closest_supplier_name(insul_str, insul_dist)

        r["steel_suppliers_list"]      = _parse_all_suppliers(steel_str)
        r["insulation_suppliers_list"] = _parse_all_suppliers(insul_str)

        tax_str = str(r.get("tax_benefits_list", ""))
        r["tax_benefit"]   = _parse_tax_benefit(tax_str)
        r["insurance_benefit"] = float(r.get("insurance_benefit_percent", 0))

        r.setdefault("district", r.get("site_name") or r.get("region", ""))

        records.append(r)

    return records