# HAAPAR_UNLa

Sistema web para la asistencia y sistematización de procesos de **Prospectiva Estratégica**, desarrollado con Django e integrado con inteligencia artificial generativa.

## Descripción

**HAAPAR_UNLa** es una aplicación web desarrollada en el marco del Posgrado en Prospectiva Estratégica de la Universidad de Ciencias Empresariales y Sociales (UCES).

El sistema tiene como objetivo asistir determinadas etapas del proceso prospectivo mediante la centralización de la información y la integración de diferentes herramientas de análisis, permitiendo gestionar variables, actores, tendencias y relaciones dentro de un mismo entorno de trabajo.

La aplicación incorpora **inteligencia artificial generativa** como mecanismo de asistencia. A partir de la información proporcionada por el usuario, el sistema puede generar propuestas iniciales de subsistemas, variables, actores y tendencias, además de asistir determinados procesos de evaluación y análisis.

Los resultados generados por inteligencia artificial pueden ser posteriormente revisados, modificados, eliminados o complementados por el usuario.

## Principales funcionalidades

* Gestión de usuarios y autenticación.
* Gestión de roles y permisos.
* Creación y gestión de proyectos o temas de análisis.
* Organización mediante sistemas y subsistemas.
* Gestión de variables internas y externas.
* Gestión de tendencias externas.
* Gestión de actores clave.
* Asociación de variables con dimensiones PESTEL.
* Gestión de indicadores.
* Evaluación de importancia e incertidumbre.
* Registro de relaciones de influencia entre variables.
* Análisis MICMAC.
* Análisis MACTOR.
* Análisis FODA.
* Análisis PESTEL.
* Generación y representación de escenarios mediante los ejes de Peter Schwartz.
* Visualizaciones interactivas.
* Historial de determinadas operaciones.
* Integración con inteligencia artificial generativa.
* Registro de interacciones con el servicio de inteligencia artificial.
* API mediante Django REST Framework.

## Tecnologías utilizadas

### Backend

* **Python 3.12**
* **Django 5.1.6**
* **Django REST Framework**

### Frontend

* **HTML**
* **CSS**
* **JavaScript**
* **Bootstrap 5.3**
* **Chart.js**
* **Highcharts**
* **Font Awesome**

### Base de datos

* **PostgreSQL 15**

### Inteligencia artificial

* **OpenRouter** como proveedor de acceso al modelo.
* **Llama 3.1 8B Instruct** como modelo de lenguaje.
* Prompts estructurados para generación de información prospectiva.
* Respuestas procesadas en formato JSON.
* Mecanismos de validación y recuperación ante errores.

### Infraestructura y herramientas

* **Docker**
* **Docker Compose**
* **Git**
* **GitHub**
* **Visual Studio Code**

## Arquitectura general

La aplicación se organiza en diferentes componentes que permiten separar la presentación, la lógica de negocio, la persistencia de datos y la integración con servicios externos.

### Capa de presentación

La interfaz de usuario está desarrollada mediante plantillas de Django, HTML, CSS y JavaScript, utilizando Bootstrap como framework de componentes visuales.

Las visualizaciones de los análisis se implementan mediante Chart.js y Highcharts.

### Capa de aplicación

La lógica principal del sistema se desarrolla con Django y Python.

Django gestiona:

* autenticación y usuarios;
* permisos;
* vistas;
* formularios;
* lógica de negocio;
* acceso a la base de datos;
* gestión de proyectos y elementos prospectivos.

Django REST Framework se utiliza para exponer determinadas funcionalidades mediante API.

### Capa de persistencia

La información se almacena en **PostgreSQL** mediante el sistema de modelos de Django.

El modelo de datos representa las principales entidades del proceso prospectivo, incluyendo temas, sistemas, subsistemas, variables, tendencias, actores, evaluaciones, influencias e historial.

### Capa de inteligencia artificial

La integración con inteligencia artificial se encuentra separada de la lógica principal de la aplicación.

El sistema utiliza **OpenRouter** para comunicarse con el modelo **Llama 3.1 8B Instruct**.

La integración contempla:

1. Construcción del contexto y del prompt.
2. Envío de la solicitud al modelo.
3. Recepción de la respuesta.
4. Procesamiento de la respuesta.
5. Validación de la estructura y los valores.
6. Almacenamiento de la información obtenida.
7. Registro de la interacción.

## Inteligencia artificial

La inteligencia artificial se utiliza principalmente como mecanismo de asistencia dentro del proceso prospectivo.

### Generación de estructura prospectiva

Durante la creación de un proyecto, el sistema utiliza información como:

* nombre o tema;
* descripción;
* horizonte temporal;
* territorio.

A partir de estos datos, el modelo puede generar una estructura inicial compuesta por subsistemas, variables, actores y tendencias externas.

### Evaluaciones e influencias

La inteligencia artificial también puede asistir la generación de:

* evaluaciones de importancia e incertidumbre;
* relaciones de influencia entre variables;
* relaciones entre actores;
* impactos entre variables y tendencias.

### Escenarios

La aplicación utiliza información obtenida durante el análisis para asistir la generación de escenarios asociados a los ejes de Peter Schwartz.

### Control de respuestas

Las respuestas del modelo son procesadas antes de ser incorporadas al sistema.

Se realizan controles sobre:

* formato JSON;
* cantidad de elementos;
* dimensiones de matrices;
* rangos de valores;
* estructura de los datos recibidos.

Además, las solicitudes al servicio de IA cuentan con un mecanismo de reintentos mediante espera progresiva (*exponential backoff*) para afrontar errores temporales de comunicación.

## Configuración del proyecto

### Requisitos

