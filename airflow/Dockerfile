ARG AIRFLOW_BASE_IMAGE=apache/airflow:3.0.2-python3.12
FROM ${AIRFLOW_BASE_IMAGE}

USER ${AIRFLOW_UID}
RUN apt-get update && apt-get install -y libpq-dev build-essential

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt