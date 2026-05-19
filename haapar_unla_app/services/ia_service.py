import json
import logging
from dotenv import load_dotenv 
import os
from openai import OpenAI 

# Configuramos el logger
logger = logging.getLogger(__name__)

from ..models import Historial, Sistema, Subsistema, Variable, ActorClave, TendenciaExterna,EvaluacionVariable, Influencia

load_dotenv(override=True)

# 2. Obtenemos la clave específicamente
api_key = os.getenv("API_KEY_OPENROUTER")

# 3. Verificación de seguridad usando logging en vez de print
if api_key:
    logger.info("Clave de IA cargada correctamente.")
else:
    logger.error("No se encontró ninguna clave de IA.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

print(api_key)
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
    
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    content = response.choices[0].message.content

    print("RESPUESTA IA:")
    print(content)

    # limpiar markdown
    content = content.replace("```json", "").replace("```", "").strip()

    # extraer JSON si viene texto extra
    start = content.find("{")
    end = content.rfind("}") + 1
    content = content[start:end]

    if not content:
        print("La IA devolvió contenido vacío")
        return

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        print("JSON inválido recibido:")
        print(content)
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
                tipo_dato=tipo,  # ahora guarda el tipo real
                descripcion=t.get("descripcion", ""),
                activo=True
            )
            
            
            Historial.objects.create(
                tendencia=tendencia,
                accion='CREADO',
                usuario=None
            )

def generar_evaluaciones_e_influencias(tema, usuario):
    """
    Paso 2: Genera la matriz matemática (FODA / MIC-MAC) usando análisis lógico de la IA
    """
    # 1. Traemos las variables ordenadas por ID para asegurar la consistencia de la matriz
    variables = list(Variable.objects.filter(subsistema__sistema__tema=tema).order_by('pk'))
    
    if not variables:
        return

    # Armamos una lista de texto para pasarle a la IA
    lista_vars_texto = "\n".join([f"[{i}] {v.nombre}" for i, v in enumerate(variables)])
    cantidad = len(variables)

    prompt = f"""
    Sos un experto en prospectiva estratégica y análisis MIC-MAC.
    Acabo de identificar {cantidad} variables clave para el proyecto académico: "{tema.nombre}".
    
    Las variables, en su orden exacto, son:
    {lista_vars_texto}

    Necesito que actúes como un panel de expertos y evalúes las relaciones matemáticas entre ellas.
    Respondé SOLO con un JSON válido, sin formato markdown ni texto explicativo adicional.
    Estructura requerida:

    {{
      "evaluaciones": [
        // Array exacto de {cantidad} objetos, en el mismo orden que las variables.
        // "importancia" (1 al 10): Qué tan vital es para el futuro del proyecto.
        // "incertidumbre" (1 al 10): Qué tan impredecible es su evolución.
        {{"importancia": 8, "incertidumbre": 5}}
      ],
      "matriz_influencia": [
        // Una matriz 2D exacta de {cantidad} filas por {cantidad} columnas.
        // El valor en la fila 'i' y columna 'j' es cuánto influye directamente la variable 'i' sobre la 'j'.
        // Valores permitidos: 0 (nula), 1 (débil), 2 (moderada), 3 (fuerte).
        // La diagonal principal (influencia de una variable sobre sí misma) DEBE ser siempre 0.
        [0, 2, 1, 3],
        [1, 0, 2, 0]
      ]
    }}
    """

    print(f"Enviando solicitud matemática a la IA para {cantidad} variables...")

    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, 
        max_tokens=4000
    )

    content = response.choices[0].message.content.strip()
    
    print("RESPUESTA IA (MATEMÁTICA):")
    print(content)

    # Limpieza del JSON
    content = content.replace("```json", "").replace("```", "").strip()
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end != -1:
        content = content[start:end]

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        print("ERROR: La IA falló al generar la matriz matemática JSON. Las variables quedarán en 0 para carga manual.")
        return 

    evaluaciones = data.get("evaluaciones", [])
    matriz = data.get("matriz_influencia", [])

    # 2. Guardamos las Evaluaciones en la BD
    for i, var in enumerate(variables):
        imp = 0
        inc = 0
        # Validamos que la IA nos haya devuelto el array completo
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

    # 3. Guardamos la Matriz de Influencia en la BD
    for i, var_origen in enumerate(variables):
        for j, var_destino in enumerate(variables):
            if i != j: # Evitamos guardar la diagonal principal en la tabla de relaciones
                valor_ia = 0
                # Validamos que la matriz generada no esté rota o sea más chica de lo esperado
                if i < len(matriz) and j < len(matriz[i]):
                    valor_ia = matriz[i][j]
                
                Influencia.objects.create(
                    variable_origen=var_origen,
                    variable_destino=var_destino,
                    valor=valor_ia
                )

""""
Al crear el reporte en views.py, primero se ejecuta el prompt original de tu código que inventa los subsistemas y variables.
Inmediatamente después, se dispara este segundo prompt, que lee las variables que la IA recién inventó, las cruza lógicamente, y 
devuelve las influencias reales (por ejemplo, detectando que "Inflación" influye un 3 sobre "Costo de infraestructura").
Todo se guarda en PostgreSQL. Cuando el usuario entra a foda_graficos, ve una matriz armada inteligentemente, 
pero que él puede editar si considera que la IA se equivocó.
"""





