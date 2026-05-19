import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargamos las variables de entorno usando dotenv
load_dotenv(override=True)

def get_ai_client():
    """Configura el cliente de IA dependiendo del proveedor elegido en el .env"""
    provider = os.getenv("AI_PROVIDER", "openrouter").lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None  # Usa la oficial de OpenAI
        default_model = "gpt-3.5-turbo"
        if not api_key:
            logger.warning("Falta OPENAI_API_KEY en el .env")
    else:
        api_key = os.getenv("API_KEY_OPENROUTER")
        base_url = "https://openrouter.ai/api/v1"
        default_model = "meta-llama/llama-3.1-8b-instruct"
        if not api_key:
            logger.warning("Falta API_KEY_OPENROUTER en el .env")

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, default_model

def generar_respuesta_llm(prompt, temperature=0.7, max_tokens=4000):
    """Función unificada para pedirle texto a la IA"""
    client, model = get_ai_client()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return {
            'success': True,
            'text': response.choices[0].message.content.strip()
        }
    except Exception as e:
        logger.error(f"Error de conexión con la IA ({model}): {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }