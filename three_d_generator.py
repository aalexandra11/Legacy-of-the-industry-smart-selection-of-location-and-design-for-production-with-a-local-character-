"""
three_d_generator.py — генератор 3D-генплана завода сэндвич-панелей.

Версия без LLM: все объекты размещаются по детерминированному алгоритму.
"""

import math
import json


# ─────────────────────────────────────────────────────────────────────────────
#  Вспомогательные расчёты размеров
# ─────────────────────────────────────────────────────────────────────────────

def _dims(area_sqm: float, ratio: float = 1.6,
          min_w: float = 8.0, max_w: float = 90.0) -> tuple[float, float]:
    if area_sqm <= 0:
        return 0.0, 0.0
    w = math.sqrt(area_sqm / ratio)
    w = max(min_w, min(w, max_w))
    d = w * ratio
    return round(w, 1), round(d, 1)


def _generate_layout(buildings_spec: list[dict]) -> dict:
    """Детерминированная компоновка зданий с гарантированными зазорами."""
    GAP = 14.0
    by_id = {b["id"]: b for b in buildings_spec}

    def get(bid):
        return by_id.get(bid, {"w": 0, "d": 0, "h": 0, "color": "#607080", "label": bid, "zone": ""})

    placed = []

    def place(bid, x, z, zone_override=None):
        b = get(bid)
        if not b["w"]:
            return
        placed.append({**b, "x": round(x, 1), "z": round(z, 1),
                       "zone": zone_override or b.get("zone", "")})

    cech = get("cech")
    sklad = get("sklad")
    place("cech", 0, 0, "производство")
    sklad_x = cech["w"] / 2 + GAP + sklad["w"] / 2
    place("sklad", sklad_x, 0, "производство")

    abk = get("abk")
    abk_z = -(cech["d"] / 2 + GAP + abk["d"] / 2)
    abk_x = -(sklad_x * 0.3)
    place("abk", abk_x, abk_z, "администрация")

    canteen = get("canteen")
    medpunkt = get("medpunkt")
    canteen_x = abk_x - abk["w"] / 2 - GAP - canteen["w"] / 2
    canteen_z = abk_z
    if canteen["w"]:
        place("canteen", canteen_x, canteen_z, "соцбыт")
    med_x = canteen_x
    med_z = canteen_z - canteen["d"] / 2 - GAP - medpunkt["d"] / 2
    if medpunkt["w"]:
        place("medpunkt", med_x, med_z, "соцбыт")

    housing = get("housing")
    kinder = get("kindergarten")
    housing_z = cech["d"] / 2 + GAP + housing["d"] / 2
    housing_x = 0.0
    if housing["w"]:
        place("housing", housing_x, housing_z, "жильё")
    kinder_x = housing_x - housing["w"] / 2 - GAP - kinder["w"] / 2
    kinder_z = housing_z
    if kinder["w"]:
        place("kindergarten", kinder_x, kinder_z, "жильё")

    sport_base_x = -(cech["w"] / 2 + GAP + 15)
    sport_base_z = cech["d"] / 2 + GAP * 0.5
    sport_ids = ["stadion", "bassein", "hockey", "gym", "sportzal", "basket", "volley"]
    sx, sz = sport_base_x, sport_base_z
    for sid in sport_ids:
        s = get(sid)
        if s["w"]:
            place(sid, sx, sz + s["d"] / 2, "спорт")
            sz += s["d"] + GAP

    park_abk_x = abk_x
    park_abk_z = abk_z - abk["d"] / 2 - GAP * 0.8 - 15
    park_housing_x = housing_x + housing["w"] / 2 + GAP + 15
    park_housing_z = housing_z

    all_pts = []
    for b in placed:
        all_pts.extend([abs(b["x"]) + b["w"] / 2, abs(b["z"]) + b["d"] / 2])
    all_pts.extend([abs(park_abk_x) + 18, abs(park_abk_z) + 15])
    site_half = max(all_pts, default=80) + GAP * 1.8
    site_size = round(site_half * 2, 0)

    return {
        "site_size": site_size,
        "buildings": placed,
        "main_road": {"from_x": 0, "to_z": abk_z},
        "parking_abk": {"x": park_abk_x, "z": park_abk_z, "w": 30, "d": 20},
        "parking_housing": {
            "x": park_housing_x, "z": park_housing_z, "w": 25, "d": 16,
            "enabled": housing["w"] > 0,
        },
    }


