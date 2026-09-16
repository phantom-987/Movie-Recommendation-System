FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY models/ ./models/

EXPOSE 8000

ENV ALLOWED_ORIGINS="http://localhost:5173"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]