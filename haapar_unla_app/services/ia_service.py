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


def generar_evaluaciones_e_influencias(tema, usuario=None):

    variables = list(
        Variable.objects.filter(subsistema__sistema__tema=tema).order_by("pk")
    )

    if not variables:
        logger.warning(
            f"No hay variables para generar evaluaciones en el tema {tema.id_tema}"
        )
        return

    amount = len(variables)

    # ============================================================
    # 1. GENERAR IMPORTANCIA E INCERTIDUMBRE
    # ============================================================

    lista_vars_texto = "\n".join(
        [f"{i + 1}. {v.nombre}" for i, v in enumerate(variables)]
    )

    prompt_evaluaciones = f"""
Sos un experto en prospectiva estratégica.

Evaluá las siguientes {amount} variables del proyecto "{tema.nombre}".

VARIABLES:

{lista_vars_texto}

Para cada variable asigná:

- importancia: número entero entre 1 y 10
- incertidumbre: número entero entre 1 y 10

IMPORTANTE:

La respuesta debe contener exactamente {amount} evaluaciones,
una por cada variable y respetando exactamente el orden indicado.

Respondé ÚNICAMENTE con JSON válido.

Formato obligatorio:

{{
    "evaluaciones": [
        {{
            "importancia": 8,
            "incertidumbre": 6
        }}
    ]
}}
"""

    logger.info(
        f"Generando evaluaciones de importancia/incertidumbre "
        f"para {amount} variables..."
    )

    resultado_eval = generar_respuesta_llm(
        prompt_evaluaciones,
        temperature=0.2,
        max_tokens=2000,
    )

    if not resultado_eval.get("success"):
        logger.error(f"ERROR generando evaluaciones: " f"{resultado_eval.get('error')}")
        return

    contenido_eval = resultado_eval.get("text", "").strip()

    logger.info(f"RESPUESTA EVALUACIONES IA:\n{contenido_eval}")

    match = re.search(r"\{.*\}", contenido_eval, re.DOTALL)

    if not match:
        logger.error("La IA no devolvió JSON válido para las evaluaciones.")
        return

    try:
        data_eval = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error(f"Error interpretando JSON de evaluaciones: {e}")
        return

    evaluaciones = data_eval.get("evaluaciones", [])

    if len(evaluaciones) != amount:
        logger.error(
            f"La IA devolvió {len(evaluaciones)} evaluaciones "
            f"pero se esperaban {amount}."
        )
        return

    # ============================================================
    # 2. GUARDAR IMPORTANCIA / INCERTIDUMBRE
    # ============================================================

    for i, var in enumerate(variables):

        try:
            imp = int(evaluaciones[i].get("importancia", 5))

            inc = int(evaluaciones[i].get("incertidumbre", 5))

            imp = max(1, min(10, imp))
            inc = max(1, min(10, inc))

        except (ValueError, TypeError, AttributeError):

            imp = 5
            inc = 5

        EvaluacionVariable.objects.update_or_create(
            variable=var,
            usuario=None,
            defaults={
                "importancia": imp,
                "incertidumbre": inc,
            },
        )

    # ============================================================
    # 3. GENERAR MATRIZ MIC-MAC
    # ============================================================

    prompt_matriz = f"""
Sos un experto en análisis MIC-MAC.

Necesito construir una matriz de influencia directa entre
las siguientes {amount} variables:

{lista_vars_texto}

Generá una matriz cuadrada de {amount} x {amount}.

REGLAS:

- Cada fila representa la variable de origen.
- Cada columna representa la variable de destino.
- Los valores permitidos son únicamente:
  0, 1, 2 o 3.
- La diagonal debe ser siempre 0.
- 0 = sin influencia directa.
- 1 = influencia débil.
- 2 = influencia media.
- 3 = influencia fuerte.
- Usá 0 cuando no exista una influencia directa entre las variables.
- No llenes artificialmente la matriz con valores distintos de 0.
- Cada valor debe representar una relación de influencia directa
  plausible entre la variable de origen y la variable de destino.

La matriz debe tener exactamente {amount} filas
y cada fila debe tener exactamente {amount} valores.

Respondé ÚNICAMENTE con JSON válido.

Formato obligatorio:

{{
    "matriz_influencia": [
        [0,1,2],
        [1,0,3],
        [2,1,0]
    ]
}}
"""

    logger.info(f"Generando matriz MIC-MAC de {amount}x{amount}...")

    resultado_matriz = generar_respuesta_llm(
        prompt_matriz,
        temperature=0.2,
        max_tokens=5000,
    )

    if not resultado_matriz.get("success"):
        logger.error(f"ERROR generando matriz: " f"{resultado_matriz.get('error')}")
        return

    contenido_matriz = resultado_matriz.get("text", "").strip()

    logger.info(f"RESPUESTA MATRIZ IA:\n{contenido_matriz}")

    match = re.search(r"\{.*\}", contenido_matriz, re.DOTALL)

    if not match:
        logger.error("La IA no devolvió JSON válido para la matriz.")
        return

    try:
        data_matriz = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error(f"Error interpretando JSON de matriz: {e}")
        return

    matriz = data_matriz.get("matriz_influencia", [])

    # ============================================================
    # 4. VALIDAR MATRIZ
    # ============================================================

    if len(matriz) != amount:

        logger.error(
            f"La matriz tiene {len(matriz)} filas " f"pero se esperaban {amount}."
        )

        return

    for fila in matriz:

        if not isinstance(fila, list) or len(fila) != amount:

            logger.error("La IA devolvió una matriz con dimensiones incorrectas.")

            return

    # ============================================================
    # 5. GUARDAR MATRIZ
    # ============================================================

    for i, var_origen in enumerate(variables):

        for j, var_destino in enumerate(variables):

            # La diagonal siempre debe ser 0.
            # No se guarda una influencia de una variable
            # sobre sí misma.
            if i == j:
                continue

            try:

                valor_ia = int(matriz[i][j])

                valor_ia = max(0, min(3, valor_ia))

            except (ValueError, TypeError):

                valor_ia = 0

            Influencia.objects.update_or_create(
                variable_origen=var_origen,
                variable_destino=var_destino,
                defaults={"valor": valor_ia},
            )

    logger.info(
        f"Evaluaciones y matriz MIC-MAC generadas correctamente "
        f"para el tema {tema.id_tema}."
    )
