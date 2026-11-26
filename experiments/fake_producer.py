import json
import os
import random
import time
from confluent_kafka import Producer

p = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")})
TOPIC = os.getenv("TOPIC_RAW", "traffic.raw")
LANES = {"K1": ["K1_n_0", "K1_s_0"], "K2": ["K2_n_0", "K2_s_0"], "K3": ["K3_n_0", "K3_s_0"]}

sim_time = 0
try:
    while True:
        for tls, lanes in LANES.items():
            for lane in lanes:
                msg = {
                    "run_id": "fake_run",
                    "scenario": "S1",
                    "controller": "fixed",
                    "seed": 11,
                    "sim_time": sim_time,
                    "tls_id": tls,
                    "lane_id": lane,
                    "queue_length": random.randint(0, 20),
                    "waiting_time": round(random.uniform(0, 60), 2),
                    "mean_speed": round(random.uniform(0, 14), 2),
                    "occupancy": round(random.uniform(0, 1), 3),
                    "produced_ts": time.time(),
                }
                p.produce(TOPIC, json.dumps(msg).encode("utf-8"))
        p.poll(0)
        sim_time += 1
        time.sleep(1)
except KeyboardInterrupt:
    p.flush()