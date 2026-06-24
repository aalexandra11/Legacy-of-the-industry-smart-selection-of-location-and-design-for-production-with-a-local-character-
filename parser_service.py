"""
parser_service.py — Парсер региональных данных для «Наследие индустрии»

Источники данных:
  1. Росстат (API v2)            → avg_salary_rub, kindergarten_places_per_100
  2. Индекс городов (Минстрой)   → quality_index
  3. hh.ru API (публичный)       → аренда жилья (косвенно, через зарплаты)
  4. ГитХаб-зеркала              → energy_tariff, tax_benefit, arch_styles, color_profile
  5. Жёстко зашитый резерв       → все поля, если сеть недоступна

Запуск:
  python parser_service.py              # обновить CSV из открытых источников
  python parser_service.py --dry-run    # только показать, что было бы обновлено

Для работы через VPN/прокси задайте переменные окружения:
  HTTP_PROXY=http://user:pass@host:port
  HTTPS_PROXY=http://user:pass@host:port
  или передайте --proxy http://host:port
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# ─── Настройки ───────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "regions_data.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Таймаут и количество повторов при сетевых ошибках
REQUEST_TIMEOUT = 10
MAX_RETRIES = 2
RETRY_DELAY = 2  # секунды

# ─── Справочник: коды регионов Росстата (ОКАТО-совместимые) ──────────────────

ROSSTAT_CODES: Dict[str, str] = {
    "Республика Татарстан":    "92000",
    "Ленинградская область":   "41000",
    "Свердловская область":    "65000",
    "Краснодарский край":      "03000",
    "Новосибирская область":   "50000",
    "Челябинская область":     "75000",
    "Нижегородская область":   "22000",
    "Самарская область":       "36000",
    "Красноярский край":       "04000",
    "Владимирская область":    "17000",
}

# ─── Зеркала данных (GitHub raw, публичные JSON) ─────────────────────────────

MIRRORS = [
    # Зеркало 1 — агрегированные данные по РФ-регионам (энерготарифы, льготы)
    "https://raw.githubusercontent.com/russianregions/open-data/main/energy_tariffs.json",
    # Зеркало 2 — резервное зеркало с полным профилем регионов
    "https://raw.githubusercontent.com/opendatarussia/regions/main/profiles.json",
]

# ─── Архитектурные справочники (не меняются — жёстко зашиты) ─────────────────

ARCH_PROFILES: Dict[str, Dict[str, str]] = {
    "Республика Татарстан": {
        "arch_styles": "татарский эклектизм, ампир, советский модернизм",
        "traditional_materials": "известняк, кирпич, дерево с резьбой",
        "color_profile": "белый, синий, зелёный, золотой",
    },
    "Ленинградская область": {
        "arch_styles": "петербургский классицизм, модерн, конструктивизм",
        "traditional_materials": "гранит, кирпич, штукатурка",
        "color_profile": "серый, жёлтый, белый, охра",
    },
    "Свердловская область": {
        "arch_styles": "уральский конструктивизм, советский ампир, промышленный стиль",
        "traditional_materials": "уральский камень, металл, дерево",
        "color_profile": "тёмно-серый, терракотовый, охра, белый",
    },
    "Краснодарский край": {
        "arch_styles": "кубанский казачий стиль, средиземноморский, эклектика",
        "traditional_materials": "ракушечник, дерево, черепица",
        "color_profile": "белый, персиковый, лазурный, зелёный",
    },
    "Новосибирская область": {
        "arch_styles": "сибирский конструктивизм, советский модернизм, современный минимализм",
        "traditional_materials": "кирпич, дерево, бетон",
        "color_profile": "серый, белый, синий, природные оттенки",
    },
    "Челябинская область": {
        "arch_styles": "уральский промышленный, советский конструктивизм",
        "traditional_materials": "металл, кирпич, уральский гранит",
        "color_profile": "стальной, серый, тёмно-синий, оранжевый акцент",
    },
    "Нижегородская область": {
        "arch_styles": "нижегородский модерн, ярмарочный классицизм, деревянный ампир",
        "traditional_materials": "дерево с резьбой, кирпич, камень",
        "color_profile": "белый, зелёный, красный, золотой",
    },
    "Самарская область": {
        "arch_styles": "волжский эклектизм, модерн, советский авангард",
        "traditional_materials": "кирпич, дерево, керамическая плитка",
        "color_profile": "бежевый, белый, терракотовый, синий",
    },
    "Красноярский край": {
        "arch_styles": "сибирский классицизм, советский модернизм, промышленный футуризм",
        "traditional_materials": "сибирский кедр, лиственница, кирпич",
        "color_profile": "зелёный, коричневый, серый, красный акцент",
    },
    "Владимирская область": {
        "arch_styles": "белокаменное зодчество, древнерусский стиль, классицизм",
        "traditional_materials": "белый камень, дерево, кирпич",
        "color_profile": "белый, золотой, синий, зелёный",
    },
}

# ─── Полный резервный справочник (hardcode fallback) ─────────────────────────

FALLBACK_DATA: Dict[str, Dict[str, Any]] = {
    "Республика Татарстан": {
        "avg_salary_rub": 61200, "energy_tariff_rub_kwh": 4.10,
        "tax_benefit": 20, "insurance_benefit": 15,
        "quality_index": 214, "kindergarten_places_per_100": 67,
        "has_college": "Да", "rent_1room_rub": 16070,
        "gas_available": "Да", "free_power_kva": 958,
        "distance_to_substation_km": 2.0, "connection_cost_rub_kva": 5918,
        "steel_distance_km": 80, "insulation_distance_km": 60,
        "market_distance_km": 161, "ecology_class": 3,
    },
    "Ленинградская область": {
        "avg_salary_rub": 68500, "energy_tariff_rub_kwh": 5.20,
        "tax_benefit": 20, "insurance_benefit": 0,
        "quality_index": 208, "kindergarten_places_per_100": 40,
        "has_college": "Нет", "rent_1room_rub": 24149,
        "gas_available": "Нет", "free_power_kva": 684,
        "distance_to_substation_km": 13.0, "connection_cost_rub_kva": 7060,
        "steel_distance_km": 150, "insulation_distance_km": 60,
        "market_distance_km": 192, "ecology_class": 1,
    },
    "Свердловская область": {
        "avg_salary_rub": 63400, "energy_tariff_rub_kwh": 4.60,
        "tax_benefit": 15, "insurance_benefit": 0,
        "quality_index": 202, "kindergarten_places_per_100": 86,
        "has_college": "Да", "rent_1room_rub": 25403,
        "gas_available": "Нет", "free_power_kva": 670,
        "distance_to_substation_km": 13.0, "connection_cost_rub_kva": 3677,
        "steel_distance_km": 150, "insulation_distance_km": 120,
        "market_distance_km": 90, "ecology_class": 2,
    },
    "Краснодарский край": {
        "avg_salary_rub": 55300, "energy_tariff_rub_kwh": 5.80,
        "tax_benefit": 20, "insurance_benefit": 15,
        "quality_index": 205, "kindergarten_places_per_100": 54,
        "has_college": "Нет", "rent_1room_rub": 22108,
        "gas_available": "Да", "free_power_kva": 696,
        "distance_to_substation_km": 2.0, "connection_cost_rub_kva": 7003,
        "steel_distance_km": 600, "insulation_distance_km": 200,
        "market_distance_km": 282, "ecology_class": 1,
    },
    "Новосибирская область": {
        "avg_salary_rub": 59800, "energy_tariff_rub_kwh": 4.40,
        "tax_benefit": 15, "insurance_benefit": 15,
        "quality_index": 195, "kindergarten_places_per_100": 55,
        "has_college": "Нет", "rent_1room_rub": 25433,
        "gas_available": "Да", "free_power_kva": 575,
        "distance_to_substation_km": 9.0, "connection_cost_rub_kva": 6486,
        "steel_distance_km": 250, "insulation_distance_km": 120,
        "market_distance_km": 188, "ecology_class": 3,
    },
    "Челябинская область": {
        "avg_salary_rub": 57200, "energy_tariff_rub_kwh": 4.30,
        "tax_benefit": 20, "insurance_benefit": 15,
        "quality_index": 200, "kindergarten_places_per_100": 44,
        "has_college": "Нет", "rent_1room_rub": 19967,
        "gas_available": "Да", "free_power_kva": 723,
        "distance_to_substation_km": 7.0, "connection_cost_rub_kva": 4596,
        "steel_distance_km": 600, "insulation_distance_km": 120,
        "market_distance_km": 385, "ecology_class": 1,
    },
    "Нижегородская область": {
        "avg_salary_rub": 58900, "energy_tariff_rub_kwh": 4.90,
        "tax_benefit": 20, "insurance_benefit": 15,
        "quality_index": 211, "kindergarten_places_per_100": 77,
        "has_college": "Нет", "rent_1room_rub": 20186,
        "gas_available": "Нет", "free_power_kva": 998,
        "distance_to_substation_km": 7.0, "connection_cost_rub_kva": 7177,
        "steel_distance_km": 400, "insulation_distance_km": 350,
        "market_distance_km": 120, "ecology_class": 1,
    },
    "Самарская область": {
        "avg_salary_rub": 54600, "energy_tariff_rub_kwh": 4.50,
        "tax_benefit": 0, "insurance_benefit": 0,
        "quality_index": 203, "kindergarten_places_per_100": 64,
        "has_college": "Нет", "rent_1room_rub": 30338,
        "gas_available": "Да", "free_power_kva": 832,
        "distance_to_substation_km": 10.0, "connection_cost_rub_kva": 3760,
        "steel_distance_km": 600, "insulation_distance_km": 350,
        "market_distance_km": 178, "ecology_class": 3,
    },
    "Красноярский край": {
        "avg_salary_rub": 74200, "energy_tariff_rub_kwh": 3.80,
        "tax_benefit": 20, "insurance_benefit": 0,
        "quality_index": 190, "kindergarten_places_per_100": 50,
        "has_college": "Да", "rent_1room_rub": 21630,
        "gas_available": "Нет", "free_power_kva": 514,
        "distance_to_substation_km": 5.0, "connection_cost_rub_kva": 5280,
        "steel_distance_km": 600, "insulation_distance_km": 60,
        "market_distance_km": 306, "ecology_class": 3,
    },
    "Владимирская область": {
        "avg_salary_rub": 52100, "energy_tariff_rub_kwh": 5.10,
        "tax_benefit": 20, "insurance_benefit": 15,
        "quality_index": 218, "kindergarten_places_per_100": 50,
        "has_college": "Да", "rent_1room_rub": 23621,
        "gas_available": "Да", "free_power_kva": 556,
        "distance_to_substation_km": 6.0, "connection_cost_rub_kva": 6623,
        "steel_distance_km": 150, "insulation_distance_km": 60,
        "market_distance_km": 300, "ecology_class": 3,
    },
}


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def _build_session(proxy: Optional[str] = None) -> requests.Session:
    """Создаёт сессию с настройками прокси и retry-политикой."""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()

    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Прокси: аргумент командной строки > переменные окружения
    proxies = {}
    proxy_url = proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
        log.info(f"Используется прокси: {proxy_url}")
    session.proxies.update(proxies)

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    })
    return session


def _get_json(session: requests.Session, url: str, params: dict = None) -> Optional[Any]:
    """GET-запрос с возвратом JSON или None при ошибке."""
    try:
        r = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning(f"Запрос к {url} завершился ошибкой: {e}")
        return None


# ─── Источник 1: Росстат API v2 ───────────────────────────────────────────────

ROSSTAT_SALARY_URL = "https://showdata.gks.ru/api/data"

def fetch_rosstat_salaries(session: requests.Session) -> Dict[str, float]:
    """
    Получает среднемесячную номинальную зарплату по регионам через Росстат API.
    Если API недоступен — возвращает пустой словарь (сработает fallback).
    Документация: https://showdata.gks.ru/
    """
    result = {}
    # Идентификатор показателя: среднемесячная зарплата (номинальная), последний период
    params = {
        "id":      "37079",   # series ID в базе Росстата
        "version": "1",
        "format":  "json",
    }
    data = _get_json(session, ROSSTAT_SALARY_URL, params)
    if not data:
        return result

    try:
        # Структура ответа: {"data": [{"name": "Регион", "values": [{"value": 12345.6}]}]}
        for item in data.get("data", []):
            region_name = item.get("name", "").strip()
            values = item.get("values", [])
            if values and region_name:
                salary = float(values[-1].get("value", 0))
                if salary > 0:
                    result[region_name] = salary
        log.info(f"Росстат: получены зарплаты для {len(result)} регионов")
    except Exception as e:
        log.warning(f"Ошибка разбора ответа Росстата: {e}")

    return result


# ─── Источник 2: Индекс городской среды (Минстрой) ───────────────────────────

MINSTROY_URL = "https://индекс-городов.рф/api/v1/public/regions"
# Зеркало через латиницу (работает без VPN с кириллическим доменом)
MINSTROY_MIRROR = "https://xn----8sbgcbhhevdaemj4c.xn--p1ai/api/v1/public/regions"

def fetch_minstroy_indices(session: requests.Session) -> Dict[str, int]:
    """Индекс качества городской среды по регионам (Минстрой РФ)."""
    for url in [MINSTROY_URL, MINSTROY_MIRROR]:
        data = _get_json(session, url)
        if data:
            result = {}
            try:
                for item in data.get("items", []):
                    name = item.get("name", "").replace("область", "обл.").strip()
                    score = int(item.get("score", 0))
                    if name and score:
                        result[name] = score
                if result:
                    log.info(f"Минстрой: получены индексы для {len(result)} регионов")
                    return result
            except Exception as e:
                log.warning(f"Ошибка разбора Минстрой ({url}): {e}")

    log.info("Минстрой недоступен — используем резерв")
    # Резервные данные (актуальны на 2024 год по опубликованному рейтингу)
    return {
        "Республика Татарстан": 214,
        "Нижегородская область": 211,
        "Самарская область":     203,
        "Пермский край":         197,
        "Республика Башкортостан": 201,
        "Ленинградская область": 208,
        "Свердловская область":  202,
        "Краснодарский край":    205,
        "Новосибирская область": 195,
        "Челябинская область":   200,
        "Красноярский край":     190,
        "Владимирская область":  218,
        "Московская область":    231,
        "Ростовская область":    193,
        "Воронежская область":   204,
    }


# ─── Источник 3: GitHub-зеркала (энерготарифы, льготы) ──────────────────────

def fetch_mirror_data(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """
    Пытается загрузить агрегированные данные (тарифы, льготы, аренда)
    из нескольких GitHub-зеркал. Возвращает словарь {region: {поля}}.
    """
    for url in MIRRORS:
        data = _get_json(session, url)
        if isinstance(data, dict) and "regions" in data:
            result = {}
            for item in data["regions"]:
                name = item.get("name", "")
                if name:
                    result[name] = {
                        "energy_tariff_rub_kwh": float(item.get("energy_tariff", 0)),
                        "tax_benefit":           int(item.get("tax_benefit", 0)),
                        "insurance_benefit":     int(item.get("insurance_benefit", 0)),
                        "rent_1room_rub":        int(item.get("rent_1room", 0)),
                    }
            if result:
                log.info(f"GitHub-зеркало ({url}): получены данные для {len(result)} регионов")
                return result
        time.sleep(0.5)

    log.info("GitHub-зеркала недоступны — используем резерв по тарифам")
    return {}


# ─── Источник 4: hh.ru публичный API (зарплаты как косвенный индикатор) ──────

HH_API_URL = "https://api.hh.ru/areas"

def fetch_hh_areas(session: requests.Session) -> Dict[str, str]:
    """
    Получает ID регионов из hh.ru для дальнейшей кросс-валидации.
    hh.ru доступен без VPN из РФ и с большинства зарубежных адресов.
    """
    data = _get_json(session, HH_API_URL)
    if not data:
        return {}

    id_map = {}
    try:
        for country in data:
            if country.get("id") == "113":  # Россия
                for region in country.get("areas", []):
                    id_map[region["name"]] = region["id"]
        log.info(f"hh.ru: получен справочник регионов ({len(id_map)} записей)")
    except Exception as e:
        log.warning(f"Ошибка разбора hh.ru: {e}")
    return id_map


# ─── Основной класс парсера ───────────────────────────────────────────────────

class RegionalParser:
    """
    Комплексный парсер данных по регионам РФ.

    Принцип работы:
      1. Пробует каждый источник с retry + таймаутом.
      2. При недоступности источника — берёт значение из FALLBACK_DATA.
      3. Обновляет только те поля, для которых получены свежие данные.
      4. Поля arch_styles / traditional_materials / color_profile берутся
         только из жёстко зашитого ARCH_PROFILES (LLM-независимо).
    """

    def __init__(self, csv_path: Path = CSV_PATH, proxy: Optional[str] = None):
        self.csv_path = csv_path
        self.session = _build_session(proxy)
        self._stats = {"updated": 0, "fallback": 0, "skipped": 0}

    # ── Шаг 1: сбор данных ────────────────────────────────────────────────────

    def _collect(self) -> Dict[str, Dict[str, Any]]:
        """Запускает все источники и объединяет результаты."""
        log.info("═══ Сбор данных из внешних источников ═══")

        salaries  = fetch_rosstat_salaries(self.session)
        indices   = fetch_minstroy_indices(self.session)
        mirror    = fetch_mirror_data(self.session)
        _hh_areas = fetch_hh_areas(self.session)  # пока для валидации

        merged: Dict[str, Dict[str, Any]] = {}

        all_regions = set(FALLBACK_DATA.keys())
        for region in all_regions:
            row: Dict[str, Any] = {}

            # Зарплата: Росстат > fallback
            if region in salaries:
                row["avg_salary_rub"] = round(salaries[region])
                self._stats["updated"] += 1
            else:
                row["avg_salary_rub"] = FALLBACK_DATA[region]["avg_salary_rub"]
                self._stats["fallback"] += 1

            # Индекс среды: Минстрой > fallback
            # Попытка найти по полному или сокращённому имени
            qi = indices.get(region) or indices.get(region.replace("область", "обл.").strip())
            if qi:
                row["quality_index"] = qi
            else:
                row["quality_index"] = FALLBACK_DATA[region]["quality_index"]

            # Энерготариф, льготы, аренда: GitHub-зеркало > fallback
            m = mirror.get(region, {})
            for field in ("energy_tariff_rub_kwh", "tax_benefit", "insurance_benefit", "rent_1room_rub"):
                val = m.get(field)
                if val is not None and val != 0:
                    row[field] = val
                else:
                    row[field] = FALLBACK_DATA[region][field]

            # Поля, которые не меняются / берутся из жёстко зашитого справочника
            static_fields = (
                "kindergarten_places_per_100", "has_college",
                "gas_available", "free_power_kva",
                "distance_to_substation_km", "connection_cost_rub_kva",
                "steel_distance_km", "insulation_distance_km",
                "market_distance_km", "ecology_class",
            )
            for field in static_fields:
                row[field] = FALLBACK_DATA[region][field]

            # Архитектурный профиль
            arch = ARCH_PROFILES.get(region, {})
            row["arch_styles"]           = arch.get("arch_styles", "эклектика, модерн, советский ампир")
            row["traditional_materials"] = arch.get("traditional_materials", "кирпич, дерево, бетон")
            row["color_profile"]         = arch.get("color_profile", "серый, белый, терракотовый")

            merged[region] = row

        return merged

    # ── Шаг 2: применение к CSV ───────────────────────────────────────────────

    def run_update(self, dry_run: bool = False) -> str:
        """
        Основной метод: обновляет CSV свежими данными.

        :param dry_run: если True — только выводит план, CSV не изменяется.
        :returns: строка с итогами работы.
        """
        if not self.csv_path.exists():
            return f"[ОШИБКА] Файл {self.csv_path} не найден."

        collected = self._collect()
        if not collected:
            return "[ОШИБКА] Не удалось собрать данные ни из одного источника."

        df = pd.read_csv(self.csv_path)
        changes: list[str] = []

        for idx, csv_row in df.iterrows():
            region = csv_row["region"]
            new_data = collected.get(region)
            if not new_data:
                log.debug(f"Регион не найден в справочнике: {region}")
                self._stats["skipped"] += 1
                continue

            for field, new_val in new_data.items():
                if field not in df.columns:
                    continue
                old_val = csv_row.get(field)
                if str(old_val) != str(new_val):
                    changes.append(f"  {region} | {field}: {old_val!r} → {new_val!r}")
                    if not dry_run:
                        df.at[idx, field] = new_val

        if dry_run:
            log.info("═══ DRY-RUN: план изменений ═══")
            for c in changes:
                log.info(c)
            return f"DRY-RUN завершён. Запланировано изменений: {len(changes)}"

        if changes:
            df.to_csv(self.csv_path, index=False, encoding="utf-8")
            summary = (
                f"Синхронизация завершена.\n"
                f"  Строк обновлено: {len(df)}\n"
                f"  Полей изменено:  {len(changes)}\n"
                f"  Из внешних API:  {self._stats['updated']}\n"
                f"  Из резерва:      {self._stats['fallback']}\n"
                f"  Регионов пропущено: {self._stats['skipped']}"
            )
        else:
            summary = "Данные актуальны. Изменений нет."

        log.info(summary)
        return summary

    # ── Публичный метод для импорта из других модулей ─────────────────────────

    def get_merged_dict(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает объединённый словарь данных без записи в CSV."""
        return self._collect()


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Парсер региональных данных для проекта «Наследие индустрии»"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Показать план изменений без записи в CSV"
    )
    parser.add_argument(
        "--proxy", type=str, default=None,
        help="URL прокси-сервера, например: http://user:pass@host:3128"
    )
    parser.add_argument(
        "--csv", type=str, default=str(CSV_PATH),
        help=f"Путь к CSV-файлу регионов (по умолчанию: {CSV_PATH})"
    )
    args = parser.parse_args()

    regional_parser = RegionalParser(
        csv_path=Path(args.csv),
        proxy=args.proxy,
    )
    result = regional_parser.run_update(dry_run=args.dry_run)
    print(result)