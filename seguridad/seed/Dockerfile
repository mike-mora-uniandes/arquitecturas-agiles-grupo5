# Servicio one-shot: puebla las 3 bases PostgreSQL con datos dummy (Faker)
# antes de correr el experimento. No es un servicio de larga duración.
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

WORKDIR /seed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /seed/

CMD ["python", "generar_seed.py"]
