import json
import logging
import random
import re

from ..models import (
    PESTEL,
    ActorClave,
    EscenarioSchwartz,
    EvaluacionTendencia,
    EvaluacionVariable,
    Historial,
    IndicadorTendencia,
    IndicadorVariable,
    Influencia,
    InfluenciaActor,
    Sistema,
    Subsistema,
    TendenciaExterna,
    Variable,
    VariableTendencia,
)
from .ai_client import generar_respuesta_llm

logger = logging.getLogger(__name__)


def _extraer_json_seguro(texto):
    """Función salvavidas: extrae el JSON evitando errores NoneType si la IA responde mal."""
    if not texto:
        return None
    texto = texto.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _rellenar_subsistema_con_ia(subsistema):
    tema = subsistema.sistema.tema

    prompt = f"""
Sos un experto en prospectiva estratégica.
Proyecto: "{tema.nombre}". Subsistema: "{subsistema.nombre}" ({subsistema.descripcion})

Generá EXACTAMENTE:
- 4 variables estratégicas (Tipo "I" o "E", importancia 1-10, OBLIGATORIO asignar al menos 1 categoría PESTEL usando códigos exactos: "P", "EC", "S", "T", "EO", "L").
- 3 actores clave.
- 3 tendencias externas (con importancia/incertidumbre de 1 a 10).
- Impacto de cada tendencia sobre las variables (decimal 0.00 a 1.00).

Respondé ÚNICAMENTE con JSON válido:
{{
    "variables": [
        {{
            "nombre": "Variable 1", "descripcion": "Desc", "tipo": "I", "pestel": ["T"],
            "indicadores": [ {{"nombre_corto": "Ind1", "descripcion": "Desc", "formula": "X/Y"}} ],
            "importancia": 8, "incertidumbre": 6,
            "tendencias_relacionadas": [ {{"nombre": "Tendencia 1", "impacto": 0.75}} ]
        }}
    ],
    "actores": [ {{"nombre": "Actor 1", "descripcion": "Desc", "puesto": "Rol"}} ],
    "tendencias": [
        {{
            "nombre": "Tendencia 1", "descripcion": "Desc", "tipo": "CUANTITATIVA",
            "indicadores": [ {{"nombre_corto": "IndT1", "descripcion": "Desc", "formula": "Z"}} ],
            "importancia": 7, "incertidumbre": 8
        }}
    ]
}}
"""
    logger.info(f"Rellenando con IA el subsistema: {subsistema.nombre}")
    resultado = generar_respuesta_llm(prompt, temperature=0.7, max_tokens=4000)

    data = (
        _extraer_json_seguro(resultado.get("text", ""))
        if resultado and resultado.get("success")
        else None
    )
    if not data:
        logger.error(
            f"Fallo crítico al extraer JSON del subsistema {subsistema.nombre}."
        )
        return False

    # 1. CREAR ACTORES
    for a in data.get("actores", []):
        ActorClave.objects.create(
            subsistema=subsistema,
            nombre=a.get("nombre", "")[:100],
            descripcion=a.get("descripcion", ""),
            puesto=a.get("puesto", "")[:100],
            activo=True,
        )

    # 2. CREAR TENDENCIAS
    tendencias_creadas = {}
    for t in data.get("tendencias", []):
        tipo_t = (
            "CUANTITATIVA"
            if "CUAN" in str(t.get("tipo", "")).upper()
            else "CUALITATIVA"
        )
        nom_t = t.get("nombre", "").strip()
        tendencia = TendenciaExterna.objects.create(
            subsistema=subsistema,
            nombre=nom_t[:150],
            nombre_corto=nom_t[:40],
            tipo_dato=tipo_t,
            descripcion=t.get("descripcion", ""),
            activo=True,
        )

        for ind in t.get("indicadores", []):
            IndicadorTendencia.objects.create(
                tendencia_externa=tendencia,
                nombre_corto=ind.get("nombre_corto", "")[:50],
                descripcion=ind.get("descripcion", ""),
                formula=ind.get("formula", ""),
            )

        imp = max(1, min(10, int(t.get("importancia", 5))))
        inc = max(1, min(10, int(t.get("incertidumbre", 5))))
        EvaluacionTendencia.objects.update_or_create(
            tendencia=tendencia,
            usuario=None,
            defaults={"importancia": imp, "incertidumbre": inc},
        )

        tendencias_creadas[nom_t] = tendencia
        Historial.objects.create(tendencia=tendencia, accion="CREADO", usuario=None)

    # 3. CREAR VARIABLES Y MAPEO PESTEL SEGURO
    MAP_PESTEL = {
        "P": "P",
        "PO": "P",
        "POLITICO": "P",
        "POLÍTICO": "P",
        "EC": "EC",
        "ECO": "EC",
        "ECONOMICO": "EC",
        "ECONÓMICO": "EC",
        "S": "S",
        "SO": "S",
        "SOCIAL": "S",
        "T": "T",
        "TE": "T",
        "TECNOLOGICO": "T",
        "TECNOLÓGICO": "T",
        "EO": "EO",
        "ECOLOGICO": "EO",
        "ECOLÓGICO": "EO",
        "AMBIENTAL": "EO",
        "L": "L",
        "LE": "L",
        "LEGAL": "L",
    }

    for v in data.get("variables", []):
        tipo_v = "E" if str(v.get("tipo", "I")).upper().startswith("E") else "I"
        nom_v = v.get("nombre", "").strip()

        variable = Variable.objects.create(
            subsistema=subsistema,
            nombre=nom_v[:150],
            nombre_corto=nom_v[:40],
            descripcion=v.get("descripcion", ""),
            tipo=tipo_v,
            activo=True,
        )

        imp = max(1, min(10, int(v.get("importancia", 5))))
        inc = max(1, min(10, int(v.get("incertidumbre", 5))))
        EvaluacionVariable.objects.update_or_create(
            variable=variable,
            usuario=None,
            defaults={"importancia": imp, "incertidumbre": inc},
        )

        # ASIGNACIÓN PESTEL ROBUSTA
        pesteles = v.get("pestel", [])
        if isinstance(pesteles, str):
            pesteles = [pesteles]

        for p in pesteles:
            val = str(p).strip().upper()
            key = MAP_PESTEL.get(val) or MAP_PESTEL.get(val[:2])
            if key:
                pestel_obj, _ = PESTEL.objects.get_or_create(tipo=key)
                variable.pestels.add(pestel_obj)

        # FALLBACK: Si la IA falló por completo, asigna 'S' (Social) por defecto para que no quede pendiente.
        if not variable.pestels.exists():
            pestel_obj, _ = PESTEL.objects.get_or_create(tipo="S")
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
            nom_rel = str(tr.get("nombre", "")).strip()
            if nom_rel in tendencias_creadas:
                try:
                    impacto = max(0.0, min(1.0, float(tr.get("impacto", 0))))
                except Exception:
                    impacto = 0.0
                VariableTendencia.objects.create(
                    variable=variable,
                    tendencia=tendencias_creadas[nom_rel],
                    impacto=impacto,
                )

        Historial.objects.create(variable=variable, accion="CREADO", usuario=None)

    return True


