FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose web service port
EXPOSE 8005

ENV PORT=8005
ENV HOST=0.0.0.0
ENV SKIP_VENV_BOOTSTRAP=1

CMD ["python", "-u", "server.py"]