def _build_spec(areas: dict, form, concept: dict) -> list[dict]:
    """Формирует список зданий со всеми параметрами из areas + form."""
    SCALE = 1.4
    vol = max(float(getattr(form, "volume_thousand_m2", 10)), 1.0)
    emp = max(int(getattr(form, "employees", 50)), 1)

    colors = concept.get("colors", ["#4a7fa5", "#8a9bb0", "#3a6b3a"])
    while len(colors) < 4:
        colors.append("#607080")
    c0, c1, c2 = colors[0], colors[1], colors[2]

    def maybe(area_key, bid, label, ratio, min_w, max_w, h, color, zone):
        area = areas.get(area_key, 0)
        if area <= 0:
            return None
        w, d = _dims(area * SCALE, ratio, min_w * SCALE, max_w * SCALE)
        return {"id": bid, "w": w, "d": d, "h": round(h * SCALE, 1),
                "color": color, "label": label, "zone": zone}

    cech_h = round(max(12.0, min(24.0, 10.0 + vol * 0.35)) * SCALE, 1)
    sklad_h = round(max(8.0, min(16.0, cech_h * 0.65)), 1)
    abk_floors = max(2, min(6, emp // 35))
    abk_h = round(abk_floors * 3.5 * SCALE, 1)
    housing_floors = max(3, min(9, emp // 25))
    housing_h = round(housing_floors * 3.2 * SCALE, 1)

    spec = []
    cech_w, cech_d = _dims(areas.get("cech", 1000) * SCALE, 2.0, 18 * SCALE, 110 * SCALE)
    spec.append({"id": "cech", "w": cech_w, "d": cech_d, "h": cech_h,
                 "color": c0, "label": "Цех", "zone": "производство"})
    sklad_w, sklad_d = _dims(areas.get("sklad", 500) * SCALE, 1.8, 12 * SCALE, 85 * SCALE)
    spec.append({"id": "sklad", "w": sklad_w, "d": sklad_d, "h": sklad_h,
                 "color": c1, "label": "Склад", "zone": "производство"})
    abk_w, abk_d = _dims(areas.get("abk", 250) * SCALE, 1.4, 10 * SCALE, 55 * SCALE)
    spec.append({"id": "abk", "w": abk_w, "d": abk_d, "h": abk_h,
                 "color": c2, "label": "АБК", "zone": "администрация"})

    for item in [
        maybe("housing", "housing", "Жильё", 1.6, 12, 70, housing_h, "#c8a06a", "жильё"),
        maybe("kindergarten", "kindergarten", "Детский сад", 1.2, 8, 36, 5.5, "#f0c040", "жильё"),
        maybe("canteen", "canteen", "Столовая", 1.3, 8, 32, 5.0, "#c07a50", "соцбыт"),
        maybe("medpunkt", "medpunkt", "Медпункт", 1.1, 6, 24, 4.5, "#d8eef8", "соцбыт"),
    ]:
        if item:
            spec.append(item)

    sport_items = getattr(form, "sport_items", [])
    s = max(0.8, min(2.2, (sklad_w or 30) / 30))
    sport_map = {
        "Стадион":            ("stadion",  "Стадион",          30*s, 50*s, 1.5, "#4a8a30", "спорт"),
        "Бассейн":            ("bassein",  "Бассейн",          18*s, 28*s, 6.0, "#2299cc", "спорт"),
        "Хоккейная коробка":  ("hockey",   "Хоккейная коробка",22*s, 32*s, 1.8, "#c8e0ff", "спорт"),
        "Спортзал":           ("sportzal", "Спортзал",         14*s, 20*s, 6.0, "#c07840", "спорт"),
        "Уличные тренажёры":  ("gym",      "Тренажёры",        10*s, 12*s, 3.0, "#ff8833", "спорт"),
        "Баскетбол":          ("basket",   "Баскетбол",        15*s, 10*s, 0.5, "#8a5c3a", "спорт"),
        "Волейбол":           ("volley",   "Волейбол",         12*s,  9*s, 0.5, "#8a5c3a", "спорт"),
    }
    for sname, (sid, lbl, sw, sd, sh, sc, sz) in sport_map.items():
        if sname in sport_items:
            spec.append({"id": sid, "w": round(sw, 1), "d": round(sd, 1), "h": round(sh, 1),
                         "color": sc, "label": lbl, "zone": sz})
    return spec


# ─────────────────────────────────────────────────────────────────────────────
#  Генерация HTML (полностью детерминированная, без LLM)
# ─────────────────────────────────────────────────────────────────────────────

def generate_three_d_html(areas: dict, form, concept: dict) -> str:
    spec = _build_spec(areas, form, concept)
    layout = _generate_layout(spec)

    buildings = layout["buildings"]
    FENCE = float(layout.get("site_size", 200)) / 2
    main_road = layout.get("main_road", {"from_x": 0, "to_z": -FENCE * 0.4})
    park_abk = layout.get("parking_abk", {"x": 0, "z": -FENCE * 0.7, "w": 30, "d": 20})
    park_hous = layout.get("parking_housing", {"x": 0, "z": FENCE * 0.6, "w": 25, "d": 16, "enabled": False})

    sport_items = getattr(form, "sport_items", [])
    improve = getattr(form, "improvement_items", [])

    def jb(v): return "true" if v else "false"
    HAS_ALLEY      = jb("Аллея" in improve)
    HAS_SKVER      = jb("Сквер" in improve)
    HAS_BESEDKI    = jb("Беседки" in improve)
    HAS_SCENA      = jb("Сцена" in improve)
    HAS_TROPA      = jb("Тропа" in improve)
    HAS_POND       = jb("Пруд" in improve)
    HAS_ART        = jb("Арт-объект" in improve)
    HAS_PLAYGROUND = jb("Детская площадка" in improve)
    HAS_BASKETBALL = jb("Баскетбол" in sport_items)
    HAS_VOLLEYBALL = jb("Волейбол" in sport_items)

    # Информационная панель
    info_lines = []
    for bid, label in [("cech","Цех"),("sklad","Склад"),("abk","АБК"),
                       ("housing","Жильё"),("kindergarten","Детсад"),
                       ("canteen","Столовая"),("medpunkt","Медпункт")]:
        b = next((x for x in buildings if x["id"] == bid), None)
        if b and b.get("w"):
            area = round(b["w"] * b["d"])
            info_lines.append(f"{label}: {area} м², h={b['h']} м")
    info_html = "<br>".join(info_lines)

    buildings_js = json.dumps(buildings, ensure_ascii=False)
    park_abk_js  = json.dumps(park_abk, ensure_ascii=False)
    park_hous_js = json.dumps(park_hous, ensure_ascii=False)

    cam_dist = round(FENCE * 2.2, 1)
    cam_h    = round(FENCE * 0.9, 1)
    cam_x    = round(cam_dist * 0.65, 1)
    ground   = round(FENCE * 3.2, 0)
    grid_div = max(20, int(FENCE * 2 // 8))

    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>3D Генплан завода</title>
<style>
  body {{ margin:0; overflow:hidden; font-family:"Segoe UI",system-ui,sans-serif; }}
  #ui {{ position:absolute; top:16px; left:16px; z-index:10; pointer-events:none; }}
  #title {{ color:#1a2a40; font:700 18px/1.3 "Segoe UI",sans-serif;
            background:rgba(255,255,255,.92); border:1px solid rgba(100,140,200,.5);
            padding:12px 20px; border-radius:12px; box-shadow:0 2px 14px rgba(0,0,0,.15); }}
  #hint {{ color:#4a6080; font:12px "Segoe UI",sans-serif;
           background:rgba(255,255,255,.8); padding:6px 14px; border-radius:8px;
           margin-top:8px; box-shadow:0 1px 6px rgba(0,0,0,.1); }}
  #info {{ position:absolute; bottom:16px; right:16px; z-index:10; pointer-events:none;
           background:rgba(255,255,255,.94); border:1px solid rgba(100,140,200,.4);
           padding:12px 20px; border-radius:14px; color:#1a2848; font-size:13px;
           line-height:1.7; text-align:right; max-width:300px;
           box-shadow:0 2px 18px rgba(0,0,0,.12); }}
  #info b {{ color:#c84800; }}
  .controls-note {{ position:absolute; bottom:16px; left:16px; background:rgba(0,0,0,0.5); color:white; padding:4px 12px; border-radius:20px; font-size:11px; pointer-events:none; }}
