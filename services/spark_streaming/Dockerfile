FROM apache/spark:3.5.3-python3
USER root
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /app
COPY job.py /app/job.py
USER spark
CMD ["/opt/spark/bin/spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3", \
     "--conf", "spark.jars.ivy=/tmp/.ivy", \
     "/app/job.py"]