Para ejecutar el proyecto directamente en un entorno local se requiere:

* Python 3.12
* PostgreSQL 15
* pip
* Git

También es posible ejecutar el proyecto utilizando Docker y Docker Compose.

### Clonar el repositorio

```bash
git clone https://github.com/NicolasPerezUNLaSMN/HAAPAR_UNLa.git
cd HAAPAR_UNLa
```

### Crear entorno virtual

En Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

## Variables de entorno

La aplicación utiliza variables de entorno para evitar definir directamente en el código fuente parámetros sensibles y configuraciones específicas del entorno.

Entre las principales variables utilizadas se encuentran:

```env
SECRET_KEY=tu_clave_secreta
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=nombre_base
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=localhost
DB_PORT=5432

API_KEY_OPENROUTER=tu_clave_de_openrouter
AI_PROVIDER=openrouter
AI_MODEL=meta-llama/llama-3.1-8b-instruct
```

Los valores reales de las claves y credenciales **no deben incorporarse al repositorio**.

## Configuración de PostgreSQL

La aplicación utiliza PostgreSQL como base de datos.

Para una ejecución local, se deben configurar las variables de conexión correspondientes en el archivo `.env`.

Una vez configurada la base de datos, se deben ejecutar las migraciones:

```bash
python manage.py migrate
```

## Ejecución local

Una vez configurado el entorno, la aplicación puede iniciarse mediante:

```bash
python manage.py runserver
```

Por defecto, Django ejecutará la aplicación en:

```text
http://127.0.0.1:8000/
```

## Ejecución mediante Docker

El proyecto incluye un `Dockerfile` y un archivo `docker-compose.yml`.

La configuración define dos servicios principales:

* **web:** aplicación Django.
* **db:** base de datos PostgreSQL 15.

Para iniciar los servicios:

```bash
docker compose up --build
```

El servicio web ejecuta las migraciones de Django al iniciar el contenedor y posteriormente inicia la aplicación.

La base de datos utiliza un volumen para conservar la información almacenada entre ejecuciones de los contenedores.

La aplicación queda disponible en:

```text
http://localhost:8000/
```

## API

La aplicación utiliza Django REST Framework para exponer determinadas funcionalidades.

Entre los endpoints disponibles se encuentran:

### Temas

```text
/api/temas/
```

Permite consultar los temas activos asociados al usuario autenticado.

### Variables

```text
/api/variables/
```

Permite consultar variables activas mediante la API.

### FODA

```text
/api/foda/<tema_id>/
```

Permite obtener información asociada a un tema para su utilización en el análisis FODA.

### Proyectos

El proyecto también dispone de rutas generadas mediante `DefaultRouter` para la gestión de temas:

```text
/api/proyectos/
```

### Variables mediante ViewSet

Las variables cuentan además con un `ViewSet` registrado mediante Django REST Framework:

```text
/api/variables/
```

Las operaciones disponibles dependen del método HTTP utilizado y de los permisos correspondientes.

## Estructura general del proyecto

La aplicación se organiza en diferentes módulos según las responsabilidades principales del sistema.

Entre los componentes principales se encuentran:

```text
haapar_unla_app/
│
├── models.py
├── views.py
├── urls.py
├── serializers.py
├── api.py
├── ia_service.py
├── ai_client.py
├── retry_utils.py
│
├── views/
│   ├── variables.py
│   ├── foda.py
│   ├── proyectos.py
│   └── api.py
│
├── templates/
│
├── static/
│
└── tests.py
```

Los nombres y distribución de archivos pueden variar según la versión actual del repositorio.

## Pruebas

El proyecto incorpora pruebas automatizadas utilizando las herramientas de testing de Django y Django REST Framework.

Las pruebas implementadas contemplan, entre otros aspectos:

* procesamiento de respuestas JSON;
* restricciones de los modelos;
* cálculo de promedios de evaluaciones;
* comportamiento de señales;
* acceso a vistas;
* consulta de proyectos mediante API;
* creación de proyectos mediante API.

Las pruebas pueden ejecutarse mediante:

```bash
python manage.py test
```

## Control de versiones

El código fuente se gestiona mediante **Git** y **GitHub**.

Durante el desarrollo se utilizaron diferentes ramas para organizar funcionalidades, correcciones y tareas específicas. También se utilizaron Pull Requests para integrar determinados cambios al proyecto.

## Documentación

Este archivo contiene la información básica necesaria para comprender, configurar y ejecutar HAAPAR_UNLa.

La documentación se complementa con:

* código fuente;
* modelos de datos;
* configuración de Docker;
* pruebas automatizadas;
* historial de cambios gestionado mediante Git;
* documentación desarrollada como parte del Trabajo Final de Ingeniería.

## Consideraciones de seguridad

Las claves de acceso, contraseñas y demás información sensible deben mantenerse fuera del código fuente y del repositorio.

Se recomienda utilizar un archivo `.env` para las variables de entorno y evitar compartir sus valores reales.

En entornos distintos al desarrollo local, se deben revisar las configuraciones de seguridad de Django, incluyendo `DEBUG`, `ALLOWED_HOSTS`, claves secretas y credenciales de acceso a la base de datos.

## Alcance

HAAPAR_UNLa fue desarrollado en el contexto académico del Posgrado en Prospectiva Estratégica de la UCES.

El sistema está orientado a asistir determinadas etapas del proceso prospectivo mediante la integración de herramientas de análisis e inteligencia artificial generativa.

La generación realizada mediante IA constituye una propuesta inicial que puede ser revisada y modificada por el usuario. Por lo tanto, el sistema no reemplaza la interpretación, evaluación y toma de decisiones propias del proceso prospectivo.

