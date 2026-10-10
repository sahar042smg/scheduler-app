FROM python:3.11-slim

WORKDIR /app

# کتابخانه‌های سیستمی لازم برای pandas/ortools
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# DATABASE_URL از متغیر محیطی تزریق می‌شود (در Render به یک دیتابیس
# Postgres خارجی مثل Neon وصل می‌شود تا داده با هر ری‌استارت پاک
# نشود — دیسک این سرویس دائمی نیست). پیش‌فرض پایین فقط برای جلوگیری
# از کرش احتمالی است؛ در عمل همیشه باید override شود.
ENV DATABASE_URL=sqlite:///./scheduler.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
