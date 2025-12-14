FROM python:3.12-slim

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN mkdir /media/photos

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
