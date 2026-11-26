import os
import random

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()
client = clickhouse_connect.get_client(
    host="localhost",
    port=int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
    username=os.environ["CLICKHOUSE_USER"],
    password=os.environ["CLICKHOUSE_PASSWORD"],
    database=os.getenv("CLICKHOUSE_DB", "traffic"),
)
COLS = ["run_id", "scenario", "controller", "seed", "avg_waiting", "avg_queue",
        "avg_speed", "avg_travel_time", "throughput", "total_stops",
        "avg_latency_ms", "p95_latency_ms", "records_per_sec", "co2_mg"]

rows = []
for sc, load in [("S1", 1.0), ("S2", 1.6), ("S3", 1.4)]:
    for ctl, gain in [("fixed", 1.0), ("adaptive", 0.8)]:
        for seed in (11, 22, 33):
            rows.append([
                f"FAKE_{sc}_{ctl}_seed{seed}", sc, ctl, seed,
                30 * load * gain * random.uniform(0.9, 1.1),
                6 * load * gain * random.uniform(0.9, 1.1),
                9 / (load * gain) * random.uniform(0.9, 1.1),
                120 * load * gain * random.uniform(0.9, 1.1),
                int(900 / load / gain * random.uniform(0.95, 1.05)),
                int(1500 * load * gain),
                0.0 if ctl == "fixed" else random.uniform(800, 2500),
                0.0 if ctl == "fixed" else random.uniform(2500, 4500),
                random.uniform(20, 40),
                5e5 * load * gain * random.uniform(0.95, 1.05),
            ])
client.insert("run_summary", rows, column_names=COLS)
print(len(rows), "sahte satır eklendi")