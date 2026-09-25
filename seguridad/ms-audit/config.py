"""Configuración de MS Audit leída desde variables de entorno."""
import os


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

    # --- Detector heurístico de intrusiones (Detect Intrusion) ---
    # La anomalía de comportamiento se calcula como una PROBABILIDAD frecuencial
    # sobre el historial NO anómalo del actor (logica/detector.py): P(normal) =
    # P(país)·P(device) con suavizado de Laplace; score = 1 - P(normal).
    # BOLA es una señal determinista aparte (peso máximo). Ver detector.py.
    DETECCION_UMBRAL = float(os.getenv("DETECCION_UMBRAL", "0.7"))
    DETECCION_ALPHA = float(os.getenv("DETECCION_ALPHA", "1.0"))  # suavizado Laplace
    # Mínimo de conexiones no anómalas del actor para confiar en la señal de
    # comportamiento; por debajo, solo aplica BOLA (evita sobre-marcar con
    # historial escaso).
    DETECCION_MIN_MUESTRAS = int(os.getenv("DETECCION_MIN_MUESTRAS", "3"))

    # --- Auto-siembra del historial normal inicial (arranque en frío) ---
    # ms-audit siembra su propio historial normal al arrancar SOLO si la tabla
    # está vacía (respaldo del seed, que también la llena). Da una línea base
    # desde la primera request sin acoplar la seed al esquema de ms-audit.
    AUTOSEED_N_CLIENTES = int(os.getenv("AUTOSEED_N_CLIENTES", "10"))
    AUTOSEED_CONEXIONES = int(os.getenv("AUTOSEED_CONEXIONES", "5"))
    AUTOSEED_PAIS = os.getenv("AUTOSEED_PAIS", "CO")
    AUTOSEED_DEVICE = os.getenv("AUTOSEED_DEVICE", "desktop-linux")

    CELERY_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "2"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
