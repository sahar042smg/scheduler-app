FROM python:3.11-slim

WORKDIR /app

# کتابخانه‌های سیستمی لازم برای pandas/ortools
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# دیتابیس SQLite روی یک دیسک دائمی (persistent disk) نگه داشته می‌شود
# تا با هر دیپلوی جدید حساب‌های کاربری پاک نشوند — نگاه کنید به render.yaml.
ENV DATABASE_URL=sqlite:////data/scheduler.db
RUN mkdir -p /data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
