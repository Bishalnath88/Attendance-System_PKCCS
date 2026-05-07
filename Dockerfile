FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# copy and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . /app

# Expose port and run with gunicorn for production
ENV PORT=5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2"]
