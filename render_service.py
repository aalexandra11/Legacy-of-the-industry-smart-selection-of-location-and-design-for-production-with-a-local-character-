import asyncio
import base64
import io
import os
import hashlib
from typing import List, Dict
from openai import AsyncOpenAI
from API import api_key

image_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openai.api.proxyapi.ru/v1",
)

IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

SIDE_CONTEXT = {
    "Юг":   "main entrance facade: admin building left, production hall center, warehouse right. Wide road, gate, security booth.",
    "Север": "rear facade: production hall and warehouse from back, railway loading docks.",
    "Запад": "left side: production hall wall, internal service road, utility pipes visible.",
    "Восток": "right side: warehouse and hall wall, staff parking, employee entrance.",
}

SPORT_PROMPTS = {
    "Стадион":           "outdoor stadium with bleachers",
    "Бассейн":           "indoor swimming pool building",
    "Спортзал":          "sports gymnasium building",
    "Хоккейная коробка": "outdoor ice hockey rink",
    "Уличные тренажёры": "outdoor fitness area with exercise machines",
}
IMPROVE_PROMPTS = {
    "Аллея":     "tree-lined pedestrian alley",
    "Сквер":     "small park with benches and trees",
    "Беседки":   "decorative wooden gazebos",
    "Сцена":     "outdoor amphitheatre stage",
    "Тропа":     "landscaped walking path",
    "Пруд":      "decorative pond with fountain",
    "Арт-объект": "large contemporary metal art sculpture",
}


def _image_cache_path(region: str, side: str, concept: dict, form, region_row: dict) -> str:
    """Уникальный путь файла на основе ключевых параметров."""
    key = f"{region}|{side}|{concept.get('colors',[])}|{getattr(form,'arch_priority','')}" \
          f"|{region_row.get('arch_styles','')}|{getattr(form,'sport_items',[])}|{getattr(form,'improvement_items',[])}"
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    safe_region = "".join(c if c.isalnum() else "_" for c in region)[:20]
    return os.path.join(IMAGES_DIR, f"{safe_region}_{side}_{h}.png")


def _build_prompt(region, side, concept, form, region_row, areas):
    arch_priority = getattr(form, "arch_priority", "Техно-стиль")
    sport_items   = getattr(form, "sport_items", [])
    improve_items = getattr(form, "improvement_items", [])
    colors        = concept.get("colors", ["#4a7fa5", "#8a9bb0", "#3a6a3a"])
    color_desc    = ", ".join(colors[:3])

    arch_styles   = region_row.get("arch_styles", "industrial")
    trad_mats     = region_row.get("traditional_materials", "sandwich panels, steel, glass")
    color_profile = region_row.get("color_profile", "grey, white, blue")

    lat = float(region_row.get("lat", 55))
    if lat > 57:
        climate = "snowy winter, overcast sky, frost"
    elif lat < 45:
        climate = "bright sun, green vegetation, warm"
    else:
        climate = "partly cloudy, green surroundings, golden-hour light"

    if arch_priority == "Аутентичность региону":
        arch_char = f"regional motifs: {arch_styles}. Materials: {trad_mats}. Colors: {color_profile}."
    elif arch_priority == "Техно-стиль":
        arch_char = "high-tech: glass curtain walls, steel, geometric sharp forms, futuristic."
    elif arch_priority == "Экодизайн":
        arch_char = "eco: green roofs, vertical gardens, wood accents, energy-efficient windows."
    else:
        arch_char = "modern industrial, clean lines, functional."

    extras = ""
    sport_list = [SPORT_PROMPTS[s] for s in sport_items if s in SPORT_PROMPTS]
    if sport_list:
        extras += " On site: " + "; ".join(sport_list) + "."
    imp_list = [IMPROVE_PROMPTS[i] for i in improve_items if i in IMPROVE_PROMPTS]
    if imp_list:
        extras += " Landscaping: " + "; ".join(imp_list) + "."

    cech  = areas.get("cech",  3000)
    sklad = areas.get("sklad", 1000)
    abk   = areas.get("abk",   500)

    return (
        f"Photorealistic architectural render of a sandwich-panel factory in {region}, Russia. "
        f"View: {SIDE_CONTEXT[side]} "
        f"Style: {arch_char} Colors: {color_desc}. Climate: {climate}. "
        f"Scale: hall {cech:.0f}m², warehouse {sklad:.0f}m², admin {abk:.0f}m². "
        f"{extras} "
        f"8K, eye-level, 28mm wide-angle, photorealistic shadows. No text, no people."
    ).strip()


async def _render_one(region, side, concept, form, region_row, areas):
    cache_path = _image_cache_path(region, side, concept, form, region_row)

    # Если файл уже есть на диске — отдаём его
    if os.path.exists(cache_path):
        print(f"[render_service] Cache hit: {cache_path}")
        with open(cache_path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()

    prompt = _build_prompt(region, side, concept, form, region_row, areas)
    try:
        response = await image_client.images.generate(
            model="gpt-image-2",
            prompt=prompt,
            size="1536x1024",
            quality="low",       # экономия токенов; "medium" при необходимости
            output_format="png",
            n=1,
        )
        b64 = response.data[0].b64_json
        img_bytes = base64.b64decode(b64)

        # Сохраняем на диск
        with open(cache_path, "wb") as f:
            f.write(img_bytes)
        print(f"[render_service] Saved: {cache_path}")

        return "data:image/png;base64," + b64
    except Exception as e:
        print(f"[render_service] {side} failed: {e}")
        return _make_fallback(region, side)


def _make_fallback(region, side):
    try:
        from PIL import Image, ImageDraw
        W, H = 1200, 800
        img  = Image.new("RGB", (W, H), (35, 45, 65))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, W-50, H-50], outline=(120, 160, 210), width=3)
        draw.text((80, H//2 - 20), f"{region} · {side}", fill=(200, 220, 250))
        draw.text((80, H//2 + 20), "Рендер временно недоступен", fill=(150, 170, 200))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        EMPTY = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
                 "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
        return f"data:image/png;base64,{EMPTY}"


async def get_renders(region_name, concept, form, region_row, areas):
    """Генерирует 4 рендера (Юг, Север, Запад, Восток) параллельно.
    Уже сгенерированные берёт из кэша на диске — без повторных API-вызовов.
    """
    sides = ["Юг", "Север", "Запад", "Восток"]
    tasks = [
        _render_one(region_name, s, concept, form, region_row, areas)
        for s in sides
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output = []
    for side, res in zip(sides, results):
        if isinstance(res, Exception):
            print(f"[render_service] {side} exception: {res}")
            output.append(_make_fallback(region_name, side))
        else:
            output.append(res)
    return output