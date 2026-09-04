import logging
import os

import pika

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("ms-notificaciones")

RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_USER = os.environ["RABBITMQ_USER"]
RABBITMQ_PASSWORD = os.environ["RABBITMQ_PASSWORD"]
QUEUE_NAME = "resultado-evaluacion-perfil"


def on_message(channel, method, properties, body):
    logger.info("ResultadoEvaluacionPerfil recibido: %s", body.decode())
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)
    logger.info("Escuchando la cola '%s'...", QUEUE_NAME)
    channel.start_consuming()


if __name__ == "__main__":
    main()
