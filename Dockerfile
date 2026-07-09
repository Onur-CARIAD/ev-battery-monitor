FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/
COPY README.md ./

RUN pip install --no-cache-dir .

USER app

CMD ["python", "-m", "ev_battery_monitor.main"]
