# -*- coding: utf-8 -*-
"""
Генерация синтетического датасета проб воды для кейса "автоматизация
контроля качества" (pass/fail по нормативам + свод результатов).

Логика:
- 3 точки отбора проб (условные объекты контроля)
- ~6 месяцев наблюдений, несколько проб в день на точку
- Параметры пробы: сырой сигнал по железу (для пересчёта через
  градуировку из первого кейса), pH, температура, электропроводность
- Заложена реалистичная доля проб с превышением норматива (~8-12%),
  чтобы дашборд по итогам показывал содержательный тренд
"""

from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

np.random.seed(7)

# Градуировка Fe взята из предыдущего кейса (см. automated-calibration-framework):
# A = k*C + b, k=0.8373, b=0.0113 -> используем для генерации "сырого" сигнала
K_FE, B_FE = 0.8373, 0.0113

points = ["Точка-1 (скважина)", "Точка-2 (резервуар)", "Точка-3 (сброс)"]

start = date(2026, 1, 5)
n_days = 130  # ~6 месяцев рабочих дней
samples_per_day = 4

rows = []
sample_id = 1
for d in range(n_days):
    current_date = start + timedelta(days=d)
    if current_date.weekday() >= 5:  # пропускаем выходные
        continue
    for _ in range(samples_per_day):
        point = np.random.choice(points, p=[0.4, 0.35, 0.25])

        # Истинная концентрация Fe: обычно в норме, изредка превышение ПДК (0.3 мг/дм3)
        base_fe = {"Точка-1 (скважина)": 0.14, "Точка-2 (резервуар)": 0.18, "Точка-3 (сброс)": 0.22}[point]
        true_fe = max(np.random.normal(base_fe, 0.09), 0)
        # сезонный дрейф (за полгода концентрация чуть растёт к точке 3 - сброс)
        true_fe += 0.05 * (d / n_days) if point == "Точка-3 (сброс)" else 0
        signal_fe = K_FE * true_fe + B_FE + np.random.normal(0, 0.006)

        ph = np.clip(np.random.normal(7.2, 0.55), 4.5, 10.5)
        temp = np.random.normal(11.5, 4.0) if d < 65 else np.random.normal(16.0, 4.0)  # зима->весна/лето
        ec = np.clip(np.random.normal(650, 160), 150, None)

        rows.append({
            "Дата": current_date.isoformat(),
            "ID_пробы": f"S-{sample_id:04d}",
            "Точка_отбора": point,
            "A_Fe_сигнал": round(max(signal_fe, 0), 4),
            "pH_измерено": round(ph, 2),
            "Температура_C": round(temp, 1),
            "Электропроводность_мкСм_см": round(ec, 0),
        })
        sample_id += 1

df = pd.DataFrame(rows)
out_path = DATA_DIR / "raw_measurements.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"Сохранено: {out_path}")
print(df.shape)
print(df.head(8))
