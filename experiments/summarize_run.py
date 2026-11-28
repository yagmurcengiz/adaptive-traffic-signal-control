"""Bir koşu bitince run_summary tablosuna tek satır yazar.

Kullanım:
    python experiments/summarize_run.py RUN_ID
    python experiments/summarize_run.py RUN_ID --tripinfo path/to/tripinfo.xml
    python experiments/summarize_run.py RUN_ID --force      # mevcut satırın üzerine yaz

ClickHouse'tan hesaplananlar:
    avg_waiting, avg_queue, avg_speed   (traffic_metrics, kayıt sayısıyla ağırlıklı)
    avg_latency_ms, p95_latency_ms      (control_events)
    records_per_sec                     (traffic_metrics, pencere başına ortalama)

SUMO tripinfo dosyasından gelenler (--tripinfo verilirse):
    avg_travel_time, throughput, total_stops, co2_mg
Dosya verilmezse bu dört alan 0 yazılır.
"""
import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET

import clickhouse_connect
from dotenv import load_dotenv

COLS = [
    "run_id", "scenario", "controller", "seed",
    "avg_waiting", "avg_queue", "avg_speed", "avg_travel_time",
    "throughput", "total_stops", "avg_latency_ms", "p95_latency_ms",
    "records_per_sec", "co2_mg",
]


def get_client():
    load_dotenv()
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST_LOCAL", "localhost"),
        port=int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=os.getenv("CLICKHOUSE_DB", "traffic"),
    )


def clean(value):
    """NaN/None değerlerini 0.0 yap."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return float(value)


def traffic_stats(client, run_id):
    row = client.query(
        """
        SELECT any(scenario), any(controller), any(seed),
               sum(avg_waiting * record_count) / sum(record_count),
               sum(avg_queue * record_count) / sum(record_count),
               sum(avg_speed * record_count) / sum(record_count),
               count()
        FROM traffic_metrics
        WHERE run_id = {r:String}
        """,
        parameters={"r": run_id},
    ).result_rows[0]
    if row[6] == 0:
        sys.exit(f"'{run_id}' için traffic_metrics içinde satır yok.")
    return row


def records_per_sec(client, run_id):
    """Pencere başına saniyedeki kayıt sayısının ortalaması.

    Pencereler kayar (üst üste biner), bu yüzden toplam kaydı süreye
    bölmek yerine her pencerenin kendi hızını ortalıyoruz.
    """
    row = client.query(
        """
        SELECT avg(rate) FROM (
            SELECT sum(record_count) / greatest(1, dateDiff('second', window_start, window_end)) AS rate
            FROM traffic_metrics
            WHERE run_id = {r:String}
            GROUP BY window_start, window_end
        )
        """,
        parameters={"r": run_id},
    ).result_rows[0]
    return clean(row[0])


def latency_stats(client, run_id):
    row = client.query(
        """
        SELECT avg((applied_ts - trigger_produced_ts) * 1000),
               quantile(0.95)((applied_ts - trigger_produced_ts) * 1000),
               count()
        FROM control_events
        WHERE run_id = {r:String}
        """,
        parameters={"r": run_id},
    ).result_rows[0]
    if row[2] == 0:  # fixed-time koşularında karar olayı yoktur
        return 0.0, 0.0
    return clean(row[0]), clean(row[1])


def tripinfo_stats(path):
    """SUMO tripinfo çıktısından seyahat süresi, throughput, duruş ve CO2."""
    durations, stops, co2 = [], 0, 0.0
    for trip in ET.parse(path).getroot().iter("tripinfo"):
        durations.append(float(trip.get("duration", 0)))
        stops += int(float(trip.get("waitingCount", 0)))
        emissions = trip.find("emissions")
        if emissions is not None:
            co2 += float(emissions.get("CO2_abs", 0))
    if not durations:
        return 0.0, 0, 0, 0.0
    return sum(durations) / len(durations), len(durations), stops, co2


def main():
    parser = argparse.ArgumentParser(description="run_summary satırı üretir")
    parser.add_argument("run_id")
    parser.add_argument("--tripinfo", help="SUMO tripinfo XML dosyası")
    parser.add_argument("--force", action="store_true", help="mevcut satırın üzerine yaz")
    args = parser.parse_args()

    client = get_client()

    exists = client.query(
        "SELECT count() FROM run_summary WHERE run_id = {r:String}",
        parameters={"r": args.run_id},
    ).result_rows[0][0]
    if exists and not args.force:
        sys.exit(f"'{args.run_id}' zaten run_summary içinde. Üzerine yazmak için --force kullan.")

    scenario, controller, seed, waiting, queue, speed, _ = traffic_stats(client, args.run_id)
    rps = records_per_sec(client, args.run_id)
    avg_lat, p95_lat = latency_stats(client, args.run_id)

    travel, throughput, stops, co2 = 0.0, 0, 0, 0.0
    if args.tripinfo:
        travel, throughput, stops, co2 = tripinfo_stats(args.tripinfo)
    else:
        print("Uyarı: --tripinfo verilmedi, seyahat süresi/throughput/duruş/CO2 = 0")

    if exists and args.force:
        client.command(
            "ALTER TABLE run_summary DELETE WHERE run_id = {r:String} SETTINGS mutations_sync = 1",
            parameters={"r": args.run_id},
        )

    row = [
        args.run_id, scenario, controller, int(seed),
        clean(waiting), clean(queue), clean(speed), travel,
        throughput, stops, avg_lat, p95_lat, rps, co2,
    ]
    client.insert("run_summary", [row], column_names=COLS)

    print(f"run_summary yazıldı: {args.run_id}")
    for name, value in zip(COLS, row):
        print(f"  {name}: {value}")


if __name__ == "__main__":
    main()