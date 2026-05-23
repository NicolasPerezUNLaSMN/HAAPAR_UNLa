import json
import logging
import re
from ..models import Historial, Sistema, Subsistema, Variable, ActorClave, TendenciaExterna, EvaluacionVariable, Influencia
from .ai_client import generar_respuesta_llm
from ..models import IAInteraction
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
    
    IMPORTANTE:
    Las variables deben ser CUANTIFICABLES, es decir, deben poder medirse numéricamente.

    Las tendencias deben ser de dos tipos:

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
     # Guardar interacción en la base de datos
    IAInteraction.objects.create(
        tema=tema,
        usuario=None,  # o el usuario actual si lo tenés en contexto
        prompt=prompt,
        respuesta=resultado.get('text'),
        success=resultado.get('success', False),
        error=resultado.get('error')
    )

    if not resultado.get('success'):
        logger.error(f"La IA falló al estructurar: {resultado.get('error')}")
        return

    content = resultado.get('text')
    
    # limpiar markdown
    content = content.replace("```json", "").replace("```", "").strip()

    # extraer JSON si viene texto extra
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
        logger.error(content)
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

            variable = Variable.objects.create(
                subsistema=subsistema,
                nombre=v.get("nombre", ""),
                nombre_corto=v.get("nombre", "")[:40],
                descripcion=v.get("descripcion", ""),
                tipo=tipo,
                activo=True
            )

            Historial.objects.create(
                variable=variable,
                accion='CREADO',
                usuario=None
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

            tipo = t.get("tipo", "CUALITATIVA")

            # validar tipo
            if tipo not in ["CUALITATIVA", "CUANTITATIVA"]:
                tipo = "CUALITATIVA"

            tendencia = TendenciaExterna.objects.create(
                subsistema=subsistema,
                nombre=t.get("nombre", ""),
                nombre_corto=t.get("nombre", "")[:40],
                tipo_dato=tipo, 
                descripcion=t.get("descripcion", ""),
                activo=True
            )
            
            Historial.objects.create(
                tendencia=tendencia,
                accion='CREADO',
                usuario=None
            )
            

def generar_evaluaciones_e_influencias(tema, usuario):
    
    variables = list(Variable.objects.filter(subsistema__sistema__tema=tema).order_by('pk'))
    
    if not variables:
        return

    lista_vars_texto = "\n".join([f"[{i}] {v.nombre}" for i, v in enumerate(variables)])
    cantidad = len(variables)

    prompt = f"""
    Sos un expert en prospectiva estratégica y análisis MIC-MAC.
    Acabo de identificar {cantidad} variables clave para el proyecto académico: "{tema.nombre}".
    
    Las variables, en su orden exacto, son:
    {lista_vars_texto}

    Necesito que actúes como un panel de expertos y evalúes las relaciones matemáticas entre ellas.
    
    IMPORTANTE: Respondé ÚNICAMENTE con el objeto JSON estructurado tal cual el ejemplo. 
    NO incluyas introducciones, NO incluyas conclusiones, ni bloques de código markdown (```json). Solo el JSON puro.

    Estructura requerida:
    {{
      "evaluaciones": [
        {{"importancia": 8, "incertidumbre": 5}}
      ],
      "matriz_influencia": [
        [0, 2, 1, 3],
        [1, 0, 2, 0]
      ]
    }}
    """

    logger.info(f"Enviando solicitud matemática a la IA para {cantidad} variables...")
    resultado = generar_respuesta_llm(prompt, temperature=0.1, max_tokens=4000)

    if not resultado.get('success'):
        logger.error(f"ERROR: La IA falló al generar la matriz: {resultado.get('error')}")
        return

    content = resultado.get('text').strip()

    # Buscador robusto con expresiones regulares para quedarse solo con el contenido entre llaves
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)
    else:
        logger.error("ERROR: No se encontró estructura de JSON en la respuesta de la IA.")
        logger.error(f"Contenido crudo recibido: {content}")
        return

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("ERROR: La IA falló al parsear la matriz matemática JSON. Las variables quedarán en 0.")
        logger.error(f"Contenido que falló al parsear: {content}")
        return 

    evaluaciones = data.get("evaluaciones", [])
    matriz = data.get("matriz_influencia", [])

    for i, var in enumerate(variables):
        imp = 0
        inc = 0
        if i < len(evaluaciones):
            imp = evaluaciones[i].get("importancia", 0)
            inc = evaluaciones[i].get("incertidumbre", 0)
            
        EvaluacionVariable.objects.create(
            variable=var,
            usuario=usuario,
            importancia=imp,
            incertidumbre=inc
        )
        Historial.objects.create(
            variable=var,
            usuario=usuario,
            accion='EVALUACION'
        )

    for i, var_origen in enumerate(variables):
        for j, var_destino in enumerate(variables):
            if i != j:
                valor_ia = 0
                if i < len(matriz) and j < len(matriz[i]):
                    valor_ia = matriz[i][j]
                
                Influencia.objects.create(
                    variable_origen=var_origen,
                    variable_destino=var_destino,
                    valor=valor_ia
                )
                