def evaluar_mactor(subsistema):
    actores = list(
        ActorClave.objects.filter(subsistema=subsistema, activo=True).order_by("pk")
    )
    n = len(actores)
    if n < 2:
        return

    lista_actores = "\n".join([f"{i+1}. {a.nombre}" for i, a in enumerate(actores)])
    prompt = f"""
    Matriz de influencia MACTOR para {n} actores:
    {lista_actores}
    Generá una matriz de {n}x{n} con valores 0, 1, 2 o 3. Diagonal en 0.
    JSON: {{"matriz_mactor": [[0,1,2],[1,0,3],[0,1,0]]}}
    """
    res = generar_respuesta_llm(prompt, temperature=0.3, max_tokens=1500)
    data = (
        _extraer_json_seguro(res.get("text", ""))
        if res and res.get("success")
        else None
    )

    matriz = data.get("matriz_mactor", []) if data else []

    if not matriz or len(matriz) != n:
        matriz = [
            [0 if i == j else random.randint(0, 2) for j in range(n)] for i in range(n)
        ]

    InfluenciaActor.objects.filter(actor_origen__subsistema=subsistema).delete()

    for i in range(n):
        for j in range(n):
            if i != j:
                try:
                    val = max(0, min(3, int(matriz[i][j])))
                except Exception:
                    val = random.randint(0, 2)
                InfluenciaActor.objects.create(
                    actor_origen=actores[i], actor_destino=actores[j], valor=val
                )


