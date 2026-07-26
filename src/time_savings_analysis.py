# -*- coding: utf-8 -*-
"""
Количественная оценка эффекта автоматизации: сколько времени экономится
на обработке одной пробы и сколько это даёт в масштабе дня/месяца/года.

Оценки по этапам (примерные, легко скорректировать под реальные цифры):
  - Запись результатов измерений в журнал вручную: 10 мин -> 3 мин (ввод в форму)
  - Расчёт показателей и сверка с нормативами вручную (несколько листов
    вычислений на пробу) + составление сводного отчёта: 5 мин -> 1 мин (автоматически)
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------
# 1. Разбивка времени на пробу по этапам (вручную vs автоматизировано)
# ---------------------------------------------------------------
steps = pd.DataFrame([
    {"Этап": "Запись результатов измерений", "Вручную_мин": 10, "Автоматизировано_мин": 3},
    {"Этап": "Расчёт показателей + сверка с нормативами + сводный отчёт", "Вручную_мин": 5, "Автоматизировано_мин": 1},
])
steps["Итого_вручную"] = steps["Вручную_мин"].sum()
steps["Итого_автоматизировано"] = steps["Автоматизировано_мин"].sum()

total_manual = steps["Вручную_мин"].sum()
total_auto = steps["Автоматизировано_мин"].sum()
reduction_pct = round((1 - total_auto / total_manual) * 100, 1)

print(f"Итого на пробу вручную: {total_manual} мин")
print(f"Итого на пробу автоматизировано: {total_auto} мин")
print(f"Сокращение времени: {reduction_pct}%")

# ---------------------------------------------------------------
# 2. Экстраполяция на день / месяц / год
# ---------------------------------------------------------------
df = pd.read_csv(DATA_DIR / "raw_measurements.csv", encoding="utf-8-sig")
working_days = df["Дата"].nunique()
avg_samples_per_day = round(len(df) / working_days, 1)

WORKING_DAYS_PER_MONTH = 22
WORKING_DAYS_PER_YEAR = 12 * WORKING_DAYS_PER_MONTH

scale = pd.DataFrame([
    {
        "Период": "1 проба",
        "Вручную, ч": round(total_manual / 60, 2),
        "Автоматизировано, ч": round(total_auto / 60, 2),
    },
    {
        "Период": "1 рабочий день "
                  f"(~{avg_samples_per_day:g} проб)",
        "Вручную, ч": round(total_manual * avg_samples_per_day / 60, 1),
        "Автоматизировано, ч": round(total_auto * avg_samples_per_day / 60, 1),
    },
    {
        "Период": "1 месяц "
                  f"({WORKING_DAYS_PER_MONTH} раб. дн.)",
        "Вручную, ч": round(total_manual * avg_samples_per_day * WORKING_DAYS_PER_MONTH / 60, 1),
        "Автоматизировано, ч": round(total_auto * avg_samples_per_day * WORKING_DAYS_PER_MONTH / 60, 1),
    },
    {
        "Период": "1 год "
                  f"({WORKING_DAYS_PER_YEAR} раб. дн.)",
        "Вручную, ч": round(total_manual * avg_samples_per_day * WORKING_DAYS_PER_YEAR / 60, 0),
        "Автоматизировано, ч": round(total_auto * avg_samples_per_day * WORKING_DAYS_PER_YEAR / 60, 0),
    },
])
scale["Экономия, ч"] = (scale["Вручную, ч"] - scale["Автоматизировано, ч"]).round(1)

print("\n" + scale.to_string(index=False))

steps.to_csv(RESULTS_DIR / "time_breakdown.csv", index=False, encoding="utf-8-sig")
scale.to_csv(RESULTS_DIR / "time_scale.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------
# 3. Визуализация
# ---------------------------------------------------------------
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# (a) время на пробу по этапам
ax = axes[0]
x = range(len(steps))
width = 0.35
ax.bar([i - width / 2 for i in x], steps["Вручную_мин"], width, label="Вручную", color="#B5482A")
ax.bar([i + width / 2 for i in x], steps["Автоматизировано_мин"], width, label="Автоматизировано", color="#3E6E8E")
ax.set_xticks(list(x))
ax.set_xticklabels(["Запись\nрезультатов", "Расчёт + сверка\n+ отчёт"], fontsize=10)
ax.set_ylabel("Минуты на пробу")
ax.set_title(f"Время на 1 пробу: {total_manual} мин -> {total_auto} мин (-{reduction_pct}%)",
             fontsize=12, fontweight="bold")
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.4)

# (b) экономия часов в масштабе
ax2 = axes[1]
periods = scale["Период"]
ax2.bar(periods, scale["Вручную, ч"], color="#B5482A", alpha=0.85, label="Вручную")
ax2.bar(periods, scale["Автоматизировано, ч"], color="#3E6E8E", alpha=0.85, label="Автоматизировано")
ax2.set_ylabel("Часы")
ax2.set_title("Затраты времени на обработку проб: масштаб дня/месяца/года",
              fontsize=12, fontweight="bold")
ax2.set_xticklabels(periods, rotation=20, ha="right", fontsize=9)
ax2.legend()
ax2.grid(axis="y", linestyle="--", alpha=0.4)

plt.tight_layout()
out_png = RESULTS_DIR / "time_savings.png"
plt.savefig(out_png, dpi=200, bbox_inches="tight")
print(f"\nГрафик сохранён: {out_png}")
