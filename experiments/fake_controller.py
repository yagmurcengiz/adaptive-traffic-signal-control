import os
import random
import time

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

RUN_ID = "fake_run"
plans = {"K1": "A", "K2": "A", "K3": "A"}
COLS = ["run_id", "tls_id", "old_plan", "new_plan",
        "trigger_produced_ts", "decision_ts", "applied_ts"]

try:
    while True:
        tls = random.choice(list(plans))
        old = plans[tls]
        new = random.choice([p for p in "ABC" if p != old])
        now = time.time()
        trigger = now - random.uniform(1.0, 3.0)
        decision = trigger + random.uniform(0.5, 2.0)
        applied = decision + random.uniform(0.05, 0.5)
        client.insert("control_events",
                      [[RUN_ID, tls, old, new, trigger, decision, applied]],
                      column_names=COLS)
        plans[tls] = new
        print(f"{tls}: {old} -> {new}  gecikme={(applied - trigger) * 1000:.0f} ms")
        time.sleep(random.uniform(5, 15))
except KeyboardInterrupt:
    pass