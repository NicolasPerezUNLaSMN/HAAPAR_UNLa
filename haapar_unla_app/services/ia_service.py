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


def _rellenar_subsistema_con_ia(subsistema):
    """
    FUNCIÓN NÚCLEO: Toma UN subsistema y le pide a la IA que lo llene con
    variables, actores y tendencias con descripciones REALES y detalladas.
    Al procesar de a uno, evitamos por completo el límite de tokens.
    """
    tema = subsistema.sistema.tema

    prompt = f"""
    Sos un experto en prospectiva estratégica.
    Estamos trabajando en el proyecto "{tema.nombre}".
    Tu tarea es completar el subsistema: "{subsistema.nombre}" (Descripción: {subsistema.descripcion}).

    Generá EXCLUSIVAMENTE para este subsistema:
    - 4 variables (CUANTIFICABLES, con métrica clara %, Tasa, etc.)
    - 3 actores clave
    - 3 tendencias (mezcla de cualitativas y cuantitativas)

    IMPORTANTE:
    - Escribí descripciones REALES, analíticas y profundas. NADA de texto genérico.
    - Asigná cada variable a 1 o 2 códigos PESTEL ("P", "EC", "S", "T", "EO", "L").
    - Tipo: "I" (Interna) o "E" (Externa).

    Respondé SOLO en JSON válido minificado (sin saltos de línea) con esta estructura exacta:
    {{
        "variables": [ {{"nombre":"", "descripcion":"", "tipo":"", "pestel":["P"], "indicadores":[{{"nombre_corto":"", "descripcion":"", "formula":""}}], "tendencias_relacionadas":[{{"nombre":"", "impacto":0.5}}] }} ],
        "actores": [ {{"nombre":"", "descripcion":"", "puesto":""}} ],
        "tendencias": [ {{"nombre":"", "descripcion":"", "tipo":""}} ]
    }}
    """

    logger.info(f"Rellenando con IA el subsistema: {subsistema.nombre}")
    resultado = generar_respuesta_llm(prompt, temperature=0.7, max_tokens=4000)

    # Escudo de seguridad por si la API falla o devuelve None
    if not resultado or not resultado.get("success"):
        return False

    content = resultado.get("text") or ""
    content = content.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)

    try:
        data = json.loads(content)
    except Exception:
        return False

    # 1. Crear Actores
    for a in data.get("actores", []):
        ActorClave.objects.create(
            subsistema=subsistema,
            nombre=a.get("nombre", "")[:100],
            descripcion=a.get("descripcion", ""),
            puesto=a.get("puesto", "")[:100],
            activo=True,
        )

    # 2. Crear Tendencias
    tendencias_creadas = {}
    for t in data.get("tendencias", []):

        tipo_tendencia = str(t.get("tipo", "CUALITATIVA")).upper()
        if "CUAN" in tipo_tendencia:
            tipo_tendencia = "CUANTITATIVA"
        else:
            tipo_tendencia = "CUALITATIVA"

        tendencia = TendenciaExterna.objects.create(
            subsistema=subsistema,
            nombre=t.get("nombre", "")[:150],
            nombre_corto=t.get("nombre", "")[:40],
            tipo_dato=tipo_tendencia,
            descripcion=t.get("descripcion", ""),
            activo=True,
        )
        tendencias_creadas[t.get("nombre")] = tendencia
        Historial.objects.create(tendencia=tendencia, accion="CREADO", usuario=None)

    # 3. Crear Variables
    MAP_PESTEL = {
        "P": "P",
        "POLITICO": "P",
        "POLÍTICO": "P",
        "POLÍTICA": "P",
        "EC": "EC",
        "ECONOMICO": "EC",
        "ECONÓMICO": "EC",
        "ECONOMÍA": "EC",
        "S": "S",
        "SOCIAL": "S",
        "T": "T",
        "TECNOLOGICO": "T",
        "TECNOLÓGICO": "T",
        "TECNOLOGÍA": "T",
        "EO": "EO",
        "ECOLOGICO": "EO",
        "ECOLÓGICO": "EO",
        "ECOLOGÍA": "EO",
        "AMBIENTAL": "EO",
        "L": "L",
        "LEGAL": "L",
        "LEGISLATIVO": "L",
    }

    for v in data.get("variables", []):

        tipo_ia = str(v.get("tipo", "I")).upper().strip()
        tipo_final = "E" if tipo_ia.startswith("E") else "I"

        variable = Variable.objects.create(
            subsistema=subsistema,
            nombre=v.get("nombre", "")[:150],
            nombre_corto=v.get("nombre", "")[:40],
            descripcion=v.get("descripcion", ""),
            tipo=tipo_final,
            activo=True,
        )

        pesteles = v.get("pestel", [])
        if isinstance(pesteles, str):
            pesteles = [pesteles]

        for p in pesteles:
            key = MAP_PESTEL.get(str(p).strip().upper())
            if key:
                pestel_obj, _ = PESTEL.objects.get_or_create(tipo=key)
                variable.pestels.add(pestel_obj)

        indicadores = v.get("indicadores", [])
        if not indicadores:
            IndicadorVariable.objects.create(
                variable=variable,
                nombre_corto="default",
                descripcion="Auto",
                formula="1",
            )
        else:
            for ind in indicadores:
                IndicadorVariable.objects.create(
                    variable=variable,
                    nombre_corto=ind.get("nombre_corto", "")[:50],
                    descripcion=ind.get("descripcion", ""),
                    formula=ind.get("formula", "")[:100],
                )

        for tr in v.get("tendencias_relacionadas", []):
            nombre_t = tr.get("nombre")
            if nombre_t in tendencias_creadas:
                VariableTendencia.objects.create(
                    variable=variable,
                    tendencia=tendencias_creadas[nombre_t],
                    impacto=tr.get("impacto", 0),
                )

        Historial.objects.create(variable=variable, accion="CREADO", usuario=None)

    return True