def generar_escenarios_schwartz(subsistema):
    variables = list(Variable.objects.filter(subsistema=subsistema, activo=True))
    if len(variables) < 2:
        return

    puntajes = []
    for v in variables:
        imp = v.promedio_importancia() or 5.0
        inc = v.promedio_incertidumbre() or 5.0
        inf = sum(
            Influencia.objects.filter(variable_origen=v).values_list("valor", flat=True)
        )
        dep = sum(
            Influencia.objects.filter(variable_destino=v).values_list(
                "valor", flat=True
            )
        )
        score = float(imp) + float(inc) + float(inf) + float(dep)
        puntajes.append((score, v))

    puntajes.sort(key=lambda x: x[0], reverse=True)
    v1, v2 = puntajes[0][1], puntajes[1][1]

    prompt = f"""
    Generá 4 escenarios cruzando la evolución de las 2 variables más críticas:
    Eje X: {v1.nombre}. Eje Y: {v2.nombre}.
    
    Respondé ÚNICAMENTE JSON:
    {{
      "escenarios": [
        {{
          "cuadrante": "Estrella Ascendente", "nombre_marketinero": "Futuro Ideal", "descripcion": "Breve desc...",
          "fortalezas": ["..."], "debilidades": ["..."], "oportunidades": ["..."], "amenazas": ["..."]
        }},
        {{
          "cuadrante": "Experto en Evolución", "nombre_marketinero": "Crecimiento Lento", "descripcion": "...",
          "fortalezas": ["..."], "debilidades": ["..."], "oportunidades": ["..."], "amenazas": ["..."]
        }},
        {{
          "cuadrante": "Retroceso Competitivo", "nombre_marketinero": "Crisis Total", "descripcion": "...",
          "fortalezas": ["..."], "debilidades": ["..."], "oportunidades": ["..."], "amenazas": ["..."]
        }},
        {{
          "cuadrante": "Proyección Brillante", "nombre_marketinero": "Revolución", "descripcion": "...",
          "fortalezas": ["..."], "debilidades": ["..."], "oportunidades": ["..."], "amenazas": ["..."]
        }}
      ]
    }}
    """
    res = generar_respuesta_llm(prompt, temperature=0.7, max_tokens=3000)
    data = (
        _extraer_json_seguro(res.get("text", ""))
        if res and res.get("success")
        else None
    )
    escenarios = data.get("escenarios", []) if data else []

    if len(escenarios) < 4:
        logger.warning(f"Fallback activado para Escenarios en {subsistema.nombre}")
        escenarios = [
            {
                "cuadrante": "Estrella Ascendente",
                "nombre_marketinero": "Escenario Optimista",
                "descripcion": "El mejor escenario posible.",
                "fortalezas": ["Fuerte inversión"],
                "debilidades": ["Ninguna"],
                "oportunidades": ["Crecimiento global"],
                "amenazas": ["Baja cautela"],
            },
            {
                "cuadrante": "Experto en Evolución",
                "nombre_marketinero": "Avance Moderado",
                "descripcion": "Mejora con precaución.",
                "fortalezas": ["Estabilidad"],
                "debilidades": ["Lentitud"],
                "oportunidades": ["Nuevos nichos"],
                "amenazas": ["Competencia"],
            },
            {
                "cuadrante": "Retroceso Competitivo",
                "nombre_marketinero": "Escenario Pesimista",
                "descripcion": "El peor escenario.",
                "fortalezas": ["Resiliencia básica"],
                "debilidades": ["Falta de recursos"],
                "oportunidades": ["Cambio de rumbo"],
                "amenazas": ["Colapso"],
            },
            {
                "cuadrante": "Proyección Brillante",
                "nombre_marketinero": "Innovación Disruptiva",
                "descripcion": "Cambio radical positivo.",
                "fortalezas": ["Alta tecnología"],
                "debilidades": ["Riesgo alto"],
                "oportunidades": ["Dominio del mercado"],
                "amenazas": ["Regulaciones estrictas"],
            },
        ]

    EscenarioSchwartz.objects.filter(subsistema=subsistema).delete()

    for esc in escenarios:
        foda_html = f"<p>{esc.get('descripcion', '')}</p><div class='mt-3'><strong>Análisis FODA:</strong><ul class='mb-0'>"
        foda_html += f"<li><span class='text-success fw-bold'>Fortalezas:</span> {', '.join(esc.get('fortalezas', []))}</li>"
        foda_html += f"<li><span class='text-danger fw-bold'>Debilidades:</span> {', '.join(esc.get('debilidades', []))}</li>"
        foda_html += f"<li><span class='text-info fw-bold'>Oportunidades:</span> {', '.join(esc.get('oportunidades', []))}</li>"
        foda_html += f"<li><span class='text-warning fw-bold'>Amenazas:</span> {', '.join(esc.get('amenazas', []))}</li></ul></div>"

        EscenarioSchwartz.objects.create(
            subsistema=subsistema,
            cuadrante=esc.get("cuadrante", "Desconocido"),
            nombre_marketinero=esc.get("nombre_marketinero", "Escenario Base"),
            descripcion=foda_html,
        )


