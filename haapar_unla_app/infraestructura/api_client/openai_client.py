import os
from typing import Any, Dict

try:
    import openai
except Exception:  # pragma: no cover - handled at runtime
    openai = None


def _get_api_key() -> str | None:
    return os.environ.get('OPENAI_API_KEY')


def generate_chat_completion(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 512, temperature: float = 0.7) -> Dict[str, Any]:
    """Llama a la API de Chat completions (chatGPT) y devuelve un dict con el resultado.

    Retorna:
      {"success": True, "text": str, "raw": <response>} o
      {"success": False, "error": str}
    """
    api_key = _get_api_key()
    if openai is None:
        return {"success": False, "error": "openai package no está instalado"}
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY no configurada en variables de entorno"}

    openai.api_key = api_key

    try:
        # Intentar la interfaz clásica (openai<1.0)
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as e:
        # Si falla (por ejemplo openai>=1.0 no soporta ChatCompletion), intentar
        # usar la nueva interfaz `OpenAI` (chat.completions o responses).
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            try:
                # intentar chat completions (1.x)
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except Exception:
                # fallback a Responses API
                resp = client.responses.create(
                    model=model,
                    input=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
        except Exception:
            # No se pudo invocar la nueva API, devolver el error original
            return {"success": False, "error": str(e)}
        pass
    # Si llegamos aquí `resp` debe contener la respuesta del cliente (viejo o nuevo).
    try:
        # Extraer la respuesta de forma robusta. Dependiendo de la versión
        # del cliente OpenAI la respuesta puede ser indexable como dict o
        # como OpenAIObject con atributos.
        text = ""
        try:
            # Intentar acceso estilo dict (resp['choices'][0]['message']['content'])
            text = resp['choices'][0]['message']['content']
        except Exception:
            try:
                # Intentar acceso estilo objeto (resp.choices[0].message['content'])
                text = resp.choices[0].message['content']
            except Exception:
                try:
                    # Otra variante posible: message es dict-like en choices[0]
                    text = resp.choices[0]['message']['content']
                except Exception:
                    # Fallback final: intentar otras formas (Responses API)
                    try:
                        if hasattr(resp, 'output'):
                            out = resp.output
                            try:
                                text = out[0]['content'][0]['text']
                            except Exception:
                                text = str(out)
                        elif 'output' in resp:
                            text = resp['output'][0]['content'][0]['text']
                        elif hasattr(resp, 'generations'):
                            text = resp.generations[0][0].text
                        else:
                            text = str(resp)
                    except Exception:
                        text = str(resp)

        # Normalizar a str y limpiar espacios
        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8')
            except Exception:
                text = str(text)
        text = str(text).strip()
        return {"success": True, "text": text, "raw": resp}
    except Exception as e:
        return {"success": False, "error": str(e)}
