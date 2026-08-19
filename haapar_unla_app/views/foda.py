import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from haapar_unla_app.forms import VariablePESTELForm
from haapar_unla_app.models import (
    EvaluacionVariable,
    Historial,
    Influencia,
    Subsistema,
    Variable,
)


# ---------------------------------------------------------
# VISTA PRINCIPAL (FODA Y GRÁFICOS) con CACHE
# ---------------------------------------------------------
@login_required
def foda_graficos(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para ver este proyecto.")

    # Aumentamos la versión de la caché a v3 para forzar la actualización automática
    cache_key = f"foda_micmac_pestel_v3_{subsistema_id}"
    contexto = cache.get(cache_key)

    if contexto is None:
        variables_obj = (
            Variable.objects.filter(subsistema=subsistema, activo=True)
            .select_related(
                "subsistema", "subsistema__sistema", "subsistema__sistema__tema"
            )
            .prefetch_related("pestels")
            .order_by("pk")
        )

        nombres_vars = [
            v.nombre_corto if v.nombre_corto else v.nombre for v in variables_obj
        ]

        importancias = [int(v.promedio_importancia()) for v in variables_obj]
        incertidumbres = [int(v.promedio_incertidumbre()) for v in variables_obj]

        datos_dispersion = {
            "variables": nombres_vars,
            "importancia": importancias,
            "incertidumbre": incertidumbres,
        }

        n = len(variables_obj)
        matriz_valores = [[0] * n for _ in range(n)]
        var_index = {v.pk: i for i, v in enumerate(variables_obj)}

        influencias = Influencia.objects.filter(
            variable_origen__in=variables_obj, variable_destino__in=variables_obj
        ).select_related("variable_origen", "variable_destino")

        for inf in influencias:
            i = var_index[inf.variable_origen.pk]
            j = var_index[inf.variable_destino.pk]
            matriz_valores[i][j] = int(inf.valor)

        matriz_indirecta = {"variables": nombres_vars, "valores": matriz_valores}

        influencia_totales = [sum(fila) for fila in matriz_valores]
        dependencia_totales = [
            sum(matriz_valores[i][j] for i in range(n)) for j in range(n)
        ]

        datos_micmac = {
            "variables": nombres_vars,
            "influencia": influencia_totales,
            "dependencia": dependencia_totales,
        }

        # --- CLASIFICACIÓN MICMAC ---
        umbral_influencia = (
            sum(influencia_totales) / len(influencia_totales)
            if influencia_totales
            else 0
        )
        umbral_dependencia = (
            sum(dependencia_totales) / len(dependencia_totales)
            if dependencia_totales
            else 0
        )

        clasificacion = {}
        for idx, nombre in enumerate(nombres_vars):
            inf = influencia_totales[idx]
            dep = dependencia_totales[idx]

            if inf >= umbral_influencia and dep >= umbral_dependencia:
                categoria = "Clave"
            elif inf >= umbral_influencia and dep < umbral_dependencia:
                categoria = "Motora"
            elif inf < umbral_influencia and dep >= umbral_dependencia:
                categoria = "Dependiente"
            else:
                categoria = "Autónoma"

            clasificacion[nombre] = categoria

        # --- LÓGICA PESTEL ---
        variables_sin_pestel = []
        datos_pestel_nombres = {
            k: []
            for k in [
                "Político",
                "Económico",
                "Social",
                "Tecnológico",
                "Ecológico",
                "Legal",
            ]
        }
        tarjetas_pestel = {
            k: []
            for k in [
                "Político",
                "Económico",
                "Social",
                "Tecnológico",
                "Ecológico",
                "Legal",
            ]
        }

        for var in variables_obj:
            mis_pestels = var.pestels.all()
            if not mis_pestels:
                variables_sin_pestel.append(var)
            else:
                for pestel in mis_pestels:
                    categoria = pestel.get_tipo_display()
                    if categoria in datos_pestel_nombres:
                        datos_pestel_nombres[categoria].append(
                            var.nombre_corto or var.nombre[:15]
                        )
                        tarjetas_pestel[categoria].append(var)

        # --- CONTEXTO FINAL ---
        contexto = {
            "tema": tema,
            "subsistema": subsistema,
            "datos_dispersion": json.dumps(datos_dispersion),
            "variables": nombres_vars,
            "filas": zip(nombres_vars, matriz_valores),
            "matriz_indirecta": json.dumps(matriz_indirecta),
            "datos_micmac": json.dumps(datos_micmac),
            "datos_pestel": json.dumps(datos_pestel_nombres),
            "variables_sin_pestel": variables_sin_pestel,
            "tarjetas_pestel": tarjetas_pestel,
            "nombres_vars": nombres_vars,
            "influencia_totales": influencia_totales,
            "dependencia_totales": dependencia_totales,
            "clasificacion_variables": clasificacion,
            # Se añaden los umbrales para que el frontend dibuje las cruces correctas
            "umbral_influencia": umbral_influencia,
            "umbral_dependencia": umbral_dependencia,
        }

        cache.set(cache_key, contexto, timeout=3600)

    return render(request, "haapar_unla_app/foda-graficos.html", contexto)


# ---------------------------------------------------------
# ABM MANUAL DE LA MATRIZ MATEMÁTICA
# ---------------------------------------------------------
@login_required
def editar_matriz(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para editar este proyecto.")

    variables = list(
        Variable.objects.filter(subsistema=subsistema, activo=True)
        .select_related("subsistema")
        .order_by("pk")
    )

    evaluaciones = EvaluacionVariable.objects.filter(
        usuario=request.user, variable__in=variables
    ).select_related("variable")
    eval_map = {e.variable_id: e for e in evaluaciones}

    influencias = Influencia.objects.filter(
        variable_origen__in=variables, variable_destino__in=variables
    ).select_related("variable_origen", "variable_destino")
    inf_map = {(i.variable_origen_id, i.variable_destino_id): i for i in influencias}

    if request.method == "POST":

        for var in variables:
            imp_val = request.POST.get(f"imp_{var.pk}")
            inc_val = request.POST.get(f"inc_{var.pk}")

            if imp_val and inc_val:
                imp_val = int(imp_val)
                inc_val = int(inc_val)

                eval_obj = eval_map.get(var.pk)
                old_imp = eval_obj.importancia if eval_obj else "Vacío"
                old_inc = eval_obj.incertidumbre if eval_obj else "Vacío"

                if not eval_obj or old_imp != imp_val or old_inc != inc_val:
                    EvaluacionVariable.objects.update_or_create(
                        variable=var,
                        usuario=request.user,
                        defaults={"importancia": imp_val, "incertidumbre": inc_val},
                    )
                    Historial.objects.create(
                        variable=var,
                        usuario=request.user,
                        accion="EVALUACION",
                        detalles=f"Imp: {old_imp} ➔ {imp_val} | Inc: {old_inc} ➔ {inc_val}",
                    )

        for origen in variables:
            for destino in variables:
                if origen.pk != destino.pk:
                    inf_val = request.POST.get(f"inf_{origen.pk}_{destino.pk}")
                    if inf_val is not None:
                        inf_val = float(inf_val)
                        inf_obj = inf_map.get((origen.pk, destino.pk))
                        old_inf = float(inf_obj.valor) if inf_obj else "Vacío"

                        if not inf_obj or old_inf != inf_val:
                            Influencia.objects.update_or_create(
                                variable_origen=origen,
                                variable_destino=destino,
                                defaults={"valor": inf_val},
                            )
                            Historial.objects.create(
                                variable=origen,
                                usuario=request.user,
                                accion="MODIFICADO",
                                detalles=f"Influencia sobre '{destino.nombre_corto}': {old_inf} ➔ {int(inf_val)}",
                            )

        # Actualizado también acá
        cache.delete(f"foda_micmac_pestel_v3_{subsistema_id}")
        messages.success(
            request, "¡Valores actualizados! Los gráficos se recalcularon."
        )
        return redirect("foda-graficos", subsistema_id=subsistema_id)

    filas_tabla = []
    for origen in variables:
        eval_obj = eval_map.get(origen.pk)

        try:
            imp_clean = max(
                1,
                min(
                    10,
                    int(
                        round(
                            float(
                                eval_obj.importancia
                                if eval_obj
                                else (origen.promedio_importancia() or 1)
                            )
                        )
                    ),
                ),
            )
        except Exception:
            imp_clean = 1

        try:
            inc_clean = max(
                1,
                min(
                    10,
                    int(
                        round(
                            float(
                                eval_obj.incertidumbre
                                if eval_obj
                                else (origen.promedio_incertidumbre() or 1)
                            )
                        )
                    ),
                ),
            )
        except Exception:
            inc_clean = 1

        celdas = []
        for destino in variables:
            if origen.pk == destino.pk:
                celdas.append({"destino_id": destino.pk, "valor": "-", "is_self": True})
            else:
                inf_obj = inf_map.get((origen.pk, destino.pk))
                try:
                    inf_clean = max(
                        0, min(3, int(round(float(inf_obj.valor if inf_obj else 0))))
                    )
                except Exception:
                    inf_clean = 0
                celdas.append(
                    {"destino_id": destino.pk, "valor": inf_clean, "is_self": False}
                )

        filas_tabla.append(
            {"origen": origen, "imp": imp_clean, "inc": inc_clean, "celdas": celdas}
        )

    return render(
        request,
        "haapar_unla_app/editar-matriz.html",
        {
            "tema": tema,
            "subsistema": subsistema,
            "variables": variables,
            "filas_tabla": filas_tabla,
        },
    )


# ---------------------------------------------------------
# EDICIÓN DE PESTEL
# ---------------------------------------------------------
@login_required
def editar_pestel(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema = variable.subsistema
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para editar este proyecto.")

    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        form = VariablePESTELForm(request.POST, instance=variable)

        if form.is_valid():
            form.save()

            # Actualizado también acá
            cache.delete(f"foda_micmac_pestel_v3_{subsistema.id_subsistema}")
            messages.success(request, "PESTEL actualizado correctamente.")

            if next_url:
                return redirect(next_url)

            return redirect("variable_completa", variable_id=variable.id_variable)

    else:
        form = VariablePESTELForm(instance=variable)

    return render(
        request,
        "haapar_unla_app/editar-pestel.html",
        {
            "form": form,
            "variable": variable,
            "subsistema": subsistema,
            "tema": tema,
            "variable_completa_url": reverse(
                "variable_completa", kwargs={"variable_id": variable.id_variable}
            ),
        },
    )
