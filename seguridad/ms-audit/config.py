"""Configuración de MS Audit leída desde variables de entorno."""
import os


def _lista(valor: str) -> list[str]:
    """Convierte una variable 'a,b,c' en ['a','b','c'] (sin vacíos)."""
    return [x.strip() for x in valor.split(",") if x.strip()]


class Config:
    # HistorialRegistrosUsuario + HistorialConexion + incidentes — PostgreSQL
    # propio. Nombre de variable específico — el .env se comparte entre los 5
    # servicios (ver la misma nota en ../ms-riesgo/config.py).
    DATABASE_URL = os.getenv(
        "AUDIT_DATABASE_URL", "postgresql://solventa:solventa@ms-audit-db:5432/audit"
    )

    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")

    # --- Consume: ReporteSesionAccion (de ms-identidad) ---
    SESION_ACCION_QUEUE = os.getenv("SESION_ACCION_QUEUE", "audit.sesion_accion.q")
    SESION_ACCION_ROUTING_KEY = os.getenv(
        "SESION_ACCION_ROUTING_KEY", "identidad.sesion_accion"
    )
    SESION_ACCION_TASK_NAME = os.getenv(
        "SESION_ACCION_TASK_NAME", "audit.registrar_sesion_accion"
    )

    # --- Consume: ReporteExtraccionPerfilRiesgoCliente (de ms-riesgo) ---
    EXTRACCION_QUEUE = os.getenv("EXTRACCION_QUEUE", "audit.extraccion_perfil.q")
    EXTRACCION_ROUTING_KEY = os.getenv(
        "EXTRACCION_ROUTING_KEY", "riesgo.extraccion_perfil"
    )
    EXTRACCION_TASK_NAME = os.getenv(
        "EXTRACCION_TASK_NAME", "audit.registrar_extraccion_perfil"
    )

    # --- Consume: IntegridadFallida (de ms-cliente) ---
    # El incidente de integridad se detecta inline en ms-cliente (verifica el
    # hash del perfil). Como ms-cliente no persiste ni notifica, publica este
    # evento ligero al broker y ms-audit centraliza métrica + notificación,
    # manteniendo el invariante "solo ms-audit emite incidentes" del diseño.
    INTEGRIDAD_QUEUE = os.getenv("INTEGRIDAD_QUEUE", "audit.integridad_fallida.q")
    INTEGRIDAD_ROUTING_KEY = os.getenv(
        "INTEGRIDAD_ROUTING_KEY", "cliente.integridad_fallida"
    )
    INTEGRIDAD_TASK_NAME = os.getenv(
        "INTEGRIDAD_TASK_NAME", "audit.registrar_integridad_fallida"
    )

    # --- Produce: NotificacionIncidenteSeguridad (lo consume ms-notificaciones) ---
    INCIDENTE_ROUTING_KEY = os.getenv(
        "INCIDENTE_ROUTING_KEY", "audit.incidente_seguridad"
    )
    NOTIFICAR_INCIDENTE_TASK_NAME = os.getenv(
        "NOTIFICAR_INCIDENTE_TASK_NAME", "notificaciones.notificar_incidente"
    )

    # --- Umbrales de los ASR de detección (para la señal de cumplimiento) ---
    # ASR1 (confidencialidad): detectar la extracción no autorizada en < 200 ms.
    ASR1_UMBRAL_MS = float(os.getenv("ASR1_UMBRAL_MS", "200"))
    # ASR2 (integridad): detectar la alteración no autorizada en < 500 ms.
    ASR2_UMBRAL_MS = float(os.getenv("ASR2_UMBRAL_MS", "500"))

    # --- Señales del clasificador de intrusiones (Detect Intrusion) ---
    # País/device del atacante simulados con datos dummy (ver
    # ../../experimento/forjar_token.py y ../../seed/). No es GeoIP real:
    # una lista de bloqueo configurable materializa "contexto anómalo".
    PAISES_ANOMALOS = _lista(os.getenv("PAISES_ANOMALOS", "IR,KP,SY"))
    DEVICES_ANOMALOS = _lista(os.getenv("DEVICES_ANOMALOS", "unknown-device"))

    # Ventana de correlación: una sesión sospechosa y una extracción se
    # consideran parte del mismo patrón si ocurren dentro de esta ventana.
    VENTANA_CORRELACION_S = int(os.getenv("VENTANA_CORRELACION_S", "60"))

    CELERY_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "2"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
