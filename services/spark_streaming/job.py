import os
import clickhouse_connect
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField, StringType,
                               IntegerType, DoubleType)

BOOTSTRAP = os.environ["KAFKA_INTERNAL_BOOTSTRAP"]
TOPIC_RAW = os.environ["TOPIC_RAW"]
TOPIC_METRICS = os.environ["TOPIC_METRICS"]
WINDOW = os.environ.get("SPARK_WINDOW", "10 seconds")
SLIDE = os.environ.get("SPARK_SLIDE", "5 seconds")
WATERMARK = os.environ.get("SPARK_WATERMARK", "5 seconds")

CH_HOST = os.environ["CLICKHOUSE_HOST"]
CH_PORT = int(os.environ["CLICKHOUSE_HTTP_PORT_INTERNAL"])
CH_USER = os.environ["CLICKHOUSE_USER"]
CH_PASS = os.environ["CLICKHOUSE_PASSWORD"]
CH_DB = os.environ["CLICKHOUSE_DB"]

spark = SparkSession.builder.appName("traffic-streaming").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("run_id", StringType()),
    StructField("scenario", StringType()),
    StructField("controller", StringType()),
    StructField("seed", IntegerType()),
    StructField("sim_time", DoubleType()),
    StructField("tls_id", StringType()),
    StructField("lane_id", StringType()),
    StructField("queue_length", DoubleType()),
    StructField("waiting_time", DoubleType()),
    StructField("mean_speed", DoubleType()),
    StructField("occupancy", DoubleType()),
    StructField("produced_ts", DoubleType()),
])

raw = (spark.readStream.format("kafka")
       .option("kafka.bootstrap.servers", BOOTSTRAP)
       .option("subscribe", TOPIC_RAW)
       .option("startingOffsets", "latest")
       .load())

parsed = (raw.select(F.from_json(F.col("value").cast("string"), schema).alias("d"))
          .select("d.*")
          .withColumn("event_time", F.col("produced_ts").cast("timestamp")))

metrics = (parsed
           .withWatermark("event_time", WATERMARK)
           .groupBy(F.window("event_time", WINDOW, SLIDE),
                    "run_id", "scenario", "controller", "seed", "tls_id")
           .agg(F.avg("queue_length").alias("avg_queue"),
                F.max("queue_length").alias("max_queue"),
                F.avg("waiting_time").alias("avg_waiting"),
                F.avg("mean_speed").alias("avg_speed"),
                F.avg("occupancy").alias("avg_occupancy"),
                F.count("*").alias("record_count"),
                F.max("produced_ts").alias("max_produced_ts"))
           .select("run_id", "scenario", "controller", "seed", "tls_id",
                   F.col("window.start").alias("window_start"),
                   F.col("window.end").alias("window_end"),
                   "avg_queue", "max_queue", "avg_waiting", "avg_speed",
                   "avg_occupancy", "record_count", "max_produced_ts"))


def write_batch(df, batch_id):
    if df.rdd.isEmpty():
        return
    df = df.withColumn("processed_ts", F.current_timestamp().cast("double"))
    df.persist()
    # 1) Kafka'ya (karar servisi buradan okuyacak)
    (df.select(F.col("tls_id").alias("key"),
               F.to_json(F.struct(*df.columns)).alias("value"))
       .write.format("kafka")
       .option("kafka.bootstrap.servers", BOOTSTRAP)
       .option("topic", TOPIC_METRICS)
       .save())
    # 2) ClickHouse'a
    pdf = df.toPandas()
    client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT,
                                           username=CH_USER, password=CH_PASS,
                                           database=CH_DB)
    client.insert_df("traffic_metrics", pdf)
    df.unpersist()


query = (metrics.writeStream
         .outputMode("append")
         .foreachBatch(write_batch)
         .option("checkpointLocation", "/tmp/checkpoints/metrics")
         .start())
query.awaitTermination()