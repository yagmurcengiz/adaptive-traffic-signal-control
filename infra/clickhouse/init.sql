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
    max_produced_ts Float64
)
ENGINE = MergeTree
ORDER BY (run_id, tls_id, window_start);

CREATE TABLE IF NOT EXISTS traffic.control_events
(
    run_id String,
    tls_id String,
    old_plan String,
    new_plan String,
    decision_ts Float64,
    applied_ts Float64
)
ENGINE = MergeTree
ORDER BY (run_id, tls_id, decision_ts);