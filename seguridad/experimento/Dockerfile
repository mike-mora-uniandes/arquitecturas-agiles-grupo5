FROM locustio/locust:2.31.5

WORKDIR /tmp
COPY locust-requirements.txt /tmp/locust-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/locust-requirements.txt
