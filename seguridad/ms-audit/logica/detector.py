"""Detector heurístico de intrusiones de confidencialidad (Detect Intrusion).

Responsabilidad única: dada una sesión (una request), decidir si es intrusión
y por qué, combinando señales. Hoy dos:

1. BOLA (determinista, peso máximo): el customer_id del token difiere del
   solicitado — ms-identidad no los compara (vulnerabilidad deliberada).
2. Comportamiento (probabilístico): qué tan improbable es el país/device de la
   request dado el HISTORIAL NO ANÓMALO del actor. Se estima con frecuencias
   suavizadas (Laplace):

       P(país)  = (veces(país)  + α) / (N + α·(distintos_país  + 1))
       P(device)= (veces(device)+ α) / (N + α·(distintos_device+ 1))
       P(normal)= P(país) · P(device)        (independencia, tipo naive-Bayes)
       score    = 1 − P(normal)              → intrusión si score ≥ umbral

El suavizado evita 0 duros y sobre-marcar con historial escaso; excluir las
conexiones anómalas evita que el atacante envenene la línea base; el mínimo de
muestras hace que con poca historia se dependa solo de BOLA. Todo son counts
sobre una tabla indexada → rápido (ASR1 < 200 ms), determinista y explicable.
"""
from config import Config
from logica.modelos import HistorialConexion


def _prob(veces: int, total: int, distintos: int, alpha: float) -> float:
    return (veces + alpha) / (total + alpha * (distintos + 1))


def _historial_no_anomalo(session, actor: str, excluir_id):
    """Conexiones validadas y NO anómalas del actor (excluye la conexión en
    evaluación, por id, para no contarla como parte de su propia normalidad).
    Se excluye por id y no por request_id porque el historial sembrado tiene
    request_id NULL y una comparación `!= NULL` en SQL lo descartaría.
    """
    consulta = session.query(HistorialConexion).filter(
        HistorialConexion.customer_id_token == actor,
        HistorialConexion.validado.is_(True),
        HistorialConexion.anomala.is_(False),
    )
    if excluir_id is not None:
        consulta = consulta.filter(HistorialConexion.id != excluir_id)
    return consulta.all()


def clasificar_trafico(session, sesion: HistorialConexion) -> str:
    """Etiqueta la sesión por lo que ms-audit observa (para la mezcla de
    tráfico del dashboard): 'rechazada', 'bola', 'anomala_comportamiento' o
    'legitima'. Es una clasificación observada, no ground-truth.
    """
    if not sesion.validado:
        return "rechazada"
    if (
        sesion.customer_id_token
        and sesion.customer_id_token != sesion.customer_id_solicitado
    ):
        return "acceso_no_autorizado"
    es_intrusion, _score, _motivos = evaluar(session, sesion)
    return "anomala_comportamiento" if es_intrusion else "legitima"


def evaluar(session, sesion: HistorialConexion):
    """Devuelve (es_intrusion: bool, score: float, motivos: list[str])."""
    motivos: list[str] = []

    if not sesion.validado:
        # Un rechazo no consuma extracción; no es intrusión de confidencialidad.
        return False, 0.0, motivos

    # Señal 1: BOLA (determinista).
    if (
        sesion.customer_id_token
        and sesion.customer_id_token != sesion.customer_id_solicitado
    ):
        motivos.append(
            f"acceso no autorizado (BOLA): token de "
            f"'{sesion.customer_id_token}' usado para extraer el perfil de "
            f"'{sesion.customer_id_solicitado}'"
        )
        return True, 1.0, motivos

    # Señal 2: comportamiento probabilístico (país/device vs historial del actor).
    actor = sesion.customer_id_token
    if not actor:
        return False, 0.0, motivos

    historial = _historial_no_anomalo(session, actor, sesion.id)
    n = len(historial)
    if n < Config.DETECCION_MIN_MUESTRAS:
        return False, 0.0, motivos  # historial insuficiente → solo BOLA

    paises = [h.pais for h in historial]
    devices = [h.device for h in historial]
    p_pais = _prob(paises.count(sesion.pais), n, len(set(paises)), Config.DETECCION_ALPHA)
    p_device = _prob(devices.count(sesion.device), n, len(set(devices)), Config.DETECCION_ALPHA)
    p_normal = p_pais * p_device
    score = 1.0 - p_normal

    if score >= Config.DETECCION_UMBRAL:
        motivos.append(
            f"comportamiento anómalo: P(normal)={p_normal:.3f} para país "
            f"'{sesion.pais}'/device '{sesion.device}' del actor '{actor}' "
            f"(score {score:.2f} ≥ umbral {Config.DETECCION_UMBRAL}, N={n})"
        )
        return True, score, motivos

    return False, score, motivos
