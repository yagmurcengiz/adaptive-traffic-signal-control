import os

import clickhouse_connect
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

# Düşük olması iyi olanlar / yüksek olması iyi olanlar
LOWER_BETTER = ["avg_waiting", "avg_queue", "avg_travel_time", "total_stops", "co2_mg"]
HIGHER_BETTER = ["avg_speed", "throughput"]
METRICS = LOWER_BETTER + HIGHER_BETTER

# 1) Senaryo x kontrol bazında ortalama ve standart sapma
stats = df.groupby(["scenario", "controller"])[METRICS].agg(["mean", "std"])
stats.to_csv(f"{OUT}/summary_stats.csv")

# 2) Yüzde iyileşme
means = df.groupby(["scenario", "controller"])[METRICS].mean()
rows = []
for sc in sorted(df["scenario"].unique()):
    for m in METRICS:
        fixed = means.loc[(sc, "fixed"), m]
        adap = means.loc[(sc, "adaptive"), m]
        pct = (fixed - adap) / fixed * 100 if m in LOWER_BETTER else (adap - fixed) / fixed * 100
        rows.append({"scenario": sc, "metric": m, "fixed": fixed,
                     "adaptive": adap, "improvement_pct": pct})
imp = pd.DataFrame(rows)
imp.to_csv(f"{OUT}/improvement.csv", index=False)
print(imp.round(2).to_string(index=False))

# 3) Grafikler: her metrik için senaryo bazlı fixed vs adaptive
for m in METRICS:
    piv_mean = means[m].unstack("controller")
    piv_std = df.groupby(["scenario", "controller"])[m].std().unstack("controller")
    ax = piv_mean[["fixed", "adaptive"]].plot(
        kind="bar", yerr=piv_std[["fixed", "adaptive"]], capsize=3, figsize=(6, 4))
    ax.set_title(m)
    ax.set_xlabel("Senaryo")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f"{OUT}/{m}.png", dpi=150)
    plt.close()
print("Çıktılar:", OUT)