FROM python:3.12-slim
LABEL authors="dani"
WORKDIR /src/job_market_app
COPY requirements.txt .
COPY ./src/ /src/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]