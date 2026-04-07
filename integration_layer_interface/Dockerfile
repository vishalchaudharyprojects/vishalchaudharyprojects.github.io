FROM python:3.11-slim

WORKDIR /integration_layer_interface

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_ssot.txt .
RUN pip install --no-cache-dir -r requirements_ssot.txt

# Copy the application code
COPY . .

# Install in development mode (if setup.py exists)
RUN pip install -e .

# Set Python path
ENV PYTHONPATH="/integration_layer_interface:${PYTHONPATH}"

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5001

# Expose the port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

CMD ["python", "app.py"]