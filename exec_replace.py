import os
import re

# Define the replacements
replacements = {
    'iniciar_sesion': 'sign-in',
    'registro': 'sign-up',
    'cerrar_sesion': 'log-out',
    'listar_proyectos': 'listar-proyectos',
    'proyecto_detalle': 'proyecto-detalle',
    'eliminar_proyecto': 'eliminar-proyecto',
    'variable_detalle': 'variable-detalle',
    'editar_variable': 'editar-variable',
    'eliminar_variable': 'eliminar-variable',
    'crear_variable': 'crear-variable',
    'historial_variables_subsistema': 'historial-variables-subsistema',
    'foda_graficos': 'foda-graficos',
    'actor_detalle': 'actor-detalle',
    'editar_actor': 'editar-actor',
    'eliminar_actor': 'eliminar-actor',
    'crear_actor': 'crear-actor',
    'tendencia_detalle': 'tendencia-detalle',
    'editar_tendencia': 'editar-tendencia',
    'eliminar_tendencia': 'eliminar-tendencia',
    'crear_tendencia': 'crear-tendencia',
    'password_reset_request': 'password-reset-request',
    'password_reset_done': 'password-reset-done',
    'password_reset_complete': 'password-reset-complete',
    'password_reset_confirm': 'password-reset-confirm',
    'reactivar_cuenta': 'reactivar-cuenta',
    'asignar_colaboradores': 'asignar-colaboradores',
    'crear_subsistema': 'crear-subsistema',
    'eliminar_subsistema': 'eliminar-subsistema',
}

templates_dir = r'c:\Users\Guido\HAAPAR_UNLa.worktrees\agents-estandarizar-nombres-url-kebab-case\haapar_unla_app\templates'

files_modified = 0
total_replacements = 0
modified_files = []

for root, dirs, files in os.walk(templates_dir):
    for filename in files:
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                file_replacements = 0
                
                for old_name, new_name in replacements.items():
                    pattern = r"(['\"])(" + re.escape(old_name) + r")(['\"])"
                    new_string = r"\1" + new_name + r"\3"
                    content, count = re.subn(pattern, new_string, content)
                    file_replacements += count
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_modified += 1
                    total_replacements += file_replacements
                    rel_path = os.path.relpath(filepath, templates_dir)
                    modified_files.append((rel_path, file_replacements))
            except Exception as e:
                print("ERROR: {}".format(filepath))

print("Modified {} files with {} total replacements".format(files_modified, total_replacements))
if modified_files:
    for filepath, count in modified_files:
        print("  - {}: {} replacements".format(filepath, count))