def generar_estructura_prospectiva(tema):
    prompt = f"""
    Tema: {tema.nombre}. Generá EXACTAMENTE 4 subsistemas clave.
    JSON: {{"subsistemas": [ {{"nombre": "Sub 1", "descripcion": "Desc"}} ]}}
    """
    resultado = generar_respuesta_llm(prompt, temperature=0.7, max_tokens=1500)
    data = (
        _extraer_json_seguro(resultado.get("text", ""))
        if resultado and resultado.get("success")
        else None
    )

    if not data or "subsistemas" not in data:
        raise Exception("La IA no pudo generar los subsistemas correctamente.")

    sistema = Sistema.objects.create(
        tema=tema, nombre=f"Sistema de {tema.nombre}", descripcion=tema.descripcion
    )

    for s in data.get("subsistemas", []):
        sub = Subsistema.objects.create(
            sistema=sistema,
            nombre=s.get("nombre", "")[:150],
            descripcion=s.get("descripcion", ""),
            activo=True,
        )
        _rellenar_subsistema_con_ia(sub)


def generar_datos_nuevo_subsistema(subsistema, usuario):
    exito = _rellenar_subsistema_con_ia(subsistema)
    if exito:
        generar_evaluaciones_e_influencias(subsistema.sistema.tema, usuario)
        return True
    return False


def calcular_impacto_variable_tendencia(variable, tendencia):
    prompt = f"""
    Variable: {variable.nombre}. Tendencia: {tendencia.nombre}.
    Evaluá impacto DIRECTO. Respondé solo decimal 0 a 1.
    """
    resultado = generar_respuesta_llm(prompt, temperature=0.2)
    try:
        valor = float(resultado.get("text", "0").strip())
        return max(0.0, min(1.0, valor))
    except Exception:
        return 0.0


def generar_evaluaciones_e_influencias(tema, usuario=None):
    variables = list(
        Variable.objects.filter(subsistema__sistema__tema=tema).order_by("pk")
    )
    if not variables:
        return
    amount = len(variables)
    lista_vars = "\n".join([f"{i + 1}. {v.nombre}" for i, v in enumerate(variables)])

    prompt_matriz = f"""
    Matriz MIC-MAC {amount}x{amount} (0 a 3) para:\n{lista_vars}
    JSON: {{"matriz_influencia": [[0,1],[1,0]]}}
    """
    res = generar_respuesta_llm(prompt_matriz, temperature=0.2, max_tokens=3000)
    data = (
        _extraer_json_seguro(res.get("text", ""))
        if res and res.get("success")
        else None
    )

    matriz = data.get("matriz_influencia", []) if data else []

    if len(matriz) != amount:
        logger.warning("Fallback activado para Matriz MICMAC.")
        matriz = [
            [0 if i == j else random.randint(0, 2) for j in range(amount)]
            for i in range(amount)
        ]

    for i, var_origen in enumerate(variables):
        for j, var_destino in enumerate(variables):
            if i != j:
                try:
                    valor = max(0, min(3, int(matriz[i][j])))
                except Exception:
                    valor = random.randint(0, 1)
                Influencia.objects.update_or_create(
                    variable_origen=var_origen,
                    variable_destino=var_destino,
                    defaults={"valor": valor},
                )

    for sub in Subsistema.objects.filter(sistema__tema=tema, activo=True):
        evaluar_mactor(sub)
        generar_escenarios_schwartz(sub)
