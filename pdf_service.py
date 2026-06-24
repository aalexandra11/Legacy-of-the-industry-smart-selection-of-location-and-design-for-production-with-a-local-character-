import os
import base64
import traceback
from fpdf import FPDF
from datetime import datetime

class DetailedPresentationPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        font_path = "times.ttf"
        font_bold_path = "timesbd.ttf"
        if not os.path.exists(font_path):
            font_path = 'C:/Windows/Fonts/arial.ttf'
            font_bold_path = 'C:/Windows/Fonts/arialbd.ttf'
        if os.path.exists(font_path):
            try:
                self.add_font('FreeSans', '', font_path, uni=True)
                if os.path.exists(font_bold_path):
                    self.add_font('FreeSans', 'B', font_bold_path, uni=True)
                else:
                    self.add_font('FreeSans', 'B', font_path, uni=True)
                print("[PDF] Шрифт FreeSans загружен")
            except Exception as e:
                print(f"[PDF] Ошибка загрузки шрифта: {e}")
        else:
            print("[PDF] Шрифт не найден, используется Helvetica")

    def header(self):
        if self.page_no() > 1:
            try:
                self.set_font('FreeSans', 'B', 8)
            except:
                self.set_font('Helvetica', 'B', 8)
            self.set_text_color(100)
            self.cell(0, 10, 'Платформа «Наследие индустрии»', 0, 0, 'L')
            self.cell(0, 10, f'Слайд {self.page_no()-1}', 0, 1, 'R')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('FreeSans', '', 8)
        except:
            self.set_font('Helvetica', '', 8)
        self.set_text_color(150)
        self.cell(0, 10, datetime.now().strftime('%d.%m.%Y'), 0, 0, 'C')

    def slide_title(self, title):
        try:
            self.set_font('FreeSans', 'B', 18)
        except:
            self.set_font('Helvetica', 'B', 18)
        self.set_text_color(30, 80, 130)
        self.cell(0, 12, title, 0, 1, 'L')
        self.set_draw_color(100, 150, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def section(self, text, bold=False):
        try:
            self.set_font('FreeSans', 'B' if bold else '', 12 if bold else 11)
        except:
            self.set_font('Helvetica', 'B' if bold else '', 12 if bold else 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, text, 0, 1)
        self.ln(2)

    def paragraph(self, text):
        try:
            self.set_font('FreeSans', '', 10)
        except:
            self.set_font('Helvetica', '', 10)
        self.multi_cell(0, 5, text)
        self.ln(3)

    def bullet(self, text):
        try:
            self.set_font('FreeSans', '', 10)
        except:
            self.set_font('Helvetica', '', 10)
        self.cell(5)
        self.cell(5, 6, '•', 0, 0)
        self.multi_cell(0, 5, text)

    def two_column_text(self, left_text, right_text):
        """Две колонки текста с возвратом на правильную Y-координату"""
        try:
            self.set_font('FreeSans', '', 10)
        except:
            self.set_font('Helvetica', '', 10)
        x_start = self.get_x()
        y_start = self.get_y()
        # Левая колонка
        self.multi_cell(95, 5, left_text)
        y_left_after = self.get_y()
        # Правая колонка
        self.set_xy(x_start + 100, y_start)
        self.multi_cell(95, 5, right_text)
        y_right_after = self.get_y()
        # Устанавливаем Y ниже самой высокой колонки
        self.set_y(max(y_left_after, y_right_after))
        self.ln(3)

def clean_txt(text):
    if not text:
        return ""
    return str(text).replace('«', '"').replace('»', '"').replace('—', '-').replace('–', '-')

def create_presentation(payload, output_filename="presentation.pdf"):
    print(f"[PDF] Начинаем генерацию для {payload.get('region', 'unknown')}, файл: {output_filename}")
    try:
        pdf = DetailedPresentationPDF()
        cost = payload.get('cost_data', {})
        areas = payload.get('areas', {})
        concept = payload.get('concept_board', {})
        analytics = payload.get('analytics', {})
        region = payload.get('region', 'Не указан')
        site_name = payload.get('site_name', region)
        form = payload.get('form', None)

        # --- Слайд 1: Титул ---
        pdf.add_page()
        pdf.set_y(50)
        try:
            pdf.set_font('FreeSans', 'B', 26)
        except:
            pdf.set_font('Helvetica', 'B', 26)
        pdf.set_text_color(20, 60, 100)
        pdf.cell(0, 15, "ИНВЕСТИЦИОННЫЙ КОНЦЕПТ", 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('FreeSans', 'B', 18)
        pdf.cell(0, 12, f"Завод сэндвич-панелей", 0, 1, 'C')
        pdf.set_font('FreeSans', '', 14)
        pdf.cell(0, 10, f"на площадке {clean_txt(site_name)}", 0, 1, 'C')
        pdf.ln(20)
        pdf.set_font('FreeSans', '', 12)
        pdf.cell(0, 8, f"Субъект РФ: {clean_txt(region)}", 0, 1, 'C')
        pdf.cell(0, 8, f"Дата: {datetime.now().strftime('%d.%m.%Y')}", 0, 1, 'C')

        # --- Слайд 2: Параметры + смета ---
        pdf.add_page()
        pdf.slide_title("1. КЛЮЧЕВЫЕ ПАРАМЕТРЫ ПРОЕКТА И СМЕТА")
        left = f"""
ПРОИЗВОДСТВЕННЫЕ ПОКАЗАТЕЛИ:
• Объём выпуска: {payload.get('volume_thousand_m2', 0)} тыс. м²/год
• Количество сотрудников: {payload.get('employees', 0)} чел.
• Бюджет инвестора: {form.budget_million_rub if form else payload.get('budget', 0)} млн руб
• Класс опасности: {cost.get('hazard_class', 'III')}
• Тип утеплителя: {getattr(form, 'insulation_type', 'ППС') if form else '—'}
• Необходимость автобуса: {'Да' if cost.get('need_bus') else 'Нет'}

СМЕТА (млн руб):
• Общая смета: {cost.get('total_cost_million_rub', 0):.2f}
• Строительство: {cost.get('construction_million_rub', 0):.2f}
• Логистика: {cost.get('logistics_million_rub', 0):.2f}
• Подключение к сетям: {cost.get('connection_million_rub', 0):.2f}
• Земельный участок: {cost.get('land_cost_million_rub', 0):.2f}
• Годовой ФОТ: {cost.get('annual_fot_million_rub', 0):.2f}
"""
        right = f"""
РЕГИОНАЛЬНЫЕ КОЭФФИЦИЕНТЫ:
• Индекс стоимости строительства: {payload.get('construction_cost_index', 1.0)}
• Индекс стоимости труда: {payload.get('labour_cost_index', 1.0)}
• Климатический коэффициент: {cost.get('climate_factor', 1.0)}

СООТВЕТСТВИЕ БЮДЖЕТУ:
• Бюджет: {form.budget_million_rub if form else 0} млн руб
• Отклонение: {(cost.get('total_cost_million_rub', 0) - (form.budget_million_rub if form else 0)):.2f} млн руб
• {'✅ Укладывается' if cost.get('total_cost_million_rub', 0) <= (form.budget_million_rub if form else 0) else '❌ Превышение бюджета'}
"""
        pdf.two_column_text(left, right)

        pdf.section("Детализация строительной сметы (млн руб):")
        pdf.bullet(f"Цех+склад ({areas.get('cech',0):.0f}+{areas.get('sklad',0):.0f} м²) по 25 тыс/м² → {(areas.get('cech',0)+areas.get('sklad',0))*25/1000:.2f} млн руб")
        pdf.bullet(f"АБК ({areas.get('abk',0):.0f} м²) по 40 тыс/м² → {areas.get('abk',0)*40/1000:.2f} млн руб")
        if areas.get('housing',0) > 0:
            h_rate = 50 if (getattr(form, 'housing_type', 'общежитие') if form else 'общежитие') == 'общежитие' else 70
            pdf.bullet(f"Жильё ({areas.get('housing',0):.0f} м²) по {h_rate} тыс/м² → {areas.get('housing',0)*h_rate/1000:.2f} млн руб")
        if areas.get('kindergarten',0) > 0:
            pdf.bullet(f"Детсад ({areas.get('kindergarten',0):.0f} м²) по 45 тыс/м² → {areas.get('kindergarten',0)*45/1000:.2f} млн руб")
        sport_cost = 0
        if form:
            if 'Стадион' in getattr(form, 'sport_items', []):
                sport_cost += 5
            if 'Бассейн' in getattr(form, 'sport_items', []):
                sport_cost += 8
        pdf.bullet(f"Спортсооружения: {sport_cost:.2f} млн руб")

        # --- Слайд 3: Генплан ---
        pdf.add_page()
        pdf.slide_title("2. ГЕНЕРАЛЬНЫЙ ПЛАН И СОЦИАЛЬНАЯ ИНФРАСТРУКТУРА")
        area_list = [
            ("Производственный цех", areas.get('cech',0)),
            ("Складской комплекс", areas.get('sklad',0)),
            ("АБК", areas.get('abk',0)),
            ("Парковка", areas.get('parking',0)),
            ("Внутриплощадочные дороги", areas.get('roads',0)),
        ]
        if areas.get('housing',0) > 0:
            area_list.append(("Корпоративное жильё", areas.get('housing',0)))
        if areas.get('kindergarten',0) > 0:
            area_list.append(("Детский сад", areas.get('kindergarten',0)))
        if areas.get('canteen',0) > 0:
            area_list.append(("Столовая", areas.get('canteen',0)))
        if areas.get('medpunkt',0) > 0:
            area_list.append(("Медпункт", areas.get('medpunkt',0)))
        total = sum(a for _,a in area_list)
        for name, val in area_list:
            pdf.bullet(f"{name}: {val:.1f} м² ({val/total*100:.1f}%)")
        pdf.ln(3)
        pdf.section(f"ИТОГО полезная площадь застройки: {total:.1f} м²")
        pdf.section("Спортивные и рекреационные объекты:")
        if form:
            sport_items = getattr(form, 'sport_items', [])
            improve_items = getattr(form, 'improvement_items', [])
            if sport_items:
                for s in sport_items:
                    pdf.bullet(f"Спорт: {s}")
            else:
                pdf.bullet("Спортивные объекты не выбраны")
            if improve_items:
                for imp in improve_items:
                    pdf.bullet(f"Благоустройство: {imp}")
            else:
                pdf.bullet("Элементы благоустройства не выбраны")

        # --- Слайд 4: Инфраструктура и логистика ---
        pdf.add_page()
        pdf.slide_title("3. ИНЖЕНЕРНАЯ ИНФРАСТРУКТУРА И ЛОГИСТИКА")
        left_infra = f"""
ЭНЕРГОСНАБЖЕНИЕ:
• Газ в промзоне: {'Да' if str(payload.get('gas_available', '')).lower() == 'да' else 'Нет'}
• Уровень газификации региона: {payload.get('gasification_percent', 0):.1f}%
• Свободная мощность: {payload.get('free_power_kva', 0)} кВА
• Требуемая мощность: {cost.get('power_required_kva', 0)} кВА
• Дефицит/резерв: {payload.get('free_power_kva', 0) - cost.get('power_required_kva', 0)} кВА

ТРАНСПОРТ:
• Ж/д ветка: {'Да' if str(payload.get('railway_available', '')).lower() == 'да' else 'Нет'}
• Расстояние до фед. трассы: {payload.get('federal_road_distance_km', 0)} км
• Плотность автодорог в регионе: {payload.get('road_density', 0):.1f} км/1000 км²
• Индустриальный парк: {'Да' if str(payload.get('industrial_park_available', '')).lower() == 'да' else 'Нет'}
"""
        right_log = f"""
ЛОГИСТИКА СЫРЬЯ:
• Расстояние до стали: {payload.get('steel_distance_km', 0)} км
• Ближайший поставщик: {cost.get('closest_steel_supplier', '—')}
• Расстояние до утеплителя: {payload.get('insulation_distance_km', 0)} км
• Ближайший поставщик: {cost.get('closest_insulation_supplier', '—')}
• Расстояние до рынка сбыта: {payload.get('market_distance_km', 0)} км

Затраты на логистику в смете: {cost.get('logistics_million_rub', 0):.2f} млн руб
Доля в общей смете: {(cost.get('logistics_million_rub',0)/max(cost.get('total_cost_million_rub',1),1)*100):.1f}%
"""
        pdf.two_column_text(left_infra, right_log)

        # --- Слайд 5: Соцэконом паспорт ---
        pdf.add_page()
        pdf.slide_title("4. СОЦИАЛЬНО-ЭКОНОМИЧЕСКИЙ ПАСПОРТ РЕГИОНА")
        left_soc = f"""
НАСЕЛЕНИЕ И РЫНОК ТРУДА:
• Население: {payload.get('population_thousands', 0):.0f} тыс. чел.
• Плотность: {payload.get('population_density', 0):.1f} чел./км²
• Урбанизация: {payload.get('urban_population_percent', 0):.1f}%
• Уровень безработицы: {payload.get('unemployment_rate_percent', 0):.1f}%
• Средняя зарплата: {payload.get('avg_salary_rub', 0):,} руб/мес
• Аренда 1-комнатной: {payload.get('rent_1room_rub', 0):,} руб/мес
• Доля зарплаты на аренду: {(payload.get('rent_1room_rub',0)/max(payload.get('avg_salary_rub',1),1)*100):.1f}%

ОБРАЗОВАНИЕ И ЗДРАВООХРАНЕНИЕ:
• Колледжей: {payload.get('colleges_count', 0)}
• Профильные колледжи: {'Да' if str(payload.get('has_college', '')).lower() == 'да' else 'Нет'}
• Мед. учреждений на 100 тыс.: {payload.get('medical_institutions_per_100k', 0):.1f}
• Мест в детсадах на 100 детей: {payload.get('kindergarten_places_per_100', 0)}
"""
        right_econ = f"""
ЭКОНОМИКА:
• ВРП на душу: {payload.get('grp_per_capita_rub', 0):,} руб.
• Инвестиции в основной капитал: {payload.get('investment_capital_million_rub', 0):,} млн руб.
• Индекс промпроизводства: {payload.get('industrial_production_index', 100):.1f}%
• Розничный оборот на душу: {payload.get('retail_turnover_per_capita_rub', 0):,} руб.

КАЧЕСТВО СРЕДЫ И ЭКОЛОГИЯ:
• Индекс качества городской среды: {payload.get('quality_index', 0)} / 360
• Экологический класс: {payload.get('ecology_class', 3)}
• Уровень газификации: {payload.get('gasification_percent', 0):.1f}%
• Плотность дорог: {payload.get('road_density', 0):.1f} км/1000 км²
"""
        pdf.two_column_text(left_soc, right_econ)

        # --- Слайд 6: Налоговые льготы ---
        pdf.add_page()
        pdf.slide_title("5. НАЛОГОВЫЕ ПРЕФЕРЕНЦИИ И ЭКОНОМИЧЕСКАЯ ВЫГОДА")
        tax_benefit_pp = payload.get('tax_benefit', 0)
        insurance_benefit = payload.get('insurance_benefit', 0)
        annual_fot = cost.get('annual_fot_million_rub', 0)
        estimated_profit = annual_fot * 3
        tax_savings = estimated_profit * (tax_benefit_pp / 100)
        insurance_savings = annual_fot * (insurance_benefit / 100)
        total_savings = tax_savings + insurance_savings
        total_invest = cost.get('total_cost_million_rub', 0)
        payback = total_invest / total_savings if total_savings > 0 else 0
        pdf.paragraph(f"**Полный текст льгот:** {payload.get('tax_benefits_list', '—')}")
        pdf.ln(3)
        left_tax = f"""
НАЛОГ НА ПРИБЫЛЬ:
• Базовая ставка: 20%
• Льготная ставка: {20 - tax_benefit_pp:.1f}% (снижение на {tax_benefit_pp} п.п.)
• Оценочная прибыль до налога: {estimated_profit:.1f} млн руб/год
• Экономия на налоге на прибыль: {tax_savings:.2f} млн руб/год

СТРАХОВЫЕ ВЗНОСЫ:
• Базовая ставка: 30%
• Льготная ставка: {30 - insurance_benefit:.1f}%
• Годовой ФОТ: {annual_fot:.2f} млн руб
• Экономия на взносах: {insurance_savings:.2f} млн руб/год
"""
        right_tax = f"""
ИТОГОВАЯ ЭКОНОМИЯ:
• Общая ежегодная экономия: {total_savings:.2f} млн руб
• Объём инвестиций: {total_invest:.2f} млн руб
• Простой срок окупаемости за счёт льгот: {payback:.1f} лет

ДОПОЛНИТЕЛЬНЫЕ НАЛОГОВЫЕ ПОСТУПЛЕНИЯ В РЕГИОН:
• НДФЛ с ФОТ: {annual_fot * 0.13:.2f} млн руб/год
• Налог на имущество: оценочно {cost.get('construction_million_rub',0)*0.022:.2f} млн руб/год
"""
        pdf.two_column_text(left_tax, right_tax)

        # --- Слайд 7 и 8: Аналитика ИИ (2 страницы) ---
        ai_text = analytics.get('summary', '')
        if not ai_text:
            ai_text = "Аналитическое заключение формируется на основе предоставленных данных. Рекомендуется детальная проработка с инвестором."
        pdf.add_page()
        pdf.slide_title("6. АНАЛИТИЧЕСКОЕ ЗАКЛЮЧЕНИЕ (часть 1)")
        pdf.paragraph(clean_txt(ai_text[:2000] if len(ai_text) > 2000 else ai_text))
        if len(ai_text) > 2000:
            pdf.add_page()
            pdf.slide_title("6. АНАЛИТИЧЕСКОЕ ЗАКЛЮЧЕНИЕ (часть 2)")
            pdf.paragraph(clean_txt(ai_text[2000:4000]))

        # --- Слайд 9: Рекомендации ---
        pdf.add_page()
        pdf.slide_title("7. РЕКОМЕНДАЦИИ И СЛЕДУЮЩИЕ ШАГИ")
        rec_text = f"""
На основе анализа площадки {clean_txt(site_name)} в {clean_txt(region)} сформулированы следующие рекомендации:

1. **Инфраструктурные мероприятия**:
   - {'Обеспечить резервирование электрической мощности (' + str(cost.get('power_required_kva',0)) + ' кВА) ' if payload.get('free_power_kva',0) < cost.get('power_required_kva',0) else 'Доступной мощности достаточно, но рекомендуется заложить резерв на расширение.'}
   - {'Организовать подвод газа к границе участка.' if str(payload.get('gas_available', '')).lower() != 'да' else 'Газ подведён, что снижает эксплуатационные расходы.'}

2. **Логистика и снабжение**:
   - Ближайший поставщик стали – {cost.get('closest_steel_supplier', '—')} ({payload.get('steel_distance_km',0)} км). Заключить долгосрочный контракт.
   - Поставщик утеплителя {cost.get('closest_insulation_supplier', '—')} ({payload.get('insulation_distance_km',0)} км) – логистические риски минимальны.

3. **Кадровое обеспечение**:
   - {'В регионе есть профильные колледжи – организовать целевой набор.' if str(payload.get('has_college', '')).lower() == 'да' else 'Рекомендуется создать корпоративный учебный центр.'}
   - Доля аренды в зарплате: {payload.get('rent_1room_rub',0)/max(payload.get('avg_salary_rub',1),1)*100:.1f}% – жильё доступно.
   - {'Организовать служебный автобус (рынок сбыта > 170 км).' if cost.get('need_bus') else 'Транспортная доступность удовлетворительная.'}

4. **Налоговое планирование**:
   - Подать заявку на статус резидента ОЭЗ/ТОР.
   - Использовать пониженные ставки страховых взносов ({insurance_benefit}% экономии).

5. **Строительство и проектирование**:
   - Учесть коэффициенты: строительства {payload.get('construction_cost_index',1.0)}, климатический {cost.get('climate_factor',1.0)}.
   - Рекомендуемый стиль: {concept.get('style_description', 'современный')}. Материалы: {', '.join(concept.get('materials', ['сэндвич-панели']))}.

6. **Социальная ответственность**:
   - Программа корпоративного жилья для {getattr(form, 'housing_percent', 0) if form else 0}% сотрудников.
   - {'Построить детский сад на ' + str(areas.get('kindergarten',0)) + ' м².' if areas.get('kindergarten',0) > 0 else 'Заключить договор с муниципальными детсадами.'}
   - Спортивные объекты: {', '.join(getattr(form, 'sport_items', []) if form else []) or 'минимальный набор'}.

**Следующие шаги (ближайшие 3 месяца)**:
• Зарезервировать участок и получить ТУ на подключение.
• Заключить меморандумы с поставщиками.
• Подать заявку на финансирование ПИР.
• Начать переговоры с региональным фондом развития промышленности.
"""
        pdf.paragraph(rec_text)

        # --- Слайд 10: Рендеры фасадов (если есть) ---
        renders = payload.get("renders", [])
        if renders:
            SIDE_LABELS = ["Южный фасад (главный вход)", "Северный фасад (ж/д сторона)",
                           "Западный фасад", "Восточный фасад (парковка)"]
            pdf.add_page()
            pdf.slide_title("8. РЕНДЕРЫ ФАСАДОВ")
            pdf.paragraph("Архитектурные рендеры сгенерированы нейросетью на основе параметров проекта и региональных характеристик.")
            pdf.ln(2)

            for i, img_data in enumerate(renders[:4]):
                label = SIDE_LABELS[i] if i < len(SIDE_LABELS) else f"Вид {i+1}"
                try:
                    # Декодируем base64 → PNG → tmp-файл
                    if img_data.startswith("data:image"):
                        img_b64 = img_data.split(",", 1)[1]
                    else:
                        img_b64 = img_data
                    img_bytes = base64.b64decode(img_b64)
                    tmp_path = f"_tmp_render_{i}.png"
                    with open(tmp_path, "wb") as tf:
                        tf.write(img_bytes)

                    # Новая страница для каждого рендера
                    if i > 0 or pdf.get_y() > 150:
                        pdf.add_page()

                    pdf.section(label, bold=True)
                    pdf.ln(2)
                    # Вписываем изображение по ширине страницы (190 мм), высота ~107 мм (пропорция 16:9)
                    pdf.image(tmp_path, x=10, w=190, h=107)
                    pdf.ln(5)

                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"[PDF] Рендер {i} не добавлен: {e}")

        pdf.output(output_filename)
        print(f"[PDF] Презентация успешно создана: {output_filename}")
        return output_filename
    except Exception as e:
        print(f"[PDF] ОШИБКА: {e}")
        traceback.print_exc()
        raise