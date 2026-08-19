import json
import logging
import random
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


def generar_evaluaciones_e_influencias(tema, usuario):
    variables = list(
        Variable.objects.filter(subsistema__sistema__tema=tema).order_by("pk")
    )
    if not variables:
        return

    lista_vars = "\n".join([f"{i+1}. {v.nombre}" for i, v in enumerate(variables)])
    cantidad = len(variables)

    prompt = f"""
    Sos un experto en prospectiva. Evalúa matemáticamente las siguientes {cantidad} variables:
    {lista_vars}

    Generá una evaluación de "importancia" (1 a 10) y de "incertidumbre" (1 a 10) PARA CADA UNA de las variables, en el mismo orden exacto.
    Variables críticas deben tener valores entre 7 y 10. No uses el número 5 para todo, DIVERSIFICA (ej. 6, 8, 9, 4, 7).

    Respondé ESTRICTAMENTE en este formato JSON minificado:
    {{"evaluaciones": [{{"importancia": 8, "incertidumbre": 7}}, {{"importancia": 6, "incertidumbre": 9}}]}}
    Asegúrate de generar EXACTAMENTE {cantidad} objetos dentro del arreglo "evaluaciones".
    """

    logger.info(
        f"Enviando solicitud matemática a la IA para evaluar {cantidad} variables..."
    )
    resultado = generar_respuesta_llm(prompt, temperature=0.5, max_tokens=2500)

    try:
        content = resultado.get("text") or "{}"
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            content = match.group(0)
        data = json.loads(content)
    except Exception as e:
        logger.warning(f"Error parseando JSON de evaluaciones: {e}")
        data = {}

    evaluaciones = data.get("evaluaciones", [])

    for i, var in enumerate(variables):

        imp = random.randint(6, 9)
        inc = random.randint(4, 8)

        if i < len(evaluaciones):
            try:
                val_imp = evaluaciones[i].get("importancia")
                val_inc = evaluaciones[i].get("incertidumbre")
                if val_imp is not None:
                    imp = max(1, min(10, int(val_imp)))
                if val_inc is not None:
                    inc = max(1, min(10, int(val_inc)))
            except (ValueError, TypeError):
                pass

        EvaluacionVariable.objects.update_or_create(
            variable=var,
            usuario=usuario,
            defaults={"importancia": imp, "incertidumbre": inc},
        )

    Influencia.objects.filter(variable_origen__subsistema__sistema__tema=tema).delete()

    for v1 in variables:
        for v2 in variables:
            if v1 != v2:
                # Variables del mismo subsistema impactan con fuerza
                if v1.subsistema == v2.subsistema:
                    valor = random.choice([2, 3])
                # Variables cruzadas impactan menos
                else:
                    valor = random.choice([0, 1])

                Influencia.objects.create(
                    variable_origen=v1, variable_destino=v2, valor=valor
                )
