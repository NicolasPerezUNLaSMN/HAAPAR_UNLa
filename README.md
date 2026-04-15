# Desarrollo de un Sistema Web Django con Integracion de IA "HAAPAR"

## Planteamiento del problema
La Universidad de Ciencias Empresariales está interesada en incorporar herramientas de automatización mediante IA para la planificación de futuros y estudios del tiempo, en la carrera de posgrado de Prospectiva Estratégica.

El propósito de este proyecto es desarrollar un sistema web basado en Django que automatice la carga y gestión de tablas mediante la integración con la API de Chat GPT. 

Si bien toda la información deberá generarse automáticamente con IA, cada tabla deberá tener una interfaz para realizar crud a mano sobre ella. Y todos los productos deberán calcularse tras cualquier cambio.

## Tecnologias a Usar (Primera Version)
<span>
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54"/>
  <img src="https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white"/>
  <img src="https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white"/>
  <img src="https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white"/>
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black"/>
  <img src="https://img.shields.io/badge/bootstrap-%238511FA.svg?style=for-the-badge&logo=bootstrap&logoColor=white"/>
  <img src="https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)"/>
  <img src="https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray"/>
</span>

## Arquitectura Final de la Base de Datos
Aun en desarrollo...

## Capa de presentacion: Frontend con Bootstrap (HTML + CSS + JavaScript)
Bootstrap sigue siendo una de las herramientas más populares para crear sitios web responsivos con componentes predefinidos y una comunidad activa. Permite personalizar fácilmente diseños y es ideal para proyectos de todos los tamaños.

## Capa de aplicacion: Backend con Django (Python)
Django es un potente framework de desarrollo web de código abierto, escrito en Python. Su objetivo principal es facilitar la creación de aplicaciones web complejas y basadas en bases de datos, siguiendo el principio "Don't Repeat Yourself" (DRY) y priorizando el desarrollo rápido.

## Capa de persistencia: Base de Datos con PostgreSQL (Relacional)
PostgreSQL es un potente sistema de gestión de bases de datos relacionales de código abierto (RDBMS), conocido por su fiabilidad, robustez y rendimiento. Es altamente extensible y cumple rigurosamente con los estándares SQL.

## Consumo entre capas: Django API REST
Django REST Framework (DRF) es una potente y flexible herramienta construida sobre el framework web Django, diseñada específicamente para facilitar la creación de APIs web RESTful. Permite a los desarrolladores construir interfaces de programación de aplicaciones (APIs) de manera rápida y eficiente, aprovechando la robustez de Django.

# Configuracion del Proyecto

## Requisitos previos
Antes de comenzar, asegúrate de tener instalado en tu sistema:
- Python 3.8 o superior
- PostgreSQL
- pip (gestor de paquetes de Python)
- virtualenv (para crear entornos virtuales)

## Instalacion
Sigue los pasos a continuación para configurar el proyecto en tu máquina local:

### 1. Clona este repositorio
```
git clone https://github.com/NicolasPerezUNLaSMN/HAAPAR_UNLa.git
cd HAAPAR_UNLa
```

### 2. Instala dependencias

Usa un entorno virtual y luego instala las dependencias listadas en `requirements.txt`:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

### 3. Configura la clave de OpenAI

Coloca tu clave en una variable de entorno llamada `OPENAI_API_KEY`. En PowerShell:

```powershell
$env:OPENAI_API_KEY = 'sk-...'
```

O agrega la línea `OPENAI_API_KEY=sk-...` en un archivo `.env` en la raíz del proyecto (recuerda nunca subirlo a git).

### 4. Endpoint de ChatGPT

Se añadió un endpoint interno POST `/api/chatgpt/` que recibe JSON con la forma:

```json
{"prompt": "Tu pregunta o prompt aquí"}
```

Devuelve JSON con la respuesta: `{ "success": true, "text": "Respuesta generada" }`.

En PowerShell puedes probarlo con curl (Windows 10/11 PowerShell incluye curl aliasing a Invoke-WebRequest; si tienes curl real, úsalo):

```powershell
# usando curl real si está instalado
curl -X POST http://127.0.0.1:8000/api/chatgpt/ -H "Content-Type: application/json" -d '{"prompt":"Hola"}'
```

Notas de seguridad: Este endpoint es un ejemplo mínimo. En producción debes protegerlo con autenticación, control de uso (rate limiting) y sanitizar/registrar las entradas.
