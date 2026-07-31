import json
import logging
import re

from ..models import (
    PESTEL,
    ActorClave,
    EvaluacionVariable,
    Historial,
    IndicadorVariable,
    Influencia,
    Sistema,
    Subsistema,
    TendenciaExterna,
    Variable,
    VariableTendencia,
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

    - Cuantitativas: expresadas con métricas (%, tasas, índices, cantidades)
    - Cualitativas: cambios o fenómenos no medibles directamente

    Debe haber una mezcla de ambas.

    Ejemplos:

    Cuantitativas:
    - "Crecimiento del PBI (%)"
    - "Tasa de adopción tecnológica (%)"

    Cualitativas:
    - "Cambio en hábitos de consumo digital"
    - "Mayor conciencia ambiental en la población"
    
    IMPORTANTE:
    Las variables deben ser CUANTIFICABLES, es decir, deben poder medirse numéricamente.


    El nombre de cada variable debe incluir una métrica clara o unidad, como:
    - Porcentaje (%)
    - Tasa
    - Cantidad
    - Índice
    - Nivel

    Ejemplos:
    - "Tasa de desempleo (%)"
    - "Nivel de digitalización (%)"
    - "Cantidad de empresas activas"
    - "Índice de inflación anual"

    NO usar nombres abstractos como:
    - "Economía"
    - "Tecnología"
    - "Educación"

    Cada variable debe tener un nombre claro, específico y medible.
    
    Las variables deben clasificarse como:

    I = Interna (factor dentro del sistema)
    E = Externa (factor del entorno)

    Elegí correctamente si cada variable es I o E.
    
    - Asignar entre 1 y 3 categorías PESTEL (usar códigos: P, EC, S, T, EO, L)
    - Generar entre 1 y 2 indicadores medibles
    - Relacionar con tendencias del mismo subsistema
    - El impacto debe ser un número entre 0.0 y 1.0

    IMPORTANTE:
    Las tendencias_relacionadas deben referenciar tendencias que existan en el mismo subsistema.

    Respondé SOLO en JSON válido.
    🚨 REGLA DE OPTIMIZACIÓN: Devolvé el JSON MINIFICADO (en una sola línea, sin saltos de línea ni espacios en blanco para la indentación) para evitar que se corte por límite de tokens. 🚨
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
                "pestel": ["P", "EC", "S", "T", "EO", "L"],

                "indicadores":[
                    {{
                    "nombre_corto":"",
                    "descripcion":"",
                    "formula":""
                    }}
                ],

                "tendencias_relacionadas":[
                    {{
                    "nombre":"",
                    "impacto": 0.0
                    }}
                ]
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

    # Optimizamos los tokens forzando el límite máximo
    resultado = generar_respuesta_llm(prompt, temperature=0.7, max_tokens=8192)

    if not resultado.get("success"):
        return

    content = resultado.get("text", "")
    content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}") + 1
    content = content[start:end]

    data = json.loads(content)

    sistema = Sistema.objects.create(
        tema=tema, nombre=f"Sistema de {tema.nombre}", descripcion=tema.descripcion
    )

    # 🔴 LOOP PRINCIPAL
    for s in data.get("subsistemas", []):

        subsistema = Subsistema.objects.create(
            sistema=sistema,
            nombre=s.get("nombre", ""),
            descripcion=s.get("descripcion", ""),
            activo=True,
        )

        # 🔵 1. ACTORES (UNA SOLA VEZ)
        for a in s.get("actores", []):
            ActorClave.objects.create(
                subsistema=subsistema,
                nombre=a.get("nombre", ""),
                descripcion=a.get("descripcion", ""),
                puesto=a.get("puesto", ""),
                activo=True,
            )

        # 🟡 2. TENDENCIAS (UNA SOLA VEZ + MAPEO)
        tendencias_creadas = {}

        for t in s.get("tendencias", []):
            tendencia = TendenciaExterna.objects.create(
                subsistema=subsistema,
                nombre=t.get("nombre", ""),
                nombre_corto=t.get("nombre", "")[:40],
                tipo_dato=t.get("tipo", "CUALITATIVA"),
                descripcion=t.get("descripcion", ""),
                activo=True,
            )

            tendencias_creadas[t.get("nombre")] = tendencia

            Historial.objects.create(tendencia=tendencia, accion="CREADO", usuario=None)

        # 🟣 3. VARIABLES (TODO DENTRO DEL LOOP)
        for v in s.get("variables", []):

            variable = Variable.objects.create(
                subsistema=subsistema,
                nombre=v.get("nombre", ""),
                nombre_corto=v.get("nombre", "")[:40],
                descripcion=v.get("descripcion", ""),
                tipo=v.get("tipo", "I"),
                activo=True,
            )

            # 🟠 PESTEL
            MAP_PESTEL = {
                "P": "P",
                "EC": "EC",
                "S": "S",
                "T": "T",
                "EO": "EO",
                "L": "L",
            }

            for p in v.get("pestel", []):
                key = MAP_PESTEL.get(str(p).upper())
                if key:
                    # get_or_create crea la categoría automáticamente si la base está vacía
                    pestel_obj, created = PESTEL.objects.get_or_create(tipo=key)
                    variable.pestels.add(pestel_obj)

            # 🔵 INDICADORES (OBLIGATORIO)
            indicadores = v.get("indicadores", [])
            if not indicadores:
                IndicadorVariable.objects.create(
                    variable=variable,
                    nombre_corto="default",
                    descripcion="Auto generado",
                    formula="1",
                )
            else:
                for ind in indicadores:
                    nombre_c = ind.get("nombre_corto", "")

                    # 🛡️ PARCHE: Recortamos a un máximo de 50 caracteres para no romper la BD
                    if nombre_c:
                        nombre_c = nombre_c[:50]

                    IndicadorVariable.objects.create(
                        variable=variable,
                        nombre_corto=nombre_c,
                        descripcion=ind.get("descripcion", ""),
                        formula=ind.get("formula", ""),
                    )

            # 🟠 TENDENCIAS RELACIONADAS
            relaciones = v.get("tendencias_relacionadas", [])
            if not relaciones:
                continue

            for tr in relaciones:
                nombre = tr.get("nombre")
                if nombre in tendencias_creadas:
                    VariableTendencia.objects.create(
                        variable=variable,
                        tendencia=tendencias_creadas[nombre],
                        impacto=tr.get("impacto", 0),
                    )

            Historial.objects.create(variable=variable, accion="CREADO", usuario=None)


