# Lightweight Python 3.11 slim base image
FROM python:3.11-slim

# Enforce clean Python runtime and headless cloud environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    HEADLESS=1

WORKDIR /app

# Install lightweight dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files into container
COPY . /app/

# Expose default HTTP/REST port
EXPOSE 8080

# Health check monitoring built-in /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.getenv('PORT', '8080'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3)" || exit 1

# Launch platform via unified demo runner
CMD ["python", "run_demo.py"]
