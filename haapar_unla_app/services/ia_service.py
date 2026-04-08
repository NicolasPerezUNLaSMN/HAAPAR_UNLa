import json
import os
import random
from openai import OpenAI

from ..models import Sistema, Subsistema, Variable, ActorClave, TendenciaExterna, Influencia, Evaluacion

client = OpenAI(
    api_key=os.getenv("API_KEY_OPENROUTER"),
    base_url="https://openrouter.ai/api/v1"
)


def generar_estructura_prospectiva(tema):

    prompt = f"""
    Sos un experto en prospectiva estratégica.

    Tema: {tema.nombre}
    Descripción: {tema.descripcion}
    Horizonte: {tema.horizonte}
    Territorio: {tema.territorio}

    Generá:

    - 4 subsistemas
    - 4 variables por subsistema
    - 3 actores por subsistema
    - 3 tendencias por subsistema

    Las variables deben clasificarse como:

    I = Interna (factor dentro del sistema)
    E = Externa (factor del entorno)

    Elegí correctamente si cada variable es I o E.

    Respondé SOLO en JSON válido.

    {{
      "subsistemas":[
        {{
          "nombre":"",
          "descripcion":"",
          "variables":[
            {{
              "nombre":"",
              "descripcion":"",
              "tipo":"I o E"
            }}
          ],
          "actores":[
            {{
              "nombre":"",
              "descripcion":"",
              "puesto":""
            }}
          ],
          "tendencias":[
            {{
              "nombre":"",
              "descripcion":""
            }}
          ]
        }}
      ]
    }}
    """

    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4000
    )

    content = response.choices[0].message.content

    print("RESPUESTA IA:")
    print(content)

    # limpiar markdown
    content = content.replace("```json", "").replace("```", "").strip()

    # extraer JSON si viene texto extra
    start = content.find("{")
    end = content.rfind("}") + 1
    content = content[start:end]

    if not content:
        print("La IA devolvió contenido vacío")
        return

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        print("JSON inválido recibido:")
        print(content)
        return

    sistema = Sistema.objects.create(
        tema=tema,
        nombre=f"Sistema de {tema.nombre}",
        descripcion=tema.descripcion
    )

    for s in data.get("subsistemas", []):

        subsistema = Subsistema.objects.create(
            sistema=sistema,
            nombre=s.get("nombre", ""),
            descripcion=s.get("descripcion", ""),
            activo=True
        )

        for v in s.get("variables", []):

            tipo = v.get("tipo", "I")

            # validar tipo permitido
            if tipo not in ["I", "E"]:
                tipo = "I"

            Variable.objects.create(
                subsistema=subsistema,
                nombre=v.get("nombre", ""),
                nombre_corto=v.get("nombre", "")[:40],
                descripcion=v.get("descripcion", ""),
                tipo=tipo,
                activo=True
            )

        for a in s.get("actores", []):

            ActorClave.objects.create(
                subsistema=subsistema,
                nombre=a.get("nombre", ""),
                descripcion=a.get("descripcion", ""),
                puesto=a.get("puesto", ""),
                activo=True
            )

        for t in s.get("tendencias", []):

            TendenciaExterna.objects.create(
                subsistema=subsistema,
                nombre=t.get("nombre", ""),
                nombre_corto=t.get("nombre", "")[:40],
                tipo_dato="texto",
                descripcion=t.get("descripcion", ""),
                activo=True
            )


# --- NUEVA FUNCIÓN FUERA DEL BUCLE ---

# datos dummy no reales
def generar_evaluaciones_e_influencias_dummy(tema, usuario):
    """
    Genera datos aleatorios de prueba para que los gráficos FODA tengan información.
    Esto debe reemplazarse luego por un prompt real a la IA o carga manual.
    """
    variables = Variable.objects.filter(subsistema__sistema__tema=tema)

    for var in variables:
        Evaluacion.objects.create(
            variable=var,
            importancia=random.randint(1, 10),
            incertidumbre=random.randint(1, 10),
            usuario_creador=usuario,
            usuario_modificador=usuario,
            accion='CREADO'
        )

    for var_origen in variables:
        for var_destino in variables:
            if var_origen != var_destino:
                valor_aleatorio = random.choice([0, 0, 1, 1, 2, 3])
                Influencia.objects.create(
                    variable_origen=var_origen,
                    variable_destino=var_destino,
                    valor=valor_aleatorio
                )