import time
import random
import logging

logger = logging.getLogger(__name__)

def retry_with_backoff(func, max_retries=3, base_delay=1, max_delay=10, *args, **kwargs):
    """
    Ejecuta una función con reintentos exponenciales en caso de excepción.
    
    :param func: función a ejecutar
    :param max_retries: número máximo de reintentos
    :param base_delay: tiempo inicial de espera en segundos
    :param max_delay: tiempo máximo de espera en segundos
    :param args: argumentos posicionales para la función
    :param kwargs: argumentos nombrados para la función
    :return: resultado de la función si tiene éxito
    :raises: la última excepción si se superan los reintentos
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            sleep_time = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 1)
            logger.warning(f"Error: {e}. Reintentando en {sleep_time:.2f} segundos...")
            time.sleep(sleep_time)
    raise Exception("Max retries exceeded")