</style>
</head>
<body>
<div id="ui">
  <div id="title">🏭 3D Генеральный план</div>
  <div id="hint">ЛКМ — вращение | ПКМ — панорама | Колесо — масштаб</div>
</div>
<div id="info">
  <b>📐 Площади и высоты</b><br>
  {info_html}
  <hr style="margin:6px 0; border-color:#c8d8e8;">
  📏 Участок: {int(FENCE*2)}×{int(FENCE*2)} м
</div>
<div class="controls-note">⚡ Управление камерой</div>

<script type="importmap">
{{"imports": {{
  "three": "https://unpkg.com/three@0.128.0/build/three.module.js",
  "three/addons/": "https://unpkg.com/three@0.128.0/examples/jsm/"
}}}}
</script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ CSS2DRenderer, CSS2DObject }} from 'three/addons/renderers/CSS2DRenderer.js';

// Данные из Python
const BUILDINGS   = {buildings_js};
const PARK_ABK    = {park_abk_js};
const PARK_HOUS   = {park_hous_js};
const FENCE       = {FENCE};
const MAIN_ROAD_X = {main_road.get("from_x", 0)};
const MAIN_ROAD_Z = {main_road.get("to_z", -FENCE*0.4)};
const HAS_ALLEY   = {HAS_ALLEY};
const HAS_SKVER   = {HAS_SKVER};
const HAS_BESEDKI = {HAS_BESEDKI};
const HAS_SCENA   = {HAS_SCENA};
const HAS_TROPA   = {HAS_TROPA};
const HAS_POND    = {HAS_POND};
const HAS_ART     = {HAS_ART};
const HAS_PLAYGROUND = {HAS_PLAYGROUND};
const HAS_BASKETBALL = {HAS_BASKETBALL};
const HAS_VOLLEYBALL = {HAS_VOLLEYBALL};

// Сцена, камера, рендереры
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xc8e0f4);
scene.fog = new THREE.Fog(0xd8ecf8, FENCE * 2.5, FENCE * 7);

const camera = new THREE.PerspectiveCamera(42, innerWidth/innerHeight, 0.5, FENCE * 18);
camera.position.set({cam_x}, {cam_h}, {cam_dist});

