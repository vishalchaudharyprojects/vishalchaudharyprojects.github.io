FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_aas.txt .
RUN pip install --no-cache-dir -r requirements_aas.txt

# Copy the rest of the application
COPY . .

# Set Python path to include src directory and current directory
ENV PYTHONPATH="/app/src:/app:${PYTHONPATH}"

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5002

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:5002/health || exit 1

CMD ["python", "app.py"]