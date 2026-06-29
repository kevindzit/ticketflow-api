# Build a small container image for the API.
FROM python:3.12-slim

WORKDIR /app

# install deps first (cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code + the seed script (used by the Kubernetes seed Job)
COPY app ./app
COPY run.py .
COPY scripts ./scripts

# run as a non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

# gunicorn serves the Flask app object "app" from run.py
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "run:app"]
