"""run_summary tablosundan fixed vs adaptive karşılaştırması üretir.

Çıktılar experiments/results/ altına yazılır:
  - summary_stats.csv : senaryo x kontrol bazında ortalama ve standart sapma
  - improvement.csv   : yüzde iyileşme tablosu
  - <metrik>.png      : her metrik için karşılaştırma grafiği
"""
import os

import clickhouse_connect
import matplotlib

matplotlib.use("Agg")  # ekran gerektirmeyen backend
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

client = clickhouse_connect.get_client(
    host="localhost",
    port=int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
    username=os.environ["CLICKHOUSE_USER"],
    password=os.environ["CLICKHOUSE_PASSWORD"],
    database=os.getenv("CLICKHOUSE_DB", "traffic"),
)

OUT = "experiments/results"
os.makedirs(OUT, exist_ok=True)

df = client.query_df("SELECT * FROM run_summary")
if df.empty:
    raise SystemExit("run_summary tablosu boş. Önce fake_summary.py çalıştır.")

# Düşük olması iyi olanlar / yüksek olması iyi olanlar
LOWER_BETTER = ["avg_waiting", "avg_queue", "avg_travel_time", "total_stops", "co2_mg"]
HIGHER_BETTER = ["avg_speed", "throughput"]
METRICS = LOWER_BETTER + HIGHER_BETTER

# 1) Senaryo x kontrol bazında ortalama ve standart sapma
grouped = df.groupby(["scenario", "controller"])[METRICS]
grouped.agg(["mean", "std"]).to_csv(f"{OUT}/summary_stats.csv")
means = grouped.mean()
stds = grouped.std()

# 2) Yüzde iyileşme: (fixed - adaptive) / fixed * 100
#    Yüksek olması iyi olan metriklerde işaret ters çevrilir.
rows = []
for scenario in sorted(df["scenario"].unique()):
    for metric in METRICS:
        fixed = means.loc[(scenario, "fixed"), metric]
        adaptive = means.loc[(scenario, "adaptive"), metric]
        if metric in LOWER_BETTER:
            pct = (fixed - adaptive) / fixed * 100
        else:
            pct = (adaptive - fixed) / fixed * 100
        rows.append({
            "scenario": scenario, "metric": metric,
            "fixed": fixed, "adaptive": adaptive, "improvement_pct": pct,
        })

improvement = pd.DataFrame(rows)
improvement.to_csv(f"{OUT}/improvement.csv", index=False)
print(improvement.round(2).to_string(index=False))

# 3) Grafikler: her metrik için senaryo bazında fixed vs adaptive
for metric in METRICS:
    mean_piv = means[metric].unstack("controller")[["fixed", "adaptive"]]
    std_piv = stds[metric].unstack("controller")[["fixed", "adaptive"]].fillna(0)
    ax = mean_piv.plot(kind="bar", yerr=std_piv, capsize=3, figsize=(6, 4))
    ax.set_title(metric)
    ax.set_xlabel("Senaryo")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f"{OUT}/{metric}.png", dpi=150)
    plt.close()

print(f"\nÇıktılar: {OUT}/")