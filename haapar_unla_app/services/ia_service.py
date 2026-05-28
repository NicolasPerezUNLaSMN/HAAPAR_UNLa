import json
import logging
import re

from ..models import (
    PESTEL,
    ActorClave,
    EvaluacionVariable,
    Historial,
    IAInteraction,
    Influencia,
    Sistema,
    Subsistema,
    TendenciaExterna,
    Variable,
)
from .ai_client import generar_respuesta_llm

logger = logging.getLogger(__name__)


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
    
    IMPORTANTE PARA LAS VARIABLES:
    Las variables deben ser CUANTIFICABLES, es decir, deben poder medirse numéricamente.
    El nombre de cada variable debe incluir una métrica clara o unidad (Porcentaje (%), Tasa, Cantidad, Índice, Nivel).
    NO usar nombres abstractos como "Economía", "Tecnología".

    Clasificación del Entorno:
    tipo: "I" (Interna) o "E" (Externa).

    Clasificación PESTEL (OBLIGATORIO Y DIVERSO):
    Asigná cada variable a uno de los siguientes códigos PESTEL según su naturaleza:
    - "P" (Político)
    - "EC" (Económico)
    - "S" (Social)
    - "T" (Tecnológico)
    - "EO" (Ecológico)
    - "L" (Legal)
    
    🚨 REGLA CRÍTICA: ¡NO repitas la misma categoría PESTEL para todas las variables de un subsistema! 
    Tiene que haber una ALTA VARIEDAD de categorías (P, EC, S, T, EO, L) distribuidas de forma heterogénea. 🚨

    Las tendencias deben ser de dos tipos:
    - CUANTITATIVA o CUALITATIVA

    Respondé SOLO en JSON válido sin texto extra de la siguiente forma:

    {{
        "subsistemas":[
            {{
            "nombre":"",
            "descripcion":"",
            "variables":[
                {{
                "nombre":"",
                "descripcion":"",
                "tipo":"I o E",
                "pestel": ["Código PESTEL aquí (ej: P o EC)"]
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
                "descripcion":"",
                "tipo":"CUALITATIVA o CUANTITATIVA"
                }}
            ]
            }}
        ]
    }}
    """

    logger.info("Enviando solicitud de estructura a la IA...")
    resultado = generar_respuesta_llm(prompt, temperature=0.7)

    IAInteraction.objects.create(
        tema=tema,
        usuario=None,
        prompt=prompt,
        respuesta=resultado.get("text"),
        success=resultado.get("success", False),
        error=resultado.get("error"),
    )

    if not resultado.get("success"):
        logger.error(f"La IA falló al estructurar: {resultado.get('error')}")
        return

    content = resultado.get("text")
    content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}") + 1
    content = content[start:end]

    if not content:
        logger.error("La IA devolvió contenido vacío")
        return

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("JSON inválido recibido:")
        return

    sistema = Sistema.objects.create(
        tema=tema, nombre=f"Sistema de {tema.nombre}", descripcion=tema.descripcion
    )

    for s in data.get("subsistemas", []):
        subsistema = Subsistema.objects.create(
            sistema=sistema,
            nombre=s.get("nombre", ""),
            descripcion=s.get("descripcion", ""),
            activo=True,
        )

        for v in s.get("variables", []):
            tipo = v.get("tipo", "I")
            if tipo not in ["I", "E"]:
                tipo = "I"

            variable = Variable.objects.create(
                subsistema=subsistema,
                nombre=v.get("nombre", ""),
                nombre_corto=v.get("nombre", "")[:40],
                descripcion=v.get("descripcion", ""),
                tipo=tipo,
                activo=True,
            )

            # Sincronización Automática PESTEL generada por IA
            ai_pestel_codes = v.get("pestel", [])
            if isinstance(ai_pestel_codes, str):
                ai_pestel_codes = [ai_pestel_codes]

            for code in ai_pestel_codes:
                clean_code = str(code).upper().strip()
                if clean_code in ["P", "EC", "S", "T", "EO", "L"]:
                    pestel_obj, _ = PESTEL.objects.get_or_create(tipo=clean_code)
                    variable.pestels.add(pestel_obj)

            Historial.objects.create(variable=variable, accion="CREADO", usuario=None)

        for a in s.get("actores", []):
            ActorClave.objects.create(
                subsistema=subsistema,
                nombre=a.get("nombre", ""),
                descripcion=a.get("descripcion", ""),
                puesto=a.get("puesto", ""),
                activo=True,
            )

        for t in s.get("tendencias", []):
            tipo = t.get("tipo", "CUALITATIVA")
            if tipo not in ["CUALITATIVA", "CUANTITATIVA"]:
                tipo = "CUALITATIVA"

            tendencia = TendenciaExterna.objects.create(
                subsistema=subsistema,
                nombre=t.get("nombre", ""),
                nombre_corto=t.get("nombre", "")[:40],
                tipo_dato=tipo,
                descripcion=t.get("descripcion", ""),
                activo=True,
            )

            Historial.objects.create(tendencia=tendencia, accion="CREADO", usuario=None)


def generar_evaluaciones_e_influencias(tema, usuario):
    variables = list(
        Variable.objects.filter(subsistema__sistema__tema=tema).order_by("pk")
    )
    if not variables:
        return

    lista_vars_texto = "\n".join([f"- {v.nombre}" for v in variables])
    amount = len(variables)

    prompt = f"""
    Sos un experto en prospectiva estratégica y análisis MIC-MAC.
    Acabo de identificar exactamente {amount} variables clave para el proyecto: "{tema.nombre}".
    
    Las variables, en su orden exacto, son:
    {lista_vars_texto}

    Necesito que actúes como un panel de expertos y evalúes matemáticamente estas {amount} variables.
    
    REGLAS ESTRICTAS:
    1. "evaluaciones": DEBE ser una lista con exactamente {amount} objetos con "importancia" e "incertidumbre" (1 al 10).
    2. "matriz_influencia": DEBE ser una matriz cuadrada exacta de {amount} x {amount} (es decir, {amount} listas, cada una con {amount} valores).
    3. VALORES DE INFLUENCIA: Los únicos números permitidos son 0, 1, 2 o 3. 
       🚨 REGLA DE CONEXIÓN: En un sistema real, casi todas las variables interactúan. EVITÁ RELLENAR CON CEROS (0). Pensá críticamente y usá 1, 2 o 3 para reflejar influencias directas cruzadas. 🚨
    4. La diagonal siempre debe ser 0.

    Respondé ÚNICAMENTE con un JSON válido.
    """

    logger.info(f"Enviando solicitud matemática a la IA para {amount} variables...")
    # Subimos un poco la temperatura para que la IA sea más analítica cruzando datos y no tan repetitiva
    resultado = generar_respuesta_llm(prompt, temperature=0.3, max_tokens=4000)

    if not resultado.get("success"):
        logger.error(
            f"ERROR: La IA falló al generar la matriz: {resultado.get('error')}"
        )
        return

    content = resultado.get("text").strip()
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)
    else:
        return

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return

    evaluaciones = data.get("evaluaciones", [])
    matriz = data.get("matriz_influencia", [])

    for i, var in enumerate(variables):
        imp, inc = 5, 5
        if i < len(evaluaciones):
            try:
                imp = max(1, min(10, int(evaluaciones[i].get("importancia", 5))))
                inc = max(1, min(10, int(evaluaciones[i].get("incertidumbre", 5))))
            except (ValueError, TypeError):
                pass

        EvaluacionVariable.objects.create(
            variable=var, usuario=usuario, importancia=imp, incertidumbre=inc
        )

        Historial.objects.create(variable=var, usuario=usuario, accion="EVALUACION")

    for i, var_origen in enumerate(variables):
        for j, var_destino in enumerate(variables):
            if i != j:
                valor_ia = 0
                if i < len(matriz) and j < len(matriz[i]):
                    try:
                        val = int(matriz[i][j])
                        valor_ia = max(0, min(3, val))
                    except (ValueError, TypeError):
                        valor_ia = 0

                Influencia.objects.create(
                    variable_origen=var_origen,
                    variable_destino=var_destino,
                    valor=valor_ia,
                )
