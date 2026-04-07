FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libsnmp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements_typhoon.txt .
RUN pip install --no-cache-dir -r requirements_typhoon.txt

# Copy application
COPY . .

# Set environment variables
ENV FLASK_APP=app:app
ENV FLASK_ENV=production
ENV PORT=5004

EXPOSE 5004

# Directly run the app without editable install
CMD ["python", "app.py"]