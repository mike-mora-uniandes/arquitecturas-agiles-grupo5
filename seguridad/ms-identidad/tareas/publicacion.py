"""Publicación de ReporteSesionAccion al broker (Celery/Kombu)."""
from datetime import datetime, timezone

from config import Config
from extensiones import celery_app


def publicar_reporte_sesion(
    *, customer_id_token, customer_id_solicitado, validado,
    ip=None, device=None, pais=None, request_id=None,
):
    """Publica el reporte de sesión/acción. Se llama en cada intento de
    ValidarUsuario, exitoso o rechazado — ms-audit necesita ambos para
    correlacionar patrones. `request_id` empareja esta sesión con su extracción.
    """
    evento = {
        "customer_id_token": customer_id_token,
        "customer_id_solicitado": customer_id_solicitado,
        "validado": validado,
        "ip": ip,
        "device": device,
        "pais": pais,
        "request_id": request_id,
        "reportado_en": datetime.now(timezone.utc).isoformat(),
    }

    celery_app.send_task(
        Config.SESION_ACCION_TASK_NAME,
        [evento],
        exchange=Config.RABBITMQ_EXCHANGE,
        routing_key=Config.SESION_ACCION_ROUTING_KEY,
        retry=True,
    )

    return evento
