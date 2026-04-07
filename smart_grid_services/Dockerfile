# smart_grid_services/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libxml2-dev libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements_se.txt /app/requirements_se.txt
RUN pip install --no-cache-dir -r requirements_se.txt

COPY src/ /app/

EXPOSE 5003
ENV PYTHONPATH=/app
ENV PYTHONPATH="/app/libs/cimpy_3:${PYTHONPATH}"
CMD ["python", "app.py"]
