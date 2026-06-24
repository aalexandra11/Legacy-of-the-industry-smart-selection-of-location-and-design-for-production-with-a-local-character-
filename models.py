from pydantic import BaseModel, Field
from typing import List, Literal

class InvestmentForm(BaseModel):
    volume_thousand_m2: int = Field(..., ge=100, le=1000)
    employees: int = Field(..., ge=10, le=200)
    budget_million_rub: int = Field(..., ge=10, le=300)
    need_railway: bool
    max_distance_to_highway_km: int = Field(..., ge=1, le=100)
    arch_priority: Literal["Аутентичность региону", "Техно-стиль", "Экодизайн"]
    improvement_items: List[
        Literal["Аллея", "Сквер", "Беседки", "Сцена", "Тропа", "Пруд", "Арт-объект"]
    ] = Field(default_factory=list, max_length=3)
    housing_percent: Literal[0, 30, 50, 70]
    housing_type: Literal["общежитие", "квартиры"]
    kindergarten_places_per_100: Literal[0, 15, 30, 50]
    sport_items: List[
        Literal["Уличные тренажёры", "Стадион", "Бассейн", "Спортзал", "Хоккейная коробка"]
    ] = Field(default_factory=list, max_length=2)
    insulation_type: Literal["ППУ", "минвата", "ППС"] = "ППС"