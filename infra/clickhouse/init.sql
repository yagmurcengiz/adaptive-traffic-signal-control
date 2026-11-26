CREATE TABLE IF NOT EXISTS traffic.traffic_metrics
(
    run_id String,
    scenario String,
    controller String,
    seed UInt32,
    tls_id String,
    window_start DateTime64(3),
    window_end DateTime64(3),
    avg_queue Float64,
    max_queue Float64,
    avg_waiting Float64,
    avg_speed Float64,
    avg_occupancy Float64,
    record_count UInt32,
    max_produced_ts Float64,
    processed_ts Float64
)
ENGINE = MergeTree
ORDER BY (run_id, tls_id, window_start);

CREATE TABLE IF NOT EXISTS traffic.control_events
(
    run_id String,
    tls_id String,
    old_plan String,
    new_plan String,
    trigger_produced_ts Float64,
    decision_ts Float64,
    applied_ts Float64
)
ENGINE = MergeTree
ORDER BY (run_id, tls_id, decision_ts);

CREATE TABLE IF NOT EXISTS traffic.run_summary
(
    run_id String,
    scenario String,
    controller String,
    seed UInt32,
    avg_waiting Float64,
    avg_queue Float64,
    avg_speed Float64,
    avg_travel_time Float64,
    throughput UInt32,
    total_stops UInt32,
    avg_latency_ms Float64,
    p95_latency_ms Float64,
    records_per_sec Float64,
    co2_mg Float64
)
ENGINE = MergeTree
ORDER BY (scenario, controller, seed);