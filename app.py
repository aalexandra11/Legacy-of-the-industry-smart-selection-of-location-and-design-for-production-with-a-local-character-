import os
import re
import base64
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from models import InvestmentForm
from data_loader import load_regions
from calculator import calculate_areas, score_regions
from llm_service import generate_concept_board, generate_analytics
from pdf_service import create_presentation
from three_d_generator import generate_three_d_html
from render_service import get_renders, _image_cache_path, IMAGES_DIR
from fastapi.responses import FileResponse

app = FastAPI(title="Промышленное наследие РФ API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

REGIONS_DB = load_regions()

def _load_cached_renders(r: dict, concept: dict, form, areas: dict) -> list:
    """Читает рендеры с диска если они уже были сгенерированы, иначе пустой список."""
    sides = ["Юг", "Север", "Запад", "Восток"]
    region = r["region"]
    result = []
    all_found = True
    for side in sides:
        path = _image_cache_path(region, side, concept, form, r)
        if os.path.exists(path):
            with open(path, "rb") as f:
                result.append("data:image/png;base64," + base64.b64encode(f.read()).decode())
        else:
            all_found = False
            break
    if all_found and len(result) == 4:
        print(f"[app] Рендеры из кэша: {region}")
        return result
    return []


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name.strip('. ')

async def process_region(rank: int, r: dict, form: InvestmentForm, top3_list: list = None) -> dict:
    cost = r["_cost_preview"]
    areas = calculate_areas(form, cost)

    concept, analytics = await asyncio.gather(
        generate_concept_board(r["region"], form, cost, r),
        generate_analytics(r["region"], form, cost, r),
    )

    # Рендеры генерируются по кнопке через /api/renders.
    # При первичном анализе — пустые; если уже сгенерированы,
    # подхватываем их из кэша на диске для включения в PDF.
    renders = _load_cached_renders(r, concept, form, areas)

    three_d = generate_three_d_html(areas, form, concept)

    # Добавляем недостающие поля из данных региона
    quality_index = r.get("quality_index", 0)
    ecology_class = r.get("ecology_class", "—")
    rent_1room_rub = r.get("rent_1room_rub", 0)
    traditional_materials = r.get("traditional_materials", "")

    payload = {
        "rank": rank,
        "site_id": r.get("site_id", ""),
        "site_name": r.get("site_name", r.get("district", r["region"])),
        "region": r["region"],
        "district": r.get("site_name") or r.get("district", r["region"]),
        "score": round(r["score"], 2),
        "lat": r.get("lat", 55.0),
        "lon": r.get("lon", 60.0),
        "gas_available": r.get("gas_available", "Нет"),
        "free_power_kva": r.get("free_power_kva", 0),
        "railway_available": r.get("railway_available", "Нет"),
        "federal_road_distance_km": r.get("federal_road_distance_km", 0),
        "industrial_park_available": r.get("industrial_park_available", "Нет"),
        "steel_distance_km": r.get("steel_distance_km", 0),
        "insulation_distance_km": r.get("insulation_distance_km", 0),
        "market_distance_km": r.get("market_distance_km", 0),
        "steel_suppliers": r.get("steel_suppliers", ""),
        "insulation_suppliers": r.get("insulation_suppliers", ""),
        "closest_steel_supplier": r.get("closest_steel_supplier", ""),
        "closest_insulation_supplier": r.get("closest_insulation_supplier", ""),
        "steel_suppliers_list": r.get("steel_suppliers_list", []),
        "insulation_suppliers_list": r.get("insulation_suppliers_list", []),
        "tax_benefits_list": r.get("tax_benefits_list", ""),
        "tax_benefit": r.get("tax_benefit", 0),
        "insurance_benefit": r.get("insurance_benefit", 0),
        "energy_tariff_rub_kwh": r.get("energy_tariff_rub_kwh", 5.0),
        "avg_salary_rub": r.get("avg_salary_rub", 0),
        "color_profile": r.get("color_profile", ""),
        "arch_styles": r.get("arch_styles", ""),
        "employees": form.employees,
        "volume_thousand_m2": form.volume_thousand_m2,
        "budget": form.budget_million_rub,
        "housing_percent": form.housing_percent,
        "sport_items": form.sport_items,
        "improvement_items": form.improvement_items,
        "cost_data": cost,
        "areas": areas,
        "concept_board": concept,
        "analytics": analytics,
        "three_d_html": three_d,
        "renders": renders,
        "_region_row": r,
        "rejection_reasons": r.get("rejection_reasons", []),
        "form": form,
        "population_thousands": r.get("population_thousands", 0),
        "population_density": r.get("population_density_per_km2", 0),
        "urban_population_percent": r.get("urban_population_percent", 0),
        "grp_per_capita_rub": r.get("grp_per_capita_rub", 0),
        "unemployment_rate_percent": r.get("unemployment_rate_percent", 0),
        "investment_capital_million_rub": r.get("investment_capital_million_rub", 0),
        "industrial_production_index": r.get("industrial_production_index_percent", 100),
        "gasification_percent": r.get("gasification_percent", 0),
        "road_density": r.get("road_density_km_per_1000km2", 0),
        "colleges_count": r.get("colleges_count", 0),
        "medical_institutions_per_100k": r.get("medical_institutions_per_100k", 0),
        "retail_turnover_per_capita_rub": r.get("retail_turnover_per_capita_rub", 0),
        "has_college": r.get("has_college", "Нет"),
        "top3_regions": top3_list or [],
        # Новые поля для соц.блока и экономики
        "quality_index": quality_index,
        "ecology_class": ecology_class,
        "rent_1room_rub": rent_1room_rub,
        "traditional_materials": traditional_materials,
        "kindergarten_places_per_100": form.kindergarten_places_per_100,
    }

    pdf_file = f"pres_{sanitize_filename(r.get('site_id', '') + '_' + r['region'])}.pdf"
    sidecar_file = pdf_file.replace(".pdf", ".json")
    try:
        # Сохраняем сайдкар (payload без тяжёлых полей) для последующего обновления PDF с рендерами
        import json
        sidecar_data = {k: v for k, v in payload.items()
                        if k not in ("three_d_html", "renders", "pdf_presentation_base64", "form")}
        # form нельзя сериализовать напрямую — сохраняем нужные поля вручную
        sidecar_data["_form_fields"] = {
            "budget_million_rub": getattr(form, "budget_million_rub", 0),
            "housing_percent": getattr(form, "housing_percent", 0),
            "sport_items": getattr(form, "sport_items", []),
            "improvement_items": getattr(form, "improvement_items", []),
            "insulation_type": getattr(form, "insulation_type", ""),
            "housing_type": getattr(form, "housing_type", ""),
        }
        with open(sidecar_file, "w", encoding="utf-8") as sf:
            json.dump(sidecar_data, sf, ensure_ascii=False, default=str)

        create_presentation(payload, pdf_file)
        if os.path.exists(pdf_file):
            with open(pdf_file, "rb") as f:
                payload["pdf_presentation_base64"] = base64.b64encode(f.read()).decode()
        else:
            payload["pdf_presentation_base64"] = None
    except Exception:
        payload["pdf_presentation_base64"] = None

    return payload

@app.post("/api/analyze")
async def analyze(form: InvestmentForm):
    if not REGIONS_DB:
        raise HTTPException(status_code=500, detail="Нет базы регионов")

    scored = score_regions(REGIONS_DB, form)
    top_3 = scored[:3]

    # Подготовим данные о ТОП-3 для презентации
    top3_for_pdf = []
    for t in top_3:
        top3_for_pdf.append({
            "region": t.get("region"),
            "score": t.get("score"),
            "total_cost": t.get("_cost_preview", {}).get("total_cost_million_rub", 0),
            "tax_benefit": t.get("tax_benefit", 0),
            "energy_tariff": t.get("energy_tariff_rub_kwh", 0),
            "steel_distance": t.get("steel_distance_km", 0),
        })

    results = await asyncio.gather(
        *[process_region(rank, r, form, top3_for_pdf) for rank, r in enumerate(top_3, 1)],
        return_exceptions=True,
    )

    response = []
    for rank, res in enumerate(results, 1):
        if isinstance(res, Exception):
            import traceback as _tb
            print(f"[app] region {rank} failed: {res}")
            _tb.print_exc()
            # Не добавляем битую запись — клиент не упадёт с KeyError
        else:
            res.pop("_region_row", None)
            response.append(res)

    if not response:
        raise HTTPException(status_code=500, detail="Все регионы завершились с ошибкой")

    return {"success": True, "top_regions": response}

@app.get("/api/download_pdf/{site_id}")
async def download_pdf(site_id: str):
    import glob
    pattern = f"pres_{site_id}_*.pdf"
    files = glob.glob(pattern)
    if files:
        return FileResponse(files[0], media_type='application/pdf', filename=f"concept_{site_id}.pdf")
    else:
        raise HTTPException(status_code=404, detail="PDF не найден")

class PdfWithRendersRequest(BaseModel):
    site_id: str
    region: str
    renders: List[str] = []

@app.post("/api/pdf_with_renders")
async def pdf_with_renders(req: PdfWithRendersRequest):
    """Пересоздаёт PDF для нужного региона, добавляя рендеры.
    Ищет уже сохранённый payload-файл рядом с PDF (json-сайдкар) и дополняет его рендерами.
    """
    import glob, json
    pattern = f"pres_{sanitize_filename(req.site_id + '_' + req.region)}.pdf"
    sidecar = pattern.replace(".pdf", ".json")

    if not os.path.exists(sidecar):
        raise HTTPException(status_code=404, detail="Данные региона не найдены (json sidecar отсутствует)")

    with open(sidecar, "r", encoding="utf-8") as f:
        payload = json.load(f)

    payload["renders"] = req.renders

    try:
        create_presentation(payload, pattern)
        with open(pattern, "rb") as f:
            pdf_b64 = base64.b64encode(f.read()).decode()
        return {"success": True, "pdf_base64": pdf_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RenderRequest(BaseModel):
    region: str
    site_name: str = ""
    district: str = ""
    concept_board: dict
    areas: dict
    employees: int
    volume_thousand_m2: float
    housing_percent: float = 0
    housing_type: str = "общежитие"
    kindergarten_places_per_100: float = 0
    sport_items: List[str] = []
    improvement_items: List[str] = []
    arch_priority: str = "Техно-стиль"
    region_row: dict = {}

@app.post("/api/renders")
async def generate_renders(req: RenderRequest):
    class _FakeForm:
        pass
    form = _FakeForm()
    form.employees                   = req.employees
    form.volume_thousand_m2          = req.volume_thousand_m2
    form.housing_percent             = req.housing_percent
    form.housing_type                = req.housing_type
    form.kindergarten_places_per_100 = req.kindergarten_places_per_100
    form.sport_items                 = req.sport_items
    form.improvement_items           = req.improvement_items
    form.arch_priority               = req.arch_priority

    region_row = dict(req.region_row)
    region_row.setdefault("_cost_preview", {})
    region_row.setdefault("site_name", req.site_name or req.district)

    renders = await get_renders(req.region, req.concept_board, form, region_row, req.areas)
    return {"success": True, "renders": renders}

@app.post("/api/all_alternatives")
async def get_all_alternatives(form: InvestmentForm):
    if not REGIONS_DB:
        raise HTTPException(status_code=500, detail="Нет базы регионов")

    scored = score_regions(REGIONS_DB, form)

    results = []
    for rank, r in enumerate(scored, 1):
        cost = r["_cost_preview"]
        areas = calculate_areas(form, cost)

        results.append({
            "rank": rank,
            "in_top3": rank <= 3,
            "site_id": r.get("site_id", ""),
            "site_name": r.get("site_name", r.get("district", r["region"])),
            "region": r["region"],
            "district": r.get("district", r["region"]),
            "score": r["score"],
            "lat": r.get("lat", 55.0),
            "lon": r.get("lon", 60.0),
            "gas_available": r.get("gas_available", "Нет"),
            "free_power_kva": r.get("free_power_kva", 0),
            "railway_available": r.get("railway_available", "Нет"),
            "federal_road_distance_km": r.get("federal_road_distance_km", 0),
            "industrial_park_available": r.get("industrial_park_available", "Нет"),
            "steel_distance_km": r.get("steel_distance_km", 0),
            "insulation_distance_km": r.get("insulation_distance_km", 0),
            "market_distance_km": r.get("market_distance_km", 0),
            "steel_suppliers": r.get("steel_suppliers", ""),
            "insulation_suppliers": r.get("insulation_suppliers", ""),
            "closest_steel_supplier": r.get("closest_steel_supplier", ""),
            "closest_insulation_supplier": r.get("closest_insulation_supplier", ""),
            "tax_benefits_list": r.get("tax_benefits_list", ""),
            "tax_benefit": r.get("tax_benefit", 0),
            "insurance_benefit": r.get("insurance_benefit", 0),
            "energy_tariff_rub_kwh": r.get("energy_tariff_rub_kwh", 5.0),
            "avg_salary_rub": r.get("avg_salary_rub", 0),
            "color_profile": r.get("color_profile", ""),
            "arch_styles": r.get("arch_styles", ""),
            "construction_cost_index": r.get("construction_cost_index", 1.0),
            "employees": form.employees,
            "volume_thousand_m2": form.volume_thousand_m2,
            "total_cost_million_rub": cost["total_cost_million_rub"],
            "construction_million_rub": cost["construction_million_rub"],
            "logistics_million_rub": cost["logistics_million_rub"],
            "connection_million_rub": cost["connection_million_rub"],
            "power_required_kva": cost["power_required_kva"],
            "land_cost_million_rub": cost.get("land_cost_million_rub", 0),
            "scoring_breakdown": r["scoring_breakdown"],
            "rejection_reasons": r["rejection_reasons"],
            # Добавляем новые поля для отображения в таблице всех вариантов
            "quality_index": r.get("quality_index", 0),
            "ecology_class": r.get("ecology_class", "—"),
            "rent_1room_rub": r.get("rent_1room_rub", 0),
            "traditional_materials": r.get("traditional_materials", ""),
            "kindergarten_places_per_100": form.kindergarten_places_per_100,
        })

    return {"success": True, "all_regions": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)