const renderer = new THREE.WebGLRenderer({{ antialias:true, powerPreference:"high-performance" }});
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0px';
labelRenderer.domElement.style.left = '0px';
labelRenderer.domElement.style.pointerEvents = 'none';
document.body.appendChild(labelRenderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = FENCE * 0.3;
controls.maxDistance = FENCE * 6;
controls.maxPolarAngle = Math.PI * 0.45;
controls.target.set(0, 6, 0);
controls.update();

// Освещение
scene.add(new THREE.HemisphereLight(0xb8d8f0, 0x6a8860, 0.85));
const sun = new THREE.DirectionalLight(0xfff8e8, 2.4);
sun.position.set(FENCE * 0.8, FENCE * 1.2, FENCE * 0.4);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
const sh = FENCE * 1.6;
sun.shadow.camera.left = -sh;
sun.shadow.camera.right = sh;
sun.shadow.camera.top = sh;
sun.shadow.camera.bottom = -sh;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = FENCE * 5;
sun.shadow.bias = -0.0006;
scene.add(sun);
const fill = new THREE.DirectionalLight(0x8ab4d8, 0.5);
fill.position.set(-FENCE * 0.5, FENCE * 0.5, -FENCE * 0.3);
scene.add(fill);

// Земля, асфальт, газон
const groundMat = new THREE.MeshStandardMaterial({{ color: 0x7aaa60, roughness: 0.92 }});
const ground = new THREE.Mesh(new THREE.PlaneGeometry({ground}, {ground}), groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.y = -0.08;
ground.receiveShadow = true;
scene.add(ground);

const asphaltMat = new THREE.MeshStandardMaterial({{ color: 0x3a404d, roughness: 0.96 }});
const asphalt = new THREE.Mesh(new THREE.PlaneGeometry(FENCE*2-6, FENCE*2-6), asphaltMat);
asphalt.rotation.x = -Math.PI/2;
asphalt.position.y = -0.04;
asphalt.receiveShadow = true;
scene.add(asphalt);

const grid = new THREE.GridHelper(FENCE * 2.4, {grid_div}, 0x6a88a8, 0x4a6080);
grid.position.y = -0.02;
grid.material.transparent = true;
grid.material.opacity = 0.28;
scene.add(grid);

// Вспомогательные функции
function hexInt(h) {{ return parseInt(h.replace('#',''), 16); }}
function darken(c, f) {{
  const r=Math.floor(((c>>16)&0xff)*f), g=Math.floor(((c>>8)&0xff)*f), b=Math.floor((c&0xff)*f);
  return (r<<16)|(g<<8)|b;
}}
function makeLabel(text, x, y, z, style='') {{
  const div = document.createElement('div');
  div.innerHTML = text;
  div.style.cssText = 'color:#1a2840;font:700 12px "Segoe UI",sans-serif;'
    + 'background:rgba(255,255,255,.9);border:1px solid rgba(80,120,200,.5);'
    + 'padding:4px 10px;border-radius:20px;white-space:nowrap;'
    + 'box-shadow:0 1px 8px rgba(0,0,0,.2);' + style;
  const obj = new CSS2DObject(div);
  obj.position.set(x, y, z);
  scene.add(obj);
}}
function addEdges(geo, pos, color=0x1a2030) {{
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({{ color }}));
  edges.position.copy(pos);
  scene.add(edges);
}}
function collidesRect(px, pz, rx, rz, rw, rd, margin=1.0) {{
    return (px > rx - rw/2 - margin && px < rx + rw/2 + margin &&
            pz > rz - rd/2 - margin && pz < rz + rd/2 + margin);
}}
function collidesWithAny(x, z, radius, exclusionZones) {{
    for (let zone of exclusionZones) {{
        if (collidesRect(x, z, zone.x, zone.z, zone.w, zone.d, radius)) return true;
    }}
    return false;
}}

// Запретные зоны для деревьев и кустов
const exclusionZones = [];
BUILDINGS.forEach(b => {{
    if (b.w && b.d) exclusionZones.push({{ x: b.x, z: b.z, w: b.w + 1.5, d: b.d + 1.5 }});
}});
exclusionZones.push({{ x: MAIN_ROAD_X, z: (-FENCE + MAIN_ROAD_Z)/2, w: 9, d: Math.abs(-FENCE - MAIN_ROAD_Z) + 2 }});
const fw = 6;
[[0, -FENCE+fw/2+2, FENCE*2-fw, fw], [0, FENCE-fw/2-2, FENCE*2-fw, fw],
 [-FENCE+fw/2+2, 0, fw, FENCE*2-fw], [FENCE-fw/2-2, 0, fw, FENCE*2-fw]].forEach(([x,z,w,d]) => {{
    exclusionZones.push({{ x, z, w, d }});
}});
if (PARK_ABK.w && PARK_ABK.d) exclusionZones.push({{ x: PARK_ABK.x, z: PARK_ABK.z, w: PARK_ABK.w + 2, d: PARK_ABK.d + 2 }});
if (PARK_HOUS.enabled) exclusionZones.push({{ x: PARK_HOUS.x, z: PARK_HOUS.z, w: PARK_HOUS.w + 2, d: PARK_HOUS.d + 2 }});
exclusionZones.push({{ x: 0, z: FENCE-1.2, w: FENCE*2, d: 2.5 }});
exclusionZones.push({{ x: 0, z: -FENCE+1.2, w: FENCE*2, d: 2.5 }});
exclusionZones.push({{ x: FENCE-1.2, z: 0, w: 2.5, d: FENCE*2 }});
exclusionZones.push({{ x: -FENCE+1.2, z: 0, w: 2.5, d: FENCE*2 }});

// Здания
function makeGableRoof(w, ridgeH, d, mat) {{
  const hw=w/2, hd=d/2;
  const v = new Float32Array([-hw,0,hd, hw,0,hd, 0,ridgeH,hd, -hw,0,-hd, hw,0,-hd, 0,ridgeH,-hd]);
  const idx = [0,1,2, 5,4,3, 0,2,5,0,5,3, 1,4,5,1,5,2, 0,3,4,0,4,1];
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(v,3));
  geo.setIndex(idx); geo.computeVertexNormals();
  return new THREE.Mesh(geo, mat);
}}
function makeHipRoof(w, d, ridgeH, mat) {{
  const hw=w/2, hd=d/2, rw=w*0.3;
  const v = new Float32Array([-hw,0,hd, hw,0,hd, hw,0,-hd, -hw,0,-hd, -rw/2,ridgeH,0, rw/2,ridgeH,0]);
  const idx = [0,1,5,0,5,4, 1,2,5, 2,3,4,2,4,5, 3,0,4, 3,2,1,3,1,0];
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(v,3));
  geo.setIndex(idx); geo.computeVertexNormals();
  return new THREE.Mesh(geo, mat);
}}
function addBuilding(b) {{
  const {{ id, x, z, w, d, h, color, label }} = b;
  if (!w || !d || !h) return;
  const isMain = id === 'cech';
  const col = hexInt(color);
  const roofCol = darken(col, 0.62);
  const group = new THREE.Group();
  group.position.set(x, 0, z);

  const bodyMat = new THREE.MeshStandardMaterial({{ color: col, metalness: isMain ? 0.4 : 0.2, roughness: isMain ? 0.5 : 0.7 }});
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), bodyMat);
  body.position.y = h/2;
  body.castShadow = body.receiveShadow = true;
  group.add(body);

  const plinthMat = new THREE.MeshStandardMaterial({{ color: darken(col, 0.7), roughness: 0.9 }});
  const plinth = new THREE.Mesh(new THREE.BoxGeometry(w+0.1, h*0.12, d+0.1), plinthMat);
  plinth.position.y = h*0.06;
  group.add(plinth);

  const winMat = new THREE.MeshStandardMaterial({{ color: 0xa8d8f0, metalness: 0.05, roughness: 0.03, emissive: 0x204060, emissiveIntensity: 0.2 }});
  const floors = isMain ? 1 : Math.max(1, Math.round(h / 3.8));
  const cols = Math.max(2, Math.floor(w / 5));
  const winW = Math.min(1.9, w / (cols * 2.2));
  const winH = Math.min(1.6, (h * 0.28) / floors);
  for (let fl=0; fl<floors; fl++) {{
    const wy = h * 0.22 + fl * (h * 0.72 / Math.max(floors,1));
    for (let ci=0; ci<cols; ci++) {{
      const wx = -w/2 + w/(cols+1)*(ci+1);
      const win = new THREE.Mesh(new THREE.BoxGeometry(winW, winH, 0.12), winMat);
      win.position.set(wx, wy, d/2+0.06);
      group.add(win);
      if (ci < Math.max(1, Math.floor(d/7))) {{
        const wside = new THREE.Mesh(new THREE.BoxGeometry(0.12, winH, winW), winMat);
        wside.position.set(w/2+0.06, wy, -d/2 + d/(Math.max(1,Math.floor(d/7))+1)*(ci+1));
        group.add(wside);
      }}
    }}
  }}
  const gateW = isMain ? w*0.24 : w*0.3;
  const gateH = isMain ? h*0.55 : h*0.45;
  const gateMat = new THREE.MeshStandardMaterial({{ color: 0x445566, roughness: 0.8 }});
  const gate = new THREE.Mesh(new THREE.BoxGeometry(gateW, gateH, 0.18), gateMat);
  gate.position.set(0, gateH/2, d/2+0.08);
  group.add(gate);
  const visorMat = new THREE.MeshStandardMaterial({{ color: darken(col, 0.55), metalness: 0.5 }});
  const visor = new THREE.Mesh(new THREE.BoxGeometry(gateW+1.8, 0.28, 2.6), visorMat);
  visor.position.set(0, gateH+0.18, d/2+1.3);
  visor.castShadow = true;
  group.add(visor);

  const ridgeH = isMain ? h*0.22 : h*0.18;
  const roofMat = new THREE.MeshStandardMaterial({{ color: roofCol, metalness: isMain ? 0.6 : 0.25, roughness: 0.55 }});
  const roof = isMain ? makeGableRoof(w+1.0, ridgeH, d+1.0, roofMat) : makeHipRoof(w+0.8, d+0.8, ridgeH, roofMat);
  roof.position.y = h;
  roof.castShadow = true;
  group.add(roof);

  if (isMain) {{
    const panelMat = new THREE.MeshStandardMaterial({{ color:0x1a4a88, metalness:0.92, roughness:0.12 }});
    for (let r=0; r<Math.floor(d/5); r++) for (let c=0; c<Math.floor(w/4); c++) {{
      const px = -w/2 + c*4 + 2;
      const pz = -d/2 + r*5 + 2.5;
      const panel = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.08, 4.2), panelMat);
      panel.position.set(px, h + ridgeH*0.12, pz);
      panel.rotation.x = -0.16;
      panel.castShadow = true;
      group.add(panel);
    }}
    const chimMat = new THREE.MeshStandardMaterial({{ color:0x555566, roughness:0.9 }});
    [[w*0.28, h*0.7, -d*0.28],[w*0.36, h*0.58, d*0.16]].forEach(([cx,ch,cz]) => {{
      const r1 = 0.32 + Math.random()*0.2;
      const chim = new THREE.Mesh(new THREE.CylinderGeometry(r1*0.8, r1, ch, 8), chimMat);
      chim.position.set(cx, h + ch/2, cz); chim.castShadow=true; group.add(chim);
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(r1*1.3, r1*0.9, 0.4, 8),
        new THREE.MeshStandardMaterial({{ color:0x3a3a44 }}));
      cap.position.set(cx, h+ch+0.2, cz); group.add(cap);
    }});
  }}
  scene.add(group);
  makeLabel(label, x, h + ridgeH + 2.2, z);
  addEdges(body.geometry, body.getWorldPosition(new THREE.Vector3()).add(group.position.clone().negate()).add(group.position), 0x1a2030);
}}
BUILDINGS.forEach(b => addBuilding(b));

