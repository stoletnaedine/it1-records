FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -q -r requirements.txt

COPY . .

# Отключи веб-сервер
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]