def generar_estructura_prospectiva(tema):
    """
    Paso 1: Solo le pedimos a la IA que imagine los 4 subsistemas (contenedores).
    Paso 2: Iteramos sobre cada uno usando la función núcleo para rellenarlos con detalle.
    """
    prompt = f"""
    Sos un experto en prospectiva estratégica.
    Tema: {tema.nombre}
    Descripción: {tema.descripcion}
    Horizonte: {tema.horizonte}
    Territorio: {tema.territorio}

    Tu única tarea en este paso es definir la estructura inicial.
    Generá EXACTAMENTE 4 subsistemas clave para analizar este proyecto.
    Redactá descripciones reales y profesionales para cada uno.

    Respondé SOLO en JSON válido minificado:
    {{
        "subsistemas":[
            {{"nombre":"", "descripcion":""}}
        ]
    }}
    """

    logger.info("Generando los 4 subsistemas principales...")
    resultado = generar_respuesta_llm(prompt, temperature=0.7, max_tokens=2000)

    # Escudo protector inicial
    if not resultado or not resultado.get("success"):
        raise Exception(
            "Fallo en la conexión con la IA al generar la estructura inicial."
        )

    content = resultado.get("text") or ""
    content = content.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)

    try:
        data = json.loads(content)
    except Exception:
        raise Exception("La IA devolvió un formato inválido al crear los subsistemas.")

    sistema = Sistema.objects.create(
        tema=tema, nombre=f"Sistema de {tema.nombre}", descripcion=tema.descripcion
    )

    subsistemas_creados = []
    for s in data.get("subsistemas", []):
        subsistema = Subsistema.objects.create(
            sistema=sistema,
            nombre=s.get("nombre", "")[:150],
            descripcion=s.get("descripcion", ""),
            activo=True,
        )
        subsistemas_creados.append(subsistema)

    for sub in subsistemas_creados:
        _rellenar_subsistema_con_ia(sub)


def generar_datos_nuevo_subsistema(subsistema, usuario):
    """Aplica cuando el usuario agrega un subsistema a mano desde la interfaz."""
    exito = _rellenar_subsistema_con_ia(subsistema)
    if exito:
        generar_evaluaciones_e_influencias(subsistema.sistema.tema, usuario)
        return True
    return False


def calcular_impacto_variable_tendencia(variable, tendencia):
    prompt = f"""
    Sos un experto en prospectiva estratégica.
    Variable: {variable.nombre}
    Descripción de la variable: {variable.descripcion}
    Tendencia: {tendencia.nombre}
    Descripción de la tendencia: {tendencia.descripcion}

    Evaluá cuánto impacta esta tendencia sobre esta variable.
    Respondé únicamente un número decimal entre 0 y 1.
    """
    resultado = generar_respuesta_llm(prompt, temperature=0.2)
    try:
        valor = float(resultado.get("text", "0.5").strip())
        if valor < 0:
            return 0
        if valor > 1:
            return 1
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
    # 2. GUARDAR IMPORTANCIA / INCERTIDUMBRE DE LA IA
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
