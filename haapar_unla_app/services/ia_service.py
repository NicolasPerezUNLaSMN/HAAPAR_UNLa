import json
import os
from openai import OpenAI

from ..models import Sistema, Subsistema, Variable, ActorClave, TendenciaExterna

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

    Respondé SOLO en JSON:

    {{
      "subsistemas":[
        {{
          "nombre":"",
          "descripcion":"",
          "variables":[
            {{
              "nombre":"",
              "descripcion":"",
              "tipo":""
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
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()

    data = json.loads(content)

    sistema = Sistema.objects.create(
        tema=tema,
        nombre=f"Sistema de {tema.nombre}",
        descripcion=tema.descripcion
    )

    for s in data["subsistemas"]:

        subsistema = Subsistema.objects.create(
            sistema=sistema,
            nombre=s["nombre"],
            descripcion=s["descripcion"],
            activo=True
        )

        for v in s.get("variables", []):
            Variable.objects.create(
                subsistema=subsistema,
                nombre=v["nombre"],
                nombre_corto=v["nombre"][:40],
                descripcion=v["descripcion"],
                tipo=v["tipo"],
                activo=True
            )

        for a in s.get("actores", []):
            ActorClave.objects.create(
                subsistema=subsistema,
                nombre=a["nombre"],
                descripcion=a["descripcion"],
                puesto=a["puesto"],
                activo=True
            )

        for t in s.get("tendencias", []):
            TendenciaExterna.objects.create(
                subsistema=subsistema,
                nombre=t["nombre"],
                nombre_corto=t["nombre"][:40],
                tipo_dato="texto",
                descripcion=t["descripcion"],
                activo=True
            )