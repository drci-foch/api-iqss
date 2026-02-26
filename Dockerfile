FROM python:3.12-bookworm

WORKDIR /api-iqss

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ /api-iqss/data/

EXPOSE 8080

CMD ["python", "./src/main.py"]
