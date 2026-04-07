FROM python:3.11-slim
WORKDIR /app
COPY . /app
COPY ../integration_layer_interface/requirements_ssot.txt /app/requirements_ssot.txt
COPY requirements_cim.txt /app/requirements_cim.txt

RUN pip install --no-cache-dir -r requirements_cim.txt \
    && pip install --no-cache-dir -r requirements_ssot.txt \
    && pip install --no-cache-dir kafka-python loguru

ENV PYTHONPATH=/app:/app/..