// Постоянная инфраструктура
// Забор
function addFenceSegment(x1,z1,x2,z2) {{
  const dx=x2-x1, dz=z2-z1, len=Math.hypot(dx,dz), ang=Math.atan2(dx,dz);
  const posts = Math.max(1, Math.floor(len/3.5));
  const postMat = new THREE.MeshStandardMaterial({{ color:0xaa8866, roughness:0.85 }});
  const railMat = new THREE.MeshStandardMaterial({{ color:0xbbaa99, metalness:0.2 }});
  for (let i=0;i<=posts;i++) {{
    const t=i/posts, px=x1+dx*t, pz=z1+dz*t;
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.35,2.2,0.35), postMat);
    post.position.set(px,1.1,pz); post.castShadow=true; scene.add(post);
  }}
  [2.0,1.2].forEach(ry => {{
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.12,0.12,len), railMat);
    rail.position.set((x1+x2)/2, ry, (z1+z2)/2);
    rail.rotation.y = ang; scene.add(rail);
  }});
}}
const f = FENCE;
addFenceSegment(-f,-f, f,-f);
addFenceSegment(f,-f, f,f);
addFenceSegment(f,f, -f,f);
addFenceSegment(-f,f, -f,-f);
// Ворота
const gatePostMat = new THREE.MeshStandardMaterial({{ color:0xccaa77 }});
[[-3.5, -f], [3.5, -f]].forEach(([ox, oz]) => {{
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.6,3.6,0.6), gatePostMat);
  post.position.set(ox, 1.8, oz); scene.add(post);
  const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.28,8,6), new THREE.MeshStandardMaterial({{ color:0xffaa66, emissive:0xff4400, emissiveIntensity:0.4 }}));
  lamp.position.set(ox, 3.4, oz); scene.add(lamp);
}});
const boom = new THREE.Mesh(new THREE.BoxGeometry(6.5,0.2,0.22),
  new THREE.MeshStandardMaterial({{ color:0xff4444, metalness:0.4 }}));
boom.position.set(0, 3.5, -f); scene.add(boom);

// КПП
const kppGroup = new THREE.Group();
const kppBody = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.6, 3.2),
  new THREE.MeshStandardMaterial({{ color: 0x88aacc, roughness:0.3, metalness:0.4 }}));
kppBody.position.y = 1.3; kppBody.castShadow=true; kppGroup.add(kppBody);
const glassMat = new THREE.MeshStandardMaterial({{ color:0xaaddff, metalness:0.95, roughness:0.1, transparent:true, opacity:0.65 }});
const kppGlass = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.6, 0.08), glassMat);
kppGlass.position.set(0, 1.4, 1.62); kppGroup.add(kppGlass);
const roofKpp = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.22, 3.8),
  new THREE.MeshStandardMaterial({{ color:0x6a5a4a }}));
roofKpp.position.y = 2.75; kppGroup.add(roofKpp);
kppGroup.position.set(0, 0, -f+1.8);
scene.add(kppGroup);
makeLabel('КПП', 0, 3.5, -f+1.8, 'font-size:10px;padding:2px 6px;');

