#!/usr/bin/env python3
"""Replace snake_case URL names with kebab-case in HTML templates."""
import os
import re
import sys

# Define the replacements
replacements = [
    ('iniciar_sesion', 'sign-in'),
    ('registro', 'sign-up'),
    ('cerrar_sesion', 'log-out'),
    ('listar_proyectos', 'listar-proyectos'),
    ('proyecto_detalle', 'proyecto-detalle'),
    ('eliminar_proyecto', 'eliminar-proyecto'),
    ('variable_detalle', 'variable-detalle'),
    ('editar_variable', 'editar-variable'),
    ('eliminar_variable', 'eliminar-variable'),
    ('crear_variable', 'crear-variable'),
    ('historial_variables_subsistema', 'historial-variables-subsistema'),
    ('foda_graficos', 'foda-graficos'),
    ('actor_detalle', 'actor-detalle'),
    ('editar_actor', 'editar-actor'),
    ('eliminar_actor', 'eliminar-actor'),
    ('crear_actor', 'crear-actor'),
    ('tendencia_detalle', 'tendencia-detalle'),
    ('editar_tendencia', 'editar-tendencia'),
    ('eliminar_tendencia', 'eliminar-tendencia'),
    ('crear_tendencia', 'crear-tendencia'),
    ('password_reset_request', 'password-reset-request'),
    ('password_reset_done', 'password-reset-done'),
    ('password_reset_complete', 'password-reset-complete'),
    ('password_reset_confirm', 'password-reset-confirm'),
    ('reactivar_cuenta', 'reactivar-cuenta'),
    ('asignar_colaboradores', 'asignar-colaboradores'),
    ('crear_subsistema', 'crear-subsistema'),
    ('eliminar_subsistema', 'eliminar-subsistema'),
]

# Template directory path
templates_dir = r'c:\Users\Guido\HAAPAR_UNLa.worktrees\agents-estandarizar-nombres-url-kebab-case\haapar_unla_app\templates'

files_modified = 0
total_replacements = 0
files_processed = []

# Walk through all HTML files
for root, dirs, files in os.walk(templates_dir):
    for filename in files:
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            
            try:
                # Read the file
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                replacements_in_file = 0
                
                # Apply all replacements
                for old_name, new_name in replacements:
                    # Replace in URL patterns: {% url 'name' %}, url('name'), reverse('name'), etc.
                    # This regex looks for the pattern in various Django template/URL contexts
                    pattern = r"(['\"])(" + re.escape(old_name) + r")(['\"])"
                    new_string = r"\1" + new_name + r"\3"
                    
                    modified_content, count = re.subn(pattern, new_string, content)
                    if count > 0:
                        replacements_in_file += count
                        total_replacements += count
                        content = modified_content
                
                # If changes were made, write back to file
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_modified += 1
                    files_processed.append((os.path.relpath(filepath, templates_dir), replacements_in_file))
            
            except Exception as e:
                print("Error processing {}: {}".format(filepath, e), file=sys.stderr)

# Report results
print("✓ Modified {} file(s) with total {} replacement(s) made".format(files_modified, total_replacements))
print()

if files_processed:
    print("Files modified:")
    for filepath, count in files_processed:
        print("  - {}: {} replacement(s)".format(filepath, count))
else:
    print("No files were modified (no matching patterns found)")

sys.exit(0)
