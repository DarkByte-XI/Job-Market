from airflow.utils.task_group import TaskGroup
from datetime import timedelta, datetime
from airflow import DAG
from airflow.decorators import task
from pipelines.extract import extract_from_adzuna, extract_from_ft, extract_from_jsearch
from pipelines.load import load_jobs_to_db
from pipelines.transform import (
    transform_jobs)


with DAG("job_market_ETL",
         catchup = False,
         schedule = timedelta(days = 16),
         start_date = datetime(2025, 7, 8)
         ) as etl_dag:

    with TaskGroup("extract") as extract_group:

        @task(task_id = "extract_adzuna")
        def extract_adzuna():
            return extract_from_adzuna()


        @task(task_id = "extract_ft")
        def extract_ft():
            return extract_from_ft()


        @task(task_id = "extract_jsearch")
        def extract_jsearch():
            return extract_from_jsearch()

        extract_adzuna = extract_adzuna()
        extract_ft = extract_ft()
        extract_jsearch = extract_jsearch()


    @task(task_id="transform")
    def transform_raw_jobs():
        return transform_jobs()

    transform = transform_raw_jobs()

    @task(task_id="load_to_database")
    def load_jobs_to_database():
        return load_jobs_to_db()

    load = load_jobs_to_database()

    etl = extract_group >> transform >> load