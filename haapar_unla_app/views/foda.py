import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from haapar_unla_app.models import (
    EvaluacionVariable,
    Historial,
    Influencia,
    Subsistema,
    Variable,
)


# ---------------------------------------------------------
# VISTA PRINCIPAL (FODA Y GRÁFICOS)
# ---------------------------------------------------------
@login_required
def foda_graficos(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para ver este proyecto.")

    variables_obj = (
        Variable.objects.filter(subsistema=subsistema, activo=True)
        .prefetch_related("pestels")
        .order_by("pk")
    )

    nombres_vars = [
        v.nombre_corto if v.nombre_corto else v.nombre[:15] for v in variables_obj
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
    )

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

    datos_pestel = {}

    for var in variables_obj:
        nombre_var = var.nombre_corto or var.nombre[:15]
        for pestel in var.pestels.all():
            categoria = pestel.get_tipo_display()
            if categoria not in datos_pestel:
                datos_pestel[categoria] = []
            datos_pestel[categoria].append(nombre_var)

    contexto = {
        "tema": tema,
        "subsistema": subsistema,
        "datos_dispersion": json.dumps(datos_dispersion),
        "variables": nombres_vars,
        "filas": zip(nombres_vars, matriz_valores),
        "matriz_indirecta": json.dumps(matriz_indirecta),
        "datos_micmac": json.dumps(datos_micmac),
        "datos_pestel": json.dumps(datos_pestel),
    }

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
        Variable.objects.filter(subsistema=subsistema, activo=True).order_by("pk")
    )

    if request.method == "POST":
        for var in variables:
            imp_val = request.POST.get(f"imp_{var.pk}")
            inc_val = request.POST.get(f"inc_{var.pk}")

            if imp_val and inc_val:
                imp_val = int(imp_val)
                inc_val = int(inc_val)

                eval_obj = EvaluacionVariable.objects.filter(
                    variable=var, usuario=request.user
                ).first()
                old_imp = eval_obj.importancia if eval_obj else "Vacío"
                old_inc = eval_obj.incertidumbre if eval_obj else "Vacío"

                if not eval_obj or old_imp != imp_val or old_inc != inc_val:
                    EvaluacionVariable.objects.update_or_create(
                        variable=var,
                        usuario=request.user,
                        defaults={"importancia": imp_val, "incertidumbre": inc_val},
                    )

                    texto_detalle = (
                        f"Imp: {old_imp} ➔ {imp_val} | Inc: {old_inc} ➔ {inc_val}"
                    )
                    Historial.objects.create(
                        variable=var,
                        usuario=request.user,
                        accion="EVALUACION",
                        detalles=texto_detalle,
                    )

        for origen in variables:
            for destino in variables:
                if origen.pk != destino.pk:
                    inf_val = request.POST.get(f"inf_{origen.pk}_{destino.pk}")
                    if inf_val is not None:
                        inf_val = float(inf_val)
                        inf_obj = Influencia.objects.filter(
                            variable_origen=origen, variable_destino=destino
                        ).first()
                        old_inf = float(inf_obj.valor) if inf_obj else "Vacío"

                        if not inf_obj or old_inf != inf_val:
                            Influencia.objects.update_or_create(
                                variable_origen=origen,
                                variable_destino=destino,
                                defaults={"valor": inf_val},
                            )
                            texto_detalle = f"Influencia sobre '{destino.nombre_corto}': {old_inf} ➔ {int(inf_val)}"
                            Historial.objects.create(
                                variable=origen,
                                usuario=request.user,
                                accion="MODIFICADO",
                                detalles=texto_detalle,
                            )

        messages.success(
            request, "¡Valores actualizados! Los gráficos se recalcularon."
        )
        return redirect("foda-graficos", subsistema_id=subsistema.id_subsistema)

    filas_tabla = []
    for origen in variables:
        eval_obj = EvaluacionVariable.objects.filter(
            variable=origen, usuario=request.user
        ).first()

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
                inf_obj = Influencia.objects.filter(
                    variable_origen=origen, variable_destino=destino
                ).first()
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
    
@login_required
def editar_pestel(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema = variable.subsistema
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para editar este proyecto.")

    if request.method == "POST":
        form = VariablePESTELForm(request.POST, instance=variable)
        if form.is_valid():
            form.save()
            messages.success(request, "PESTEL actualizado correctamente.")
            return redirect("foda-graficos", subsistema_id=subsistema.id_subsistema)
    else:
        form = VariablePESTELForm(instance=variable)

    return render(request, "haapar_unla_app/editar-pestel.html", {
        "form": form,
        "variable": variable,
        "subsistema": subsistema,
        "tema": tema,
    })