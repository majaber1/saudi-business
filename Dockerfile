FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY financial-engine/ ./financial-engine/
COPY funding-engine/ ./funding-engine/
COPY database/ ./database/

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
