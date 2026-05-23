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

    # IMPORTANTE: Eliminamos el índice "[i]" para no confundir a la IA
    lista_vars_texto = "\n".join([f"- {v.nombre}" for v in variables])
    cantidad = len(variables)

    prompt = f"""
    Sos un experto en prospectiva estratégica y análisis MIC-MAC.
    Acabo de identificar exactamente {cantidad} variables clave para el proyecto: "{tema.nombre}".
    
    Las variables, en su orden exacto, son:
    {lista_vars_texto}

    Necesito que actúes como un panel de expertos y evalúes matemáticamente estas {cantidad} variables.
    
    REGLAS ESTRICTAS (Si no las cumplís, el análisis fallará):
    1. "evaluaciones": DEBE ser una lista con exactamente {cantidad} objetos. Un objeto para cada variable.
       Cada objeto debe tener "importancia" (entero del 1 al 10) e "incertidumbre" (entero del 1 al 10).
    2. "matriz_influencia": DEBE ser una matriz cuadrada exacta de {cantidad} filas por {cantidad} columnas.
    3. VALORES DE INFLUENCIA: Los únicos números que podés usar dentro de la matriz son 0, 1, 2 o 3. 
       - 0 = Sin influencia
       - 1 = Influencia débil
       - 2 = Influencia moderada
       - 3 = Influencia fuerte
       ¡PROHIBIDO USAR NÚMEROS MAYORES A 3! ¡PROHIBIDO PONER EL NÚMERO DE LA VARIABLE!
    4. La diagonal de la matriz (una variable contra sí misma) siempre debe ser 0.

    Respondé ÚNICAMENTE con un JSON válido. No uses bloques de código markdown, ni texto extra.
    
    Ejemplo de estructura esperada:
    {{
      "evaluaciones": [
        {{"importancia": 8, "incertidumbre": 5}},
        {{"importancia": 7, "incertidumbre": 8}}
        // ... (debe haber {cantidad} objetos en total)
      ],
      "matriz_influencia": [
        [0, 2, 1, 3], // ... (debe tener {cantidad} números, todos entre 0 y 3)
        [1, 0, 2, 0]  // ... (debe tener {cantidad} números, todos entre 0 y 3)
        // ... (debe haber {cantidad} filas en total)
      ]
    }}
    """

    logger.info(f"Enviando solicitud matemática a la IA para {cantidad} variables...")
    resultado = generar_respuesta_llm(prompt, temperature=0.1, max_tokens=4000)

    if not resultado.get('success'):
        logger.error(f"ERROR: La IA falló al generar la matriz: {resultado.get('error')}")
        return

    content = resultado.get('text').strip()

    # Buscador robusto con expresiones regulares para quedarse solo con el JSON
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)
    else:
        logger.error("ERROR: No se encontró estructura JSON en la respuesta de la IA.")
        return

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("ERROR: La IA falló al parsear la matriz matemática JSON.")
        return 

    evaluaciones = data.get("evaluaciones", [])
    matriz = data.get("matriz_influencia", [])

    for i, var in enumerate(variables):
        # Valores por defecto de 5 en caso de que la IA se quede corta
        imp, inc = 5, 5
        if i < len(evaluaciones):
            try:
                # Blindaje contra alucinaciones (forzar a estar entre 1 y 10)
                imp = max(1, min(10, int(evaluaciones[i].get("importancia", 5))))
                inc = max(1, min(10, int(evaluaciones[i].get("incertidumbre", 5))))
            except (ValueError, TypeError):
                pass
            
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
                    try:
                        # Blindaje absoluto: Si la IA tira un 15, lo bajamos a 3. Si tira un texto, va 0.
                        val = int(matriz[i][j])
                        valor_ia = max(0, min(3, val))
                    except (ValueError, TypeError):
                        valor_ia = 0
                
                Influencia.objects.create(
                    variable_origen=var_origen,
                    variable_destino=var_destino,
                    valor=valor_ia
                )
                