// Парковки
function addParkingComplex(px,pz,pw,pd, name) {{
  const asphaltP = new THREE.MeshStandardMaterial({{ color:0x2a303b, roughness:0.98 }});
  const lot = new THREE.Mesh(new THREE.PlaneGeometry(pw,pd), asphaltP);
  lot.rotation.x=-Math.PI/2; lot.position.set(px,-0.02,pz); lot.receiveShadow=true;
  scene.add(lot);
  const markMat = new THREE.MeshStandardMaterial({{ color:0xddddbb }});
  const rows = Math.floor(pd/5.2), cols = Math.floor(pw/2.6);
  for (let i=0;i<rows;i++) for (let j=0;j<cols;j++) {{
    const mx = px - pw/2 + (j+0.5)*2.6;
    const mz = pz - pd/2 + (i+0.5)*5.2;
    const mark = new THREE.Mesh(new THREE.PlaneGeometry(0.2,4.8), markMat);
    mark.rotation.x=-Math.PI/2; mark.position.set(mx, 0.003, mz); scene.add(mark);
  }}
  const roofMat = new THREE.MeshStandardMaterial({{ color:0x6a7a8a, metalness:0.6, roughness:0.4 }});
  const roofW = pw + 0.8;
  const roofD = pd + 0.8;
  const canopy = new THREE.Mesh(new THREE.BoxGeometry(roofW, 0.12, roofD), roofMat);
  canopy.position.set(px, 2.4, pz);
  canopy.castShadow = true;
  scene.add(canopy);
  const pillarMat = new THREE.MeshStandardMaterial({{ color:0x8899aa }});
  const pillars = [[-pw/2+1.2, -pd/2+1.2], [-pw/2+1.2, pd/2-1.2], [pw/2-1.2, -pd/2+1.2], [pw/2-1.2, pd/2-1.2]];
  pillars.forEach(([ox, oz]) => {{
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.28, 2.2, 0.28), pillarMat);
    pillar.position.set(px+ox, 1.1, pz+oz);
    pillar.castShadow = true;
    scene.add(pillar);
  }});
  const carColors = [0xcc3333,0x3399cc,0x33cc33,0xffcc00,0xaa66aa,0xcc8844];
  for (let i=0;i<rows;i++) for (let j=0;j<cols;j++) {{
    if (Math.random()<0.6) {{
      const cx = px - pw/2 + (j+0.5)*2.6;
      const cz = pz - pd/2 + (i+0.5)*5.2;
      const car = new THREE.Mesh(new THREE.BoxGeometry(1.2,0.4,2.2),
        new THREE.MeshStandardMaterial({{ color: carColors[Math.floor(Math.random()*carColors.length)], metalness:0.45, roughness:0.35 }}));
      car.position.set(cx, 0.2, cz);
      car.castShadow=true; scene.add(car);
    }}
  }}
  makeLabel(name, px, 3.5, pz);
}}
addParkingComplex(PARK_ABK.x, PARK_ABK.z, PARK_ABK.w, PARK_ABK.d, 'Парковка АБК');
if (PARK_HOUS.enabled) addParkingComplex(PARK_HOUS.x, PARK_HOUS.z, PARK_HOUS.w, PARK_HOUS.d, 'Парковка жилья');

// Остановка и автобус
const stopX = -f+5;
const stopZ = -f+4;
const stopGroup = new THREE.Group();
const roofStop = new THREE.Mesh(new THREE.BoxGeometry(3.5,0.1,2.2),
  new THREE.MeshStandardMaterial({{ color:0x8a9aaa, metalness:0.3 }}));
roofStop.position.y=2.1; stopGroup.add(roofStop);
const poleMatStop = new THREE.MeshStandardMaterial({{ color:0x6a7a8a }});
[[-1.6, -0.9], [1.6, -0.9], [-1.6, 0.9], [1.6, 0.9]].forEach(([ox, oz]) => {{
  const pole = new THREE.Mesh(new THREE.BoxGeometry(0.15,2.0,0.15), poleMatStop);
  pole.position.set(ox, 1.0, oz); stopGroup.add(pole);
}});
const bench = new THREE.Mesh(new THREE.BoxGeometry(1.8,0.3,0.8),
  new THREE.MeshStandardMaterial({{ color:0xc0a06a }}));
bench.position.set(0, 0.15, 1.0); stopGroup.add(bench);
stopGroup.position.set(stopX, 0, stopZ);
scene.add(stopGroup);
makeLabel('Остановка', stopX, 2.8, stopZ);
const busGroup = new THREE.Group();
const busBody = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.0, 6.2),
  new THREE.MeshStandardMaterial({{ color:0xdd9944, metalness:0.2 }}));
busBody.position.y=0.55; busGroup.add(busBody);
const busWindows = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.5, 5.6),
  new THREE.MeshStandardMaterial({{ color:0x88aaff, metalness:0.8, roughness:0.1 }}));
busWindows.position.y=0.85; busGroup.add(busWindows);
busGroup.position.set(stopX-4, 0.02, stopZ);
scene.add(busGroup);

// Пешеходные дорожки
const pathMat = new THREE.MeshStandardMaterial({{ color:0xc8bb99, roughness:0.88 }});
function addPath(x1,z1,x2,z2,w=1.6) {{
  const dx=x2-x1, dz=z2-z1, len=Math.hypot(dx,dz);
  const angle = Math.atan2(dz,dx);
  const path = new THREE.Mesh(new THREE.PlaneGeometry(len, w), pathMat);
  path.rotation.x = -Math.PI/2;
  path.rotation.z = angle;
  path.position.set((x1+x2)/2, -0.01, (z1+z2)/2);
  path.receiveShadow = true;
  scene.add(path);
}}
const kppPos = [0, -f+1.8];
const abkPos = [PARK_ABK.x, PARK_ABK.z];
const cechPos = [0, 0];
const housingPos = [0, FENCE*0.6];
const canteenPos = [BUILDINGS.find(b=>b.id==='canteen')?.x || -15, BUILDINGS.find(b=>b.id==='canteen')?.z || -25];
addPath(kppPos[0], kppPos[1], abkPos[0], abkPos[1], 2.0);
addPath(abkPos[0], abkPos[1], cechPos[0], cechPos[1], 2.2);
addPath(cechPos[0], cechPos[1], housingPos[0], housingPos[1], 2.0);
if (canteenPos[1]) addPath(abkPos[0], abkPos[1], canteenPos[0], canteenPos[1], 1.8);
addPath(stopX, stopZ, kppPos[0], kppPos[1], 1.5);

