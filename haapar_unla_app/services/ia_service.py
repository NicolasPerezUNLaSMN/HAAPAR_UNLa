import json
import logging
import re

from ..models import (
    PESTEL,
    ActorClave,
    EvaluacionTendencia,
    EvaluacionVariable,
    Historial,
    IndicadorTendencia,
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
    FUNCIÓN NÚCLEO:
    Toma UN subsistema y le pide a la IA que lo complete con
    variables, actores y tendencias.

    La IA también determina el impacto de cada tendencia sobre
    las variables relacionadas, con un valor entre 0 y 1.
    """

    tema = subsistema.sistema.tema

    prompt = f"""
Sos un experto en prospectiva estratégica y análisis de sistemas.

Estamos trabajando en el proyecto:
"{tema.nombre}"

Tu tarea es completar EXCLUSIVAMENTE el siguiente subsistema:

Subsistema: "{subsistema.nombre}"
Descripción: "{subsistema.descripcion}"

Generá información específica, coherente y relevante para este subsistema.

DEBÉS GENERAR:

- 4 variables estratégicas.
- 3 actores clave.
- 3 tendencias externas.
- Indicadores para las variables.
- Indicadores para las tendencias.
- Evaluación de importancia e incertidumbre para CADA variable.
- Evaluación de importancia e incertidumbre para CADA tendencia.
- Relaciones entre las variables y las tendencias cuando exista una relación relevante.
- Para cada relación variable-tendencia, calcular el IMPACTO de la tendencia sobre la variable.
============================================================
VARIABLES
============================================================

Generá exactamente 4 variables.

Las variables deben ser:

- Relevantes para el subsistema.
- Concretas y medibles.
- CUANTIFICABLES mediante un indicador.
- Evitá variables excesivamente generales o abstractas.
- Cada variable debe tener una descripción analítica y específica.

Para cada variable indicá:

- nombre
- descripción
- tipo: "I" (Interna) o "E" (Externa)
- entre 1 y 2 categorías PESTEL
- al menos un indicador que permita medir la evolución de la variable.

El indicador debe incluir:

- nombre_corto
- descripción
- fórmula o forma concreta de medición.

- Importancia: entero entre 1 y 10.
- Incertidumbre: entero entre 1 y 10.

============================================================
TENDENCIAS
============================================================

Generá exactamente 3 tendencias relacionadas con el subsistema.

Las tendencias deben representar fenómenos, cambios, patrones o evoluciones
reales que puedan afectar al sistema en el horizonte temporal del proyecto.

Podés combinar:

- tendencias cualitativas
- tendencias cuantitativas

Para cada tendencia indicá:

- nombre
- descripción
- tipo: "CUALITATIVA" o "CUANTITATIVA"

Las descripciones deben ser específicas, analíticas y realistas.

NO utilices frases genéricas como:
"aumento de la tecnología"
"cambios económicos"
"crecimiento de la población"

sin explicar concretamente qué está ocurriendo.

- Tener una evaluación inicial de:
  - importancia: entero entre 1 y 10
  - incertidumbre: entero entre 1 y 10

============================================================
RELACIÓN TENDENCIA → VARIABLE
============================================================

Para cada variable, analizá si alguna de las 3 tendencias generadas
tiene un impacto DIRECTO y significativo sobre ella.

Cuando exista una relación relevante, agregala en
"tendencias_relacionadas".

Para cada relación calculá VOS MISMO el nivel de impacto.

El impacto debe ser un número DECIMAL entre 0 y 1:

- 0.00 = sin impacto
- 0.10–0.30 = impacto muy bajo
- 0.31–0.50 = impacto bajo/medio
- 0.51–0.70 = impacto medio/alto
- 0.71–0.90 = impacto alto
- 0.91–1.00 = impacto muy alto

IMPORTANTE:

- NO uses automáticamente 0.5.
- NO asignes el mismo impacto a todas las relaciones.
- El impacto debe surgir del análisis de la relación concreta
  entre la tendencia y la variable.
- Si una tendencia NO tiene una relación directa y significativa
  con una variable, NO la incluyas.
- El impacto debe representar cuánto puede afectar la evolución
  de esa tendencia a la evolución de esa variable.
- El valor debe ser diferente cuando la intensidad de las relaciones
  sea diferente.

============================================================
ACTORES
============================================================

Generá exactamente 3 actores clave que tengan capacidad real de
influir, intervenir, regular, ejecutar o verse afectados por el subsistema.

Para cada actor indicá:

- nombre
- descripción
- puesto, función o rol dentro del sistema.

============================================================
PESTEL
============================================================

Cada variable debe tener entre 1 y 2 códigos PESTEL.

Los únicos códigos permitidos son:

"P" = Político
"EC" = Económico
"S" = Social
"T" = Tecnológico
"EO" = Ecológico/Ambiental
"L" = Legal

============================================================
FORMATO DE RESPUESTA
============================================================

Respondé ÚNICAMENTE con JSON válido.

No agregues explicaciones, comentarios, texto antes ni después del JSON.

La estructura debe ser EXACTAMENTE:

{{
    "variables": [
        {{
            "nombre": "",
            "descripcion": "",
            "tipo": "I",
            "pestel": ["T"],
            "indicadores": [
                {{
                    "nombre_corto": "",
                    "descripcion": "",
                    "formula": ""
                }}
            ],
            "importancia": 8,
            "incertidumbre": 6,
            "tendencias_relacionadas": [
                {{
                    "nombre": "",
                    "impacto": 0.73
                }}
            ]
        }}
    ],
    "actores": [
        {{
            "nombre": "",
            "descripcion": "",
            "puesto": ""
        }}
    ],
    "tendencias": [
        {{
            "nombre": "",
            "descripcion": "",
            "tipo": "CUANTITATIVA"
            "indicadores": [
                                {{
                    "nombre_corto": "",
                    "descripcion": "",
                    "formula": ""
                }}
                ],
            "importancia": 8,
            "incertidumbre": 6
        }}
    ]
}}

RECORDATORIO FINAL:

- Exactamente 4 variables.
- Exactamente 3 actores.
- Exactamente 3 tendencias.
- Variables cuantificables.
- Descripciones específicas y profesionales.
- Cada variable debe tener 1 o 2 códigos PESTEL.
- Cada variable debe tener al menos un indicador.
- Las relaciones tendencia-variable deben ser analizadas por vos.
- El campo "impacto" debe ser calculado por vos.
- El "impacto" debe estar entre 0 y 1.
- NO uses 0.5 como valor por defecto.
- NO inventes relaciones que no sean relevantes.
- JSON válido exclusivamente.
"""

    logger.info(f"Rellenando con IA el subsistema: {subsistema.nombre}")

    resultado = generar_respuesta_llm(
        prompt,
        temperature=0.7,
        max_tokens=4000,
    )

    # ============================================================
    # VALIDAR RESPUESTA DE IA
    # ============================================================

    if not resultado or not resultado.get("success"):
        logger.error(
            f"Error generando datos del subsistema: "
            f"{resultado.get('error') if resultado else 'sin respuesta'}"
        )
        return False

    content = resultado.get("text") or ""

    content = content.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if match:
        content = match.group(0)

    try:
        data = json.loads(content)
    except Exception as e:
        logger.error(f"Error interpretando JSON del subsistema: {e}")
        return False

    # ============================================================
    # 1. CREAR ACTORES
    # ============================================================

    for a in data.get("actores", []):

        ActorClave.objects.create(
            subsistema=subsistema,
            nombre=a.get("nombre", "")[:100],
            descripcion=a.get("descripcion", ""),
            puesto=a.get("puesto", "")[:100],
            activo=True,
        )

    # ============================================================
    # 2. CREAR TENDENCIAS
    # ============================================================

    tendencias_creadas = {}

    for t in data.get("tendencias", []):

        tipo_tendencia = str(t.get("tipo", "CUALITATIVA")).upper()

        if "CUAN" in tipo_tendencia:
            tipo_tendencia = "CUANTITATIVA"
        else:
            tipo_tendencia = "CUALITATIVA"

        nombre_tendencia = t.get("nombre", "").strip()

        tendencia = TendenciaExterna.objects.create(
            subsistema=subsistema,
            nombre=nombre_tendencia[:150],
            nombre_corto=nombre_tendencia[:40],
            tipo_dato=tipo_tendencia,
            descripcion=t.get("descripcion", ""),
            activo=True,
        )
        # INDICADORES DE LA TENDENCIA
        for ind in t.get("indicadores", []):
            IndicadorTendencia.objects.create(
                tendencia_externa=tendencia,
                nombre_corto=ind.get("nombre_corto", "")[:50],
                descripcion=ind.get("descripcion", ""),
                formula=ind.get("formula", ""),
            )

        # EVALUACIÓN INICIAL DE LA IA
        try:
            importancia = int(t.get("importancia", 5))
            incertidumbre = int(t.get("incertidumbre", 5))

            importancia = max(1, min(10, importancia))
            incertidumbre = max(1, min(10, incertidumbre))

        except (ValueError, TypeError):
            importancia = 5
            incertidumbre = 5

        EvaluacionTendencia.objects.update_or_create(
            tendencia=tendencia,
            usuario=None,
            defaults={
                "importancia": importancia,
                "incertidumbre": incertidumbre,
            },
        )

        tendencias_creadas[nombre_tendencia] = tendencia

        Historial.objects.create(
            tendencia=tendencia,
            accion="CREADO",
            usuario=None,
        )

    # ============================================================
    # 3. MAPEO PESTEL
    # ============================================================

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

    # ============================================================
    # 4. CREAR VARIABLES
    # ============================================================

    for v in data.get("variables", []):

        tipo_ia = str(v.get("tipo", "I")).upper().strip()

        tipo_final = "E" if tipo_ia.startswith("E") else "I"

        nombre_variable = v.get("nombre", "").strip()

        variable = Variable.objects.create(
            subsistema=subsistema,
            nombre=nombre_variable[:150],
            nombre_corto=nombre_variable[:40],
            descripcion=v.get("descripcion", ""),
            tipo=tipo_final,
            activo=True,
        )
        # ========================================================
        # EVALUACIÓN INICIAL DE LA IA
        # ========================================================

        try:
            importancia = int(v.get("importancia", 5))
            incertidumbre = int(v.get("incertidumbre", 5))

            importancia = max(1, min(10, importancia))
            incertidumbre = max(1, min(10, incertidumbre))

        except (ValueError, TypeError):
            importancia = 5
            incertidumbre = 5

        EvaluacionVariable.objects.update_or_create(
            variable=variable,
            usuario=None,
            defaults={
                "importancia": importancia,
                "incertidumbre": incertidumbre,
            },
        )

        # ========================================================
        # PESTEL
        # ========================================================

        pesteles = v.get("pestel", [])

        if isinstance(pesteles, str):
            pesteles = [pesteles]

        for p in pesteles:

            key = MAP_PESTEL.get(str(p).strip().upper())

            if key:

                pestel_obj, _ = PESTEL.objects.get_or_create(tipo=key)

                variable.pestels.add(pestel_obj)

        # ========================================================
        # INDICADORES
        # ========================================================

        indicadores = v.get("indicadores", [])

        if not indicadores:

            IndicadorVariable.objects.create(
                variable=variable,
                nombre_corto="default",
                descripcion="Indicador generado automáticamente.",
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

        # ========================================================
        # RELACIÓN TENDENCIA → VARIABLE
        # ========================================================

        for tr in v.get("tendencias_relacionadas", []):

            nombre_t = str(tr.get("nombre", "")).strip()

            if nombre_t not in tendencias_creadas:
                logger.warning(
                    f"La tendencia '{nombre_t}' indicada por la IA "
                    f"no fue encontrada entre las tendencias creadas."
                )
                continue

            # --------------------------------------------
            # VALIDAR IMPACTO GENERADO POR LA IA
            # --------------------------------------------

            try:

                impacto = float(tr.get("impacto", 0))

                impacto = max(0.0, min(1.0, impacto))

            except (ValueError, TypeError):

                logger.warning(
                    f"Impacto inválido para la relación "
                    f"'{nombre_t}' → '{nombre_variable}'. "
                    f"Se utilizará 0."
                )

                impacto = 0.0

            # --------------------------------------------
            # CREAR RELACIÓN
            # --------------------------------------------

            VariableTendencia.objects.create(
                variable=variable,
                tendencia=tendencias_creadas[nombre_t],
                impacto=impacto,
            )

            logger.info(
                f"Relación creada: "
                f"Tendencia='{nombre_t}' → "
                f"Variable='{nombre_variable}' | "
                f"Impacto={impacto}"
            )

        # ========================================================
        # HISTORIAL
        # ========================================================

        Historial.objects.create(
            variable=variable,
            accion="CREADO",
            usuario=None,
        )

    return True


def generar_estructura_prospectiva(tema):
    """
    Paso 1:
    La IA genera los 4 subsistemas.

    Paso 2:
    Cada subsistema es completado individualmente con variables,
    actores, tendencias e impactos tendencia-variable.
    """

    prompt = f"""
Sos un experto en prospectiva estratégica.

Tema: {tema.nombre}
Descripción: {tema.descripcion}
Horizonte: {tema.horizonte}
Territorio: {tema.territorio}

Tu única tarea en este paso es definir la estructura inicial.

Generá EXACTAMENTE 4 subsistemas clave para analizar este proyecto.

Cada subsistema debe tener:

- un nombre claro y específico
- una descripción real, profesional y analítica

No generes variables, actores ni tendencias en este paso.

Respondé SOLO en JSON válido minificado:

{{
    "subsistemas": [
        {{
            "nombre": "",
            "descripcion": ""
        }}
    ]
}}
"""

    logger.info("Generando los 4 subsistemas principales...")

    resultado = generar_respuesta_llm(
        prompt,
        temperature=0.7,
        max_tokens=2000,
    )

    if not resultado or not resultado.get("success"):

        raise Exception(
            "Fallo en la conexión con la IA al generar " "la estructura inicial."
        )

    content = resultado.get("text") or ""

    content = content.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if match:
        content = match.group(0)

    try:

        data = json.loads(content)

    except Exception:

        raise Exception(
            "La IA devolvió un formato inválido " "al crear los subsistemas."
        )

    sistema = Sistema.objects.create(
        tema=tema,
        nombre=f"Sistema de {tema.nombre}",
        descripcion=tema.descripcion,
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
    """
    Aplica cuando el usuario agrega un subsistema
    manualmente desde la interfaz.
    """

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

Evaluá cuánto impacta DIRECTAMENTE esta tendencia
sobre esta variable.

El impacto debe ser un número decimal entre 0 y 1.

0.00 = sin impacto
0.10–0.30 = muy bajo
0.31–0.50 = bajo/medio
0.51–0.70 = medio/alto
0.71–0.90 = alto
0.91–1.00 = muy alto

Analizá concretamente la relación entre la tendencia
y la variable.

NO uses automáticamente 0.5.

Respondé únicamente con un número decimal entre 0 y 1.
"""

    resultado = generar_respuesta_llm(prompt, temperature=0.2)

    try:

        valor = float(resultado.get("text", "0").strip())

        if valor < 0:
            return 0.0

        if valor > 1:
            return 1.0

        return valor

    except Exception:

        return 0.0


def generar_evaluaciones_e_influencias(tema, usuario=None):

    variables = list(
        Variable.objects.filter(subsistema__sistema__tema=tema).order_by("pk")
    )

    if not variables:

        logger.warning(
            f"No hay variables para generar evaluaciones " f"en el tema {tema.id_tema}"
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

Evaluá las siguientes {amount} variables
del proyecto "{tema.nombre}".

VARIABLES:

{lista_vars_texto}

Para cada variable asigná:

- importancia: número entero entre 1 y 10
- incertidumbre: número entero entre 1 y 10

IMPORTANTE:

La respuesta debe contener exactamente {amount}
evaluaciones, una por cada variable y respetando
exactamente el orden indicado.

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

    logger.info(f"RESPUESTA EVALUACIONES IA:\n" f"{contenido_eval}")

    match = re.search(r"\{.*\}", contenido_eval, re.DOTALL)

    if not match:

        logger.error("La IA no devolvió JSON válido " "para las evaluaciones.")

        return

    try:

        data_eval = json.loads(match.group(0))

    except json.JSONDecodeError as e:

        logger.error(f"Error interpretando JSON de evaluaciones: {e}")

        return

    evaluaciones = data_eval.get("evaluaciones", [])

    if len(evaluaciones) != amount:

        logger.error(
            f"La IA devolvió {len(evaluaciones)} "
            f"evaluaciones pero se esperaban {amount}."
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

Necesito construir una matriz de influencia directa
entre las siguientes {amount} variables:

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
- Usá 0 cuando no exista una influencia directa.
- No llenes artificialmente la matriz.
- Cada valor debe representar una relación de influencia
  directa plausible.

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

    logger.info(f"Generando matriz MIC-MAC de " f"{amount}x{amount}...")

    resultado_matriz = generar_respuesta_llm(
        prompt_matriz,
        temperature=0.2,
        max_tokens=5000,
    )

    if not resultado_matriz.get("success"):

        logger.error(f"ERROR generando matriz: " f"{resultado_matriz.get('error')}")

        return

    contenido_matriz = resultado_matriz.get("text", "").strip()

    logger.info(f"RESPUESTA MATRIZ IA:\n" f"{contenido_matriz}")

    match = re.search(r"\{.*\}", contenido_matriz, re.DOTALL)

    if not match:

        logger.error("La IA no devolvió JSON válido " "para la matriz.")

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

            logger.error("La IA devolvió una matriz " "con dimensiones incorrectas.")

            return

    # ============================================================
    # 5. GUARDAR MATRIZ
    # ============================================================

    for i, var_origen in enumerate(variables):

        for j, var_destino in enumerate(variables):

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
        f"Evaluaciones y matriz MIC-MAC "
        f"generadas correctamente para "
        f"el tema {tema.id_tema}."
    )