def calcular_impacto_variable_tendencia(variable, tendencia):

    prompt = f"""
    Sos un experto en prospectiva estratégica.

    Variable:
    {variable.nombre}

    Descripción de la variable:
    {variable.descripcion}

    Tendencia:
    {tendencia.nombre}

    Descripción de la tendencia:
    {tendencia.descripcion}

    Evaluá cuánto impacta esta tendencia sobre esta variable.

    Respondé únicamente un número decimal entre 0 y 1.
    """

    resultado = generar_respuesta_llm(prompt, temperature=0.2)

    try:
        valor = float(resultado["text"].strip())

        if valor < 0:
            valor = 0

        if valor > 1:
            valor = 1

        return valor

    except Exception:
        return 0.5


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
    🚨 REGLA DE OPTIMIZACIÓN: Devolvé el JSON MINIFICADO (en una sola línea, sin saltos de línea ni espacios en blanco para la indentación) para evitar que se corte por límite de tokens. 🚨
    """

    logger.info(f"Enviando solicitud matemática a la IA para {amount} variables...")
    # Ampliamos el max_tokens a 8192 para soportar la matriz completa
    resultado = generar_respuesta_llm(prompt, temperature=0.3, max_tokens=8192)

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
        # Si no encuentra un JSON, forzamos un diccionario vacío
        content = "{}"

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Si el JSON viene roto, no cancelamos. Usamos un diccionario vacío
        # para que se apliquen los valores neutrales (5 y 5).
        data = {}

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
