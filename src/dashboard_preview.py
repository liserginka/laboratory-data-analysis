# -*- coding: utf-8 -*-
"""
Визуальный обзор дашборда (для README) — то же самое, что считается
формулами в Excel на листе "Дашборд", но как статичная картинка для
превью в репозитории.
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
EXCEL_DIR = ROOT / "excel"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Пересчитываем те же самые статусы, что в Excel (Fe/pH/EC пороги),
# чтобы график полностью соответствовал логике листа "Результаты".
df = pd.read_csv(DATA_DIR / "raw_measurements.csv", encoding="utf-8-sig")

K_FE, B_FE = 0.8373, 0.0113
FE_MAX, PH_MIN, PH_MAX, EC_MAX = 0.3, 6.0, 9.0, 1000

df["Fe_conc"] = (df["A_Fe_сигнал"] - B_FE) / K_FE
df["Fe_status"] = (df["Fe_conc"] <= FE_MAX)
df["pH_status"] = df["pH_измерено"].between(PH_MIN, PH_MAX)
df["EC_status"] = df["Электропроводность_мкСм_см"] <= EC_MAX
df["overall_ok"] = df["Fe_status"] & df["pH_status"] & df["EC_status"]
df["month"] = df["Дата"].str[:7]

monthly = df.groupby("month").agg(
    total=("ID_пробы", "count"),
    pass_rate=("overall_ok", "mean"),
    fe_fail=("Fe_status", lambda s: (~s).sum()),
    ph_fail=("pH_status", lambda s: (~s).sum()),
    ec_fail=("EC_status", lambda s: (~s).sum()),
).reset_index()
monthly["pass_rate_pct"] = (monthly["pass_rate"] * 100).round(1)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
ax.plot(monthly["month"], monthly["pass_rate_pct"], marker="o", linewidth=2, color="#3E6E8E")
ax.set_ylim(70, 100)
ax.set_title("Доля проб, соответствующих нормативам, по месяцам", fontsize=12, fontweight="bold")
ax.set_ylabel("% соответствия")
ax.grid(True, linestyle="--", alpha=0.4)
for x, y in zip(monthly["month"], monthly["pass_rate_pct"]):
    ax.annotate(f"{y:.0f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)

ax2 = axes[1]
width = 0.25
xpos = range(len(monthly))
ax2.bar([i - width for i in xpos], monthly["fe_fail"], width, label="Fe", color="#B5482A")
ax2.bar([i for i in xpos], monthly["ph_fail"], width, label="pH", color="#C08628")
ax2.bar([i + width for i in xpos], monthly["ec_fail"], width, label="Электропроводность", color="#5C8A4E")
ax2.set_xticks(list(xpos))
ax2.set_xticklabels(monthly["month"])
ax2.set_title("Превышения по параметрам, по месяцам", fontsize=12, fontweight="bold")
ax2.set_ylabel("Число проб с превышением")
ax2.legend()
ax2.grid(axis="y", linestyle="--", alpha=0.4)

plt.tight_layout()
out_png = RESULTS_DIR / "dashboard_overview.png"
plt.savefig(out_png, dpi=200, bbox_inches="tight")
print(f"Сохранено: {out_png}")
