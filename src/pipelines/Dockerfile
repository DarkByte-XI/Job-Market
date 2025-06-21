FROM python:3.12-slim
LABEL authors="dani"
WORKDIR /src/pipelines
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src/ /src/
CMD ["python", "main.py"]