// Деревья, кусты, клумбы (всегда)
const treeMatTree = (color) => new THREE.MeshStandardMaterial({{ color: color, roughness:0.7 }});
const trunkMatTree = new THREE.MeshStandardMaterial({{ color:0x6a3810, roughness:0.92 }});
function addTree(x,z,sc=1) {{
  if (collidesWithAny(x, z, 1.5, exclusionZones)) return false;
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.32*sc,0.5*sc,2.0*sc,7), trunkMatTree);
  trunk.position.set(x, sc, z); trunk.castShadow=true; scene.add(trunk);
  const leafCol = [0x3a8030,0x2e6e28,0x4a9040,0x558840][Math.floor(Math.random()*4)];
  const c1 = new THREE.Mesh(new THREE.SphereGeometry(1.35*sc,8,6), treeMatTree(leafCol));
  c1.position.set(x, 3.2*sc, z); c1.castShadow=true; scene.add(c1);
  const c2 = new THREE.Mesh(new THREE.SphereGeometry(0.9*sc,6,5), treeMatTree(leafCol));
  c2.position.set(x+0.5*sc, 4.1*sc, z+0.3*sc); c2.castShadow=true; scene.add(c2);
  return true;
}}
function addBush(x,z,sc=0.7) {{
  if (collidesWithAny(x, z, 0.7, exclusionZones)) return false;
  const bushMat = new THREE.MeshStandardMaterial({{ color:0x4a8a3a, roughness:0.85 }});
  const bush = new THREE.Mesh(new THREE.SphereGeometry(0.65*sc,6,5), bushMat);
  bush.position.set(x, 0.3*sc, z); bush.castShadow=true; scene.add(bush);
  return true;
}}
for (let i=0;i<80;i++) {{
  let ang = Math.random()*Math.PI*2;
  let r = f*0.92 + (Math.random()-0.5)*2.5;
  let x = Math.cos(ang)*r, z = Math.sin(ang)*r;
  addTree(x, z, 0.85+Math.random()*0.5);
}}
for (let i=0;i<60;i++) {{
  let x = (Math.random()-0.5)*f*1.6;
  let z = (Math.random()-0.5)*f*1.6;
  if (Math.abs(x)<FENCE*0.9 && Math.abs(z)<FENCE*0.9) {{
    addTree(x, z, 0.9+Math.random()*0.6);
  }}
}}
for (let i=0;i<45;i++) {{
  let x = (Math.random()-0.5)*f*1.5;
  let z = (Math.random()-0.5)*f*1.5;
  if (Math.abs(x)<FENCE*0.95 && Math.abs(z)<FENCE*0.95) addBush(x, z, 0.6+Math.random()*0.5);
}}
function addFlowerBed(x,z,w,d) {{
  if (collidesWithAny(x, z, w/2+0.5, exclusionZones)) return;
  const soil = new THREE.Mesh(new THREE.BoxGeometry(w,0.1,d),
    new THREE.MeshStandardMaterial({{ color:0x6a4a2a }}));
  soil.position.set(x, 0, z); soil.receiveShadow=true; scene.add(soil);
  const flowerMat = new THREE.MeshStandardMaterial({{ color:0xff44aa }});
  for (let i=0;i<12;i++) {{
    const fx = x + (Math.random()-0.5)*(w-0.6);
    const fz = z + (Math.random()-0.5)*(d-0.6);
    const flower = new THREE.Mesh(new THREE.SphereGeometry(0.12,5,4), flowerMat);
    flower.position.set(fx, 0.15, fz); scene.add(flower);
  }}
}}
const flowerZones = [[-25, -30, 4,3], [15, -18, 3,2.5], [-10, 32, 3.5,3], [28, 22, 3,3], [0, -42, 5,3]];
flowerZones.forEach(([x,z,w,d]) => addFlowerBed(x,z,w,d));
if (HAS_POND) {{
  const water = new THREE.Mesh(new THREE.CylinderGeometry(5.8,5.8,0.18,32),
    new THREE.MeshStandardMaterial({{ color:0x1a7acc, roughness:0.05, metalness:0.6, emissive:0x003366, emissiveIntensity:0.3 }}));
  water.position.set(-f*0.22, -0.01, f*0.72); scene.add(water);
}}

// Фонари (всегда)
const lampH = Math.max(5.2, f*0.085);
const lampSp = Math.max(22, f*0.3);
const poleMatLight = new THREE.MeshStandardMaterial({{ color:0x889aaa, metalness:0.7 }});
function addLamp(x,z) {{
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.16,0.22, lampH, 7), poleMatLight);
  pole.position.set(x, lampH/2, z); pole.castShadow=true; scene.add(pole);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.09,0.09, 1.6, 5), poleMatLight);
  arm.rotation.z = Math.PI/2;
  arm.position.set(x+0.8, lampH-0.2, z); scene.add(arm);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.65,0.28,0.52),
    new THREE.MeshStandardMaterial({{ color:0xffe8a0, emissive:0xffcc44, emissiveIntensity:0.55 }}));
  head.position.set(x+1.6, lampH-0.28, z); scene.add(head);
  const light = new THREE.PointLight(0xfff0cc, 0.55, f*0.45);
  light.position.set(x+1.6, lampH-0.28, z); scene.add(light);
}}
const lampCoords = [];
for (let x=-f+8; x<=f-8; x+=lampSp) for (let z=-f+8; z<=f-8; z+=lampSp) {{
  if (Math.hypot(x,z) > f-6) continue;
  lampCoords.push([x,z]);
}}
lampCoords.forEach(([x,z]) => addLamp(x,z));

