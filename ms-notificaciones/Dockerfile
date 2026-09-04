# Imagen temporal mientras el equipo define la imagen base oficial.
# Al reemplazarla, mantener el mismo requirements.txt / app.py.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

CMD ["python", "app.py"]
