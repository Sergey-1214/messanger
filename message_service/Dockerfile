FROM python:3.12

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=100

ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.message_service.main:app", "--host", "0.0.0.0", "--port", "8000"]