// Пользовательские элементы (только если выбраны)
if (HAS_ALLEY) {{
  for (let t=-f*0.7; t<=f*0.7; t+=f*0.1) {{
    addTree(t, -f*0.3, 1.0);
    addTree(t, f*0.25, 1.0);
  }}
}}
if (HAS_SKVER) {{
  for (let sx of [-18,0,18]) for (let sz of [f*0.55, f*0.62]) addTree(sx, sz, 1.2);
  const benchMat = new THREE.MeshStandardMaterial({{ color:0x9a7a4a }});
  const benchSeat = new THREE.Mesh(new THREE.BoxGeometry(2.2,0.2,0.5), benchMat);
  benchSeat.position.set(0, 0.1, f*0.58); scene.add(benchSeat);
}}
if (HAS_BESEDKI) {{
  function addGazebo(x,z) {{
    const base = new THREE.Mesh(new THREE.CylinderGeometry(2.2,2.2,0.24,8),
      new THREE.MeshStandardMaterial({{ color:0xc4a06c }}));
    base.position.set(x,0.12,z); scene.add(base);
    for (let i=0;i<6;i++) {{
      const a=i/6*Math.PI*2;
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.13,0.13,2.4,6),
        new THREE.MeshStandardMaterial({{ color:0xc4a06c }}));
      col.position.set(x+Math.cos(a)*1.85, 1.2, z+Math.sin(a)*1.85);
      col.castShadow=true; scene.add(col);
    }}
    const roof = new THREE.Mesh(new THREE.ConeGeometry(2.5,1.8,8),
      new THREE.MeshStandardMaterial({{ color:0xaa6640, metalness:0.12 }}));
    roof.position.set(x,2.8,z); roof.castShadow=true; scene.add(roof);
  }}
  addGazebo(-f*0.55, -f*0.28);
  addGazebo(f*0.55, f*0.38);
}}
if (HAS_SCENA) {{
  const sm = new THREE.MeshStandardMaterial({{ color:0xbb9960 }});
  const stage = new THREE.Mesh(new THREE.BoxGeometry(12,0.55,8), sm);
  stage.position.set(f*0.6, 0.27, -f*0.32); stage.castShadow=true; scene.add(stage);
  makeLabel('Сцена', f*0.6, 2.5, -f*0.32);
}}
if (HAS_TROPA) {{
  const pts = [
    new THREE.Vector3(-f*0.3, 0, -f*0.18),
    new THREE.Vector3(0, 0, -f*0.22),
    new THREE.Vector3(f*0.3, 0, -f*0.18),
  ];
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.7, 7, false),
    new THREE.MeshStandardMaterial({{ color:0xaa9977, roughness:0.92 }})
  );
  tube.receiveShadow=true; scene.add(tube);
}}
if (HAS_ART) {{
  const art = new THREE.Mesh(new THREE.SphereGeometry(1.6,24,18),
    new THREE.MeshStandardMaterial({{ color:0xff6600, metalness:0.85, roughness:0.15, emissive:0x441100 }}));
  art.position.set(f*0.1, 1.6, f*0.82); art.castShadow=true; scene.add(art);
  makeLabel('Арт-объект', f*0.1, 4.0, f*0.82);
}}
if (HAS_PLAYGROUND) {{
  const playgroundX = -f+12;
  const playgroundZ = f-12;
  if (!collidesWithAny(playgroundX, playgroundZ, 3, exclusionZones)) {{
    const sand = new THREE.Mesh(new THREE.PlaneGeometry(5,5),
      new THREE.MeshStandardMaterial({{ color:0xe8d8a0, roughness:0.98 }}));
    sand.rotation.x = -Math.PI/2;
    sand.position.set(playgroundX, -0.01, playgroundZ);
    sand.receiveShadow = true;
    scene.add(sand);
    const swingBase = new THREE.Mesh(new THREE.BoxGeometry(3.2, 1.8, 0.2),
      new THREE.MeshStandardMaterial({{ color:0xccaa88 }}));
    swingBase.position.set(playgroundX, 0.9, playgroundZ+0.8); scene.add(swingBase);
    const slide = new THREE.Mesh(new THREE.CylinderGeometry(0.5,0.9,1.2,6),
      new THREE.MeshStandardMaterial({{ color:0xdd6644 }}));
    slide.position.set(playgroundX+1.2, 0.6, playgroundZ-1.2); scene.add(slide);
    makeLabel('Детская площадка', playgroundX, 2.2, playgroundZ, 'font-size:9px;');
  }}
}}
if (HAS_BASKETBALL) {{
  const bx = -f+15, bz = -f+12;
  if (!collidesWithAny(bx, bz, 8, exclusionZones)) {{
    const courtMat = new THREE.MeshStandardMaterial({{ color:0x4a6a3a, roughness:0.98 }});
    const court = new THREE.Mesh(new THREE.PlaneGeometry(12, 8), courtMat);
    court.rotation.x = -Math.PI/2;
    court.position.set(bx, -0.02, bz);
    court.receiveShadow = true;
    scene.add(court);
    const lineMat = new THREE.MeshStandardMaterial({{ color:0xffffff }});
    const line = new THREE.Mesh(new THREE.BoxGeometry(11.2, 0.05, 0.1), lineMat);
    line.position.set(bx, 0.02, bz + 3.8);
    scene.add(line);
    makeLabel('Баскетбол', bx, 0.5, bz);
  }}
}}
if (HAS_VOLLEYBALL) {{
  const vx = f-18, vz = -f+10;
  if (!collidesWithAny(vx, vz, 6, exclusionZones)) {{
    const courtMat = new THREE.MeshStandardMaterial({{ color:0x4a6a3a, roughness:0.98 }});
    const court = new THREE.Mesh(new THREE.PlaneGeometry(10, 7), courtMat);
    court.rotation.x = -Math.PI/2;
    court.position.set(vx, -0.02, vz);
    court.receiveShadow = true;
    scene.add(court);
    makeLabel('Волейбол', vx, 0.5, vz);
  }}
}}

// Анимация
function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}}
animate();
window.addEventListener('resize', () => {{
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  labelRenderer.setSize(innerWidth, innerHeight);
}});
</script>
</body>
</html>'''
    return html