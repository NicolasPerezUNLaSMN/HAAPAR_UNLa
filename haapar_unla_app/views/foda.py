import json
import statistics

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from haapar_unla_app.forms import VariablePESTELForm
from haapar_unla_app.models import (
    ActorClave,
    EscenarioSchwartz,
    EvaluacionTendencia,
    EvaluacionVariable,
    Historial,
    Influencia,
    InfluenciaActor,
    Subsistema,
    TendenciaExterna,
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

    cache_key = f"foda_micmac_pestel_v10_{subsistema_id}"
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

        tendencias_obj = TendenciaExterna.objects.filter(
            subsistema=subsistema, activo=True
        ).order_by("pk")

        nombres_vars = [
            v.nombre_corto if v.nombre_corto else v.nombre for v in variables_obj
        ]

        # 1. DISPERSIÓN (Variables + Tendencias)
        elementos_dispersion = []
        importancias_globales = []
        incertidumbres_globales = []

        for v in variables_obj:
            imp = float(v.promedio_importancia() or 5.0)
            inc = float(v.promedio_incertidumbre() or 5.0)
            elementos_dispersion.append(
                {
                    "nombre": v.nombre_corto or v.nombre,
                    "imp": imp,
                    "inc": inc,
                    "tipo": "Variable",
                }
            )
            importancias_globales.append(imp)
            incertidumbres_globales.append(inc)

        for t in tendencias_obj:
            imp = float(t.promedio_importancia() or 5.0)
            inc = float(t.promedio_incertidumbre() or 5.0)
            elementos_dispersion.append(
                {
                    "nombre": t.nombre_corto or t.nombre,
                    "imp": imp,
                    "inc": inc,
                    "tipo": "Tendencia",
                }
            )
            importancias_globales.append(imp)
            incertidumbres_globales.append(inc)

        mediana_imp = (
            statistics.median(importancias_globales) if importancias_globales else 5.0
        )
        mediana_inc = (
            statistics.median(incertidumbres_globales)
            if incertidumbres_globales
            else 5.0
        )

        datos_dispersion = {
            "elementos": elementos_dispersion,
            "mediana_imp": mediana_imp,
            "mediana_inc": mediana_inc,
        }

        # --- FODA AUTOMÁTICO ---
        fortalezas, debilidades, oportunidades, amenazas = [], [], [], []
        for var in variables_obj:
            imp_val = float(var.promedio_importancia() or 5.0)
            if var.tipo == "I":
                (
                    fortalezas.append(var)
                    if imp_val >= mediana_imp
                    else debilidades.append(var)
                )
            else:
                (
                    oportunidades.append(var)
                    if imp_val >= mediana_imp
                    else amenazas.append(var)
                )

        for t in tendencias_obj:
            imp_val = float(t.promedio_importancia() or 5.0)
            oportunidades.append(t) if imp_val >= mediana_imp else amenazas.append(t)

        # --- MICMAC (DIRECTO e INDIRECTO MATEMÁTICO) ---
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

        matriz_indirecta_heatmap = {
            "variables": nombres_vars,
            "valores": matriz_valores,
        }

        # 1. Totales Directos
        influencia_totales = [sum(fila) for fila in matriz_valores]
        dependencia_totales = [
            sum(matriz_valores[i][j] for i in range(n)) for j in range(n)
        ]

        datos_micmac = {
            "variables": nombres_vars,
            "influencia": influencia_totales,
            "dependencia": dependencia_totales,
        }

        # 2. Totales Indirectos (Cálculo matemático M + M^2)
        if n > 0:
            # Multiplicación de matrices M * M
            m2 = [
                [
                    sum(matriz_valores[i][k] * matriz_valores[k][j] for k in range(n))
                    for j in range(n)
                ]
                for i in range(n)
            ]
            # Matriz indirecta combinada M + M^2
            m_ind = [
                [matriz_valores[i][j] + m2[i][j] for j in range(n)] for i in range(n)
            ]
            influencia_ind_totales = [sum(fila) for fila in m_ind]
            dependencia_ind_totales = [
                sum(m_ind[i][j] for i in range(n)) for j in range(n)
            ]
        else:
            influencia_ind_totales, dependencia_ind_totales = [], []

        datos_micmac_indirecto = {
            "variables": nombres_vars,
            "influencia": influencia_ind_totales,
            "dependencia": dependencia_ind_totales,
        }

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
            inf, dep = influencia_totales[idx], dependencia_totales[idx]
            if inf >= umbral_influencia and dep >= umbral_dependencia:
                categoria = "Clave"
            elif inf >= umbral_influencia and dep < umbral_dependencia:
                categoria = "Motora"
            elif inf < umbral_influencia and dep >= umbral_dependencia:
                categoria = "Dependiente"
            else:
                categoria = "Autónoma"
            clasificacion[nombre] = categoria

        # --- PESTEL ---
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
                    cat = pestel.get_tipo_display()
                    if cat in datos_pestel_nombres:
                        datos_pestel_nombres[cat].append(
                            var.nombre_corto or var.nombre[:15]
                        )
                        tarjetas_pestel[cat].append(var)

        # --- MACTOR (Poder de Actores) ---
        actores_obj = list(
            ActorClave.objects.filter(subsistema=subsistema, activo=True).order_by("pk")
        )
        nombres_actores = [a.nombre for a in actores_obj]
        n_act = len(actores_obj)
        matriz_actores = [[0] * n_act for _ in range(n_act)]
        act_index = {a.pk: i for i, a in enumerate(actores_obj)}

        influencias_actores = InfluenciaActor.objects.filter(
            actor_origen__in=actores_obj, actor_destino__in=actores_obj
        ).select_related("actor_origen", "actor_destino")

        for inf in influencias_actores:
            matriz_actores[act_index[inf.actor_origen.pk]][
                act_index[inf.actor_destino.pk]
            ] = int(inf.valor)

        influencia_act = [sum(fila) for fila in matriz_actores]
        dependencia_act = [
            sum(matriz_actores[i][j] for i in range(n_act)) for j in range(n_act)
        ]

        datos_mactor = {
            "actores": nombres_actores,
            "influencia": influencia_act,
            "dependencia": dependencia_act,
            "matriz": matriz_actores,
        }

        # --- ESCENARIOS PETER SCHWARTZ Y NOMBRES DINÁMICOS ---
        escenarios_schwartz = list(
            EscenarioSchwartz.objects.filter(subsistema=subsistema)
        )

        puntajes_schwartz = []
        for idx, var in enumerate(variables_obj):
            imp = float(var.promedio_importancia() or 5.0)
            inc = float(var.promedio_incertidumbre() or 5.0)
            inf = influencia_totales[idx]
            dep = dependencia_totales[idx]
            puntajes_schwartz.append(
                (imp + inc + inf + dep, var.nombre_corto or var.nombre)
            )

        puntajes_schwartz.sort(key=lambda x: x[0], reverse=True)
        eje_x_schwartz = (
            puntajes_schwartz[0][1] if len(puntajes_schwartz) > 0 else "Eje Crítico 1"
        )
        eje_y_schwartz = (
            puntajes_schwartz[1][1] if len(puntajes_schwartz) > 1 else "Eje Crítico 2"
        )

        nombres_escenarios = {}
        for esc in escenarios_schwartz:
            nombres_escenarios[esc.cuadrante] = esc.nombre_marketinero

        # --- CONTEXTO FINAL ---
        contexto = {
            "tema": tema,
            "subsistema": subsistema,
            "datos_dispersion": json.dumps(datos_dispersion),
            "variables": nombres_vars,
            "filas": zip(nombres_vars, matriz_valores),
            "matriz_indirecta": json.dumps(matriz_indirecta_heatmap),
            "datos_micmac": json.dumps(datos_micmac),
            "datos_micmac_indirecto": json.dumps(datos_micmac_indirecto),  # NUEVO
            "datos_mactor": json.dumps(datos_mactor),
            "escenarios_schwartz": escenarios_schwartz,
            "eje_x_schwartz": eje_x_schwartz,
            "eje_y_schwartz": eje_y_schwartz,
            "nombres_escenarios": json.dumps(nombres_escenarios),
            "datos_pestel": json.dumps(datos_pestel_nombres),
            "variables_sin_pestel": variables_sin_pestel,
            "tarjetas_pestel": tarjetas_pestel,
            "nombres_vars": nombres_vars,
            "influencia_totales": influencia_totales,
            "dependencia_totales": dependencia_totales,
            "clasificacion_variables": clasificacion,
            "umbral_influencia": umbral_influencia,
            "umbral_dependencia": umbral_dependencia,
            "fortalezas": fortalezas,
            "debilidades": debilidades,
            "oportunidades": oportunidades,
            "amenazas": amenazas,
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

    tendencias = list(
        TendenciaExterna.objects.filter(subsistema=subsistema, activo=True).order_by(
            "pk"
        )
    )
    evaluaciones_tendencias = EvaluacionTendencia.objects.filter(
        usuario=request.user, tendencia__in=tendencias
    ).select_related("tendencia")
    eval_tend_map = {e.tendencia_id: e for e in evaluaciones_tendencias}

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

        for tend in tendencias:
            t_imp_val = request.POST.get(f"tend_imp_{tend.pk}")
            t_inc_val = request.POST.get(f"tend_inc_{tend.pk}")

            if t_imp_val and t_inc_val:
                t_imp_val = int(t_imp_val)
                t_inc_val = int(t_inc_val)
                t_eval_obj = eval_tend_map.get(tend.pk)
                t_old_imp = t_eval_obj.importancia if t_eval_obj else "Vacío"
                t_old_inc = t_eval_obj.incertidumbre if t_eval_obj else "Vacío"

                if not t_eval_obj or t_old_imp != t_imp_val or t_old_inc != t_inc_val:
                    EvaluacionTendencia.objects.update_or_create(
                        tendencia=tend,
                        usuario=request.user,
                        defaults={"importancia": t_imp_val, "incertidumbre": t_inc_val},
                    )
                    Historial.objects.create(
                        tendencia=tend,
                        usuario=request.user,
                        accion="EVALUACION",
                        detalles=f"Imp Tendencia: {t_old_imp} ➔ {t_imp_val} | Inc: {t_old_inc} ➔ {t_inc_val}",
                    )

        cache.delete(f"foda_micmac_pestel_v10_{subsistema_id}")
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

    filas_tendencias = []
    for tend in tendencias:
        t_eval_obj = eval_tend_map.get(tend.pk)
        try:
            t_imp_clean = max(
                1,
                min(
                    10,
                    int(
                        round(
                            float(
                                t_eval_obj.importancia
                                if t_eval_obj
                                else (tend.promedio_importancia() or 1)
                            )
                        )
                    ),
                ),
            )
        except Exception:
            t_imp_clean = 1
        try:
            t_inc_clean = max(
                1,
                min(
                    10,
                    int(
                        round(
                            float(
                                t_eval_obj.incertidumbre
                                if t_eval_obj
                                else (tend.promedio_incertidumbre() or 1)
                            )
                        )
                    ),
                ),
            )
        except Exception:
            t_inc_clean = 1

        filas_tendencias.append(
            {"tendencia": tend, "imp": t_imp_clean, "inc": t_inc_clean}
        )

    return render(
        request,
        "haapar_unla_app/editar-matriz.html",
        {
            "tema": tema,
            "subsistema": subsistema,
            "variables": variables,
            "filas_tabla": filas_tabla,
            "filas_tendencias": filas_tendencias,
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
            cache.delete(f"foda_micmac_pestel_v10_{subsistema.id_subsistema}")
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
