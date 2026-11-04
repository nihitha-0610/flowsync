# ==============================================================================
# FlowSync - Containerized Spark Structured Streaming Runtime
# ==============================================================================
FROM python:3.11-slim-bookworm

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark \
    PYTHONPATH=/app/backend:/app

# Install OpenJDK 17, tini, curl, procps
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    tini \
    curl \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PySpark and streaming dependencies
RUN pip install --no-cache-dir \
    "pyspark==3.5.1" \
    "psycopg[binary]==3.3.6" \
    "pyarrow==26.0.0" \
    "prometheus-client==0.26.0" \
    "pydantic>=2.6.4" \
    "pydantic-settings>=2.2.1" \
    "boto3>=1.34.0" \
    "python-dotenv>=1.0.1" \
    "pytest>=8.0.0" \
    "pytest-asyncio>=0.23.5"

# Download pinned Maven dependencies (Spark Kafka connector and Hadoop AWS S3A bundles)
# Pinned JARs placed directly into PySpark's jars directory
ENV SPARK_JARS_DIR=/usr/local/lib/python3.11/site-packages/pyspark/jars
RUN mkdir -p ${SPARK_JARS_DIR} && \
    curl -fsSL https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar -o ${SPARK_JARS_DIR}/spark-sql-kafka-0-10_2.12-3.5.1.jar && \
    curl -fsSL https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar -o ${SPARK_JARS_DIR}/spark-token-provider-kafka-0-10_2.12-3.5.1.jar && \
    curl -fsSL https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar -o ${SPARK_JARS_DIR}/kafka-clients-3.4.1.jar && \
    curl -fsSL https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar -o ${SPARK_JARS_DIR}/commons-pool2-2.11.1.jar && \
    curl -fsSL https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar -o ${SPARK_JARS_DIR}/hadoop-aws-3.3.4.jar && \
    curl -fsSL https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar -o ${SPARK_JARS_DIR}/aws-java-sdk-bundle-1.12.262.jar

# Expose Spark UI and Prometheus metrics ports
EXPOSE 4040 8000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "streaming.main"]

