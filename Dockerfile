
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv pip install -e .
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
