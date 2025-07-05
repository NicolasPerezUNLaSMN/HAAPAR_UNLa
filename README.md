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
