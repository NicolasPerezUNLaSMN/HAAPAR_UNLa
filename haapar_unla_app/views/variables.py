from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Func
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from haapar_unla_app.models import (
    PESTEL,
    EvaluacionVariable,
    Historial,
    IndicadorVariable,
    Subsistema,
    TendenciaExterna,
    Variable,
    VariableTendencia,
)
from haapar_unla_app.serializers import VariableSerializer
from haapar_unla_app.services.ia_service import calcular_impacto_variable_tendencia


# ---------------------------
# VARIABLES
# ---------------------------
@login_required
def variable_detalle(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)

    variables_list = Variable.objects.filter(
        subsistema=subsistema, activo=True
    ).order_by("-id_variable")
    paginator = Paginator(variables_list, 5)  # 5 variables por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    tema = subsistema.sistema.tema
    return render(
        request,
        "haapar_unla_app/variable-detalle.html",
        {
            "subsistema": subsistema,
            "page_obj": page_obj,
            "tema": tema,
        },
    )


@login_required
def crear_variable(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)

    pestels = PESTEL.objects.all()
    tendencias = TendenciaExterna.objects.filter(subsistema=subsistema, activo=True)

    next_view = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        variable = Variable.objects.create(
            nombre=request.POST.get("nombre"),
            nombre_corto=request.POST.get("nombre_corto"),
            descripcion=request.POST.get("descripcion"),
            tipo=request.POST.get("tipo"),
            subsistema=subsistema,
        )

        pestel_ids = request.POST.getlist("pestel")
        for p in pestel_ids:
            pestel_obj = PESTEL.objects.filter(tipo=p).first()
            if pestel_obj:
                variable.pestels.add(pestel_obj)

        nombre_ind = request.POST.get("indicador_nombre")
        desc_ind = request.POST.get("indicador_desc")
        formula_ind = request.POST.get("indicador_formula")

        if nombre_ind:
            IndicadorVariable.objects.create(
                variable=variable,
                nombre_corto=nombre_ind,
                descripcion=desc_ind,
                formula=formula_ind,
            )

        tendencias_ids = request.POST.getlist("tendencias")
        for tid in tendencias_ids:
            tendencia = TendenciaExterna.objects.filter(
                id_tendencia_externa=tid
            ).first()

            if tendencia:
                VariableTendencia.objects.create(
                    variable=variable,
                    tendencia=tendencia,
                    impacto=0,
                )

        Historial.objects.create(
            variable=variable,
            usuario=request.user,
            accion="AGREGADO",
        )

        # Caché V10
        cache.delete(f"foda_micmac_pestel_v10_{subsistema_id}")

        if next_view == "matriz":
            return redirect("editar-matriz", subsistema_id=subsistema_id)
        elif next_view == "pestel":
            url = reverse("foda-graficos", kwargs={"subsistema_id": subsistema_id})
            return redirect(f"{url}#gestion-pestel")

        return redirect("variable-detalle", subsistema_id=subsistema.id_subsistema)

    return render(
        request,
        "haapar_unla_app/crear-variable.html",
        {
            "subsistema": subsistema,
            "pestels": pestels,
            "tendencias": tendencias,
            "next": next_view,
        },
    )


@login_required
def editar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema
    next_view = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        old_nombre = variable.nombre
        old_nombre_corto = variable.nombre_corto
        new_nombre = request.POST.get("nombre")
        new_nombre_corto = request.POST.get("nombre_corto")

        variable.nombre = new_nombre
        variable.nombre_corto = new_nombre_corto
        variable.descripcion = request.POST.get("descripcion")
        variable.tipo = request.POST.get("tipo")
        variable.save()

        cambios = []
        if old_nombre != new_nombre:
            cambios.append(f"Nombre: '{old_nombre}' ➔ '{new_nombre}'")
        if old_nombre_corto != new_nombre_corto:
            cambios.append(f"Corto: '{old_nombre_corto}' ➔ '{new_nombre_corto}'")

        texto_detalle = (
            " | ".join(cambios) if cambios else "Modificación de descripción/tipo"
        )

        Historial.objects.create(
            variable=variable,
            usuario=request.user,
            accion="MODIFICADO",
            detalles=texto_detalle,
        )

        # Caché V10
        cache.delete(f"foda_micmac_pestel_v10_{subsistema_id}")

        if next_view == "matriz":
            return redirect("editar-matriz", subsistema_id=subsistema_id)
        elif next_view == "pestel":
            url = reverse("foda-graficos", kwargs={"subsistema_id": subsistema_id})
            return redirect(f"{url}#gestion-pestel")

        return redirect("variable-detalle", subsistema_id=subsistema_id)

    return render(
        request,
        "haapar_unla_app/editar-variable.html",
        {"variable": variable, "subsistema_id": subsistema_id, "next": next_view},
    )


@login_required
@require_POST
def eliminar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema
    next_view = request.GET.get("next") or request.POST.get("next")

    variable.activo = False
    variable.save()

    Historial.objects.create(
        variable=variable, usuario=request.user, accion="ELIMINADO"
    )

    # Caché V10
    cache.delete(f"foda_micmac_pestel_v10_{subsistema_id}")

    if next_view == "matriz":
        return redirect("editar-matriz", subsistema_id=subsistema_id)
    elif next_view == "pestel":
        url = reverse("foda-graficos", kwargs={"subsistema_id": subsistema_id})
        return redirect(f"{url}#gestion-pestel")

    return redirect("variable-detalle", subsistema_id=subsistema_id)


@login_required
def variable_completa(request, variable_id):
    variable = get_object_or_404(Variable, pk=variable_id, activo=True)
    indicadores = IndicadorVariable.objects.filter(variable=variable)
    relaciones = VariableTendencia.objects.filter(variable=variable).select_related(
        "tendencia"
    )
    todas_tendencias = TendenciaExterna.objects.filter(
        subsistema=variable.subsistema, activo=True
    )
    tendencias_seleccionadas = list(
        VariableTendencia.objects.filter(variable=variable).values_list(
            "tendencia_id", flat=True
        )
    )
    pestels = variable.pestels.all()
    evaluaciones = (
        EvaluacionVariable.objects.filter(variable=variable)
        .select_related("usuario")
        .order_by("-fecha")
    )
    mi_evaluacion = evaluaciones.filter(usuario=request.user).first()

    return render(
        request,
        "haapar_unla_app/variable-completa.html",
        {
            "variable": variable,
            "indicadores": indicadores,
            "relaciones": relaciones,
            "pestels": pestels,
            "todas_tendencias": todas_tendencias,
            "tendencias_seleccionadas": tendencias_seleccionadas,
            "evaluaciones": evaluaciones,
            "mi_evaluacion": mi_evaluacion,
        },
    )


@login_required
def crear_indicador(request, variable_id):
    variable = get_object_or_404(Variable, pk=variable_id)

    if request.method == "POST":
        IndicadorVariable.objects.create(
            variable=variable,
            nombre_corto=request.POST.get("nombre_corto"),
            descripcion=request.POST.get("descripcion"),
            formula=request.POST.get("formula"),
        )

    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER"))


@login_required
def editar_indicador(request, pk):
    indicador = get_object_or_404(IndicadorVariable, pk=pk)

    if request.method == "POST":
        indicador.nombre_corto = request.POST.get("nombre_corto")
        indicador.descripcion = request.POST.get("descripcion")
        indicador.formula = request.POST.get("formula")
        indicador.save()

        return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER"))

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def eliminar_indicador(request, pk):
    indicador = get_object_or_404(IndicadorVariable, pk=pk)

    if request.method == "POST":
        indicador.delete()

    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER"))


@login_required
def historial_variables(request, subsistema_id):

    historial = Historial.objects.filter(
        variable__subsistema_id=subsistema_id
    ).select_related("variable", "usuario")

    busqueda = request.GET.get("q", "").strip()
    accion = request.GET.get("accion", "").strip()

    if busqueda:
        historial = historial.annotate(
            variable_sin_acentos=Func("variable__nombre", function="unaccent")
        ).filter(variable_sin_acentos__icontains=busqueda)

    if accion:
        historial = historial.filter(accion=accion)

    historial = historial.order_by("-fecha")

    paginator = Paginator(historial, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "haapar_unla_app/historial-variable.html",
        {
            "page_obj": page_obj,
            "subsistema_id": subsistema_id,
            "busqueda": busqueda,
            "accion_seleccionada": accion,
        },
    )


@login_required
def editar_tendencias_variable(request, pk):

    variable = get_object_or_404(Variable, pk=pk, activo=True)

    if request.method == "POST":

        ids_seleccionados = set(map(int, request.POST.getlist("tendencias")))
        relaciones_actuales = VariableTendencia.objects.filter(variable=variable)
        ids_actuales = set(relaciones_actuales.values_list("tendencia_id", flat=True))

        VariableTendencia.objects.filter(
            variable=variable, tendencia_id__in=(ids_actuales - ids_seleccionados)
        ).delete()

        nuevas = ids_seleccionados - ids_actuales

        for tendencia_id in nuevas:
            tendencia = TendenciaExterna.objects.get(pk=tendencia_id)
            impacto = calcular_impacto_variable_tendencia(variable, tendencia)
            VariableTendencia.objects.create(
                variable=variable, tendencia=tendencia, impacto=impacto
            )

        messages.success(request, "Tendencias actualizadas correctamente.")
        return redirect("variable_completa", variable_id=variable.id_variable)

    tendencias = TendenciaExterna.objects.filter(
        subsistema=variable.subsistema, activo=True
    )
    tendencias_actuales = VariableTendencia.objects.filter(
        variable=variable
    ).values_list("tendencia_id", flat=True)

    return render(
        request,
        "haapar_unla_app/editar-tendencias-variable.html",
        {
            "variable": variable,
            "tendencias": tendencias,
            "tendencias_actuales": tendencias_actuales,
        },
    )


@login_required
@require_POST
def eliminar_evaluacion(request, variable_id):

    variable = get_object_or_404(Variable, pk=variable_id, activo=True)

    EvaluacionVariable.objects.filter(variable=variable, usuario=request.user).delete()

    # Caché V10
    cache.delete(f"foda_micmac_pestel_v10_{variable.subsistema.id_subsistema}")

    messages.success(request, "Tu evaluación fue eliminada correctamente.")

    return redirect("variable_completa", variable_id=variable.id_variable)


@login_required
@require_POST
def evaluar_variable(request, variable_id):

    variable = get_object_or_404(Variable, pk=variable_id, activo=True)

    try:
        importancia = int(request.POST.get("importancia"))
        incertidumbre = int(request.POST.get("incertidumbre"))
    except (TypeError, ValueError):
        messages.error(
            request, "Los valores de importancia e incertidumbre no son válidos."
        )
        return redirect("variable_completa", variable_id=variable.id_variable)

    if not 1 <= importancia <= 10 or not 1 <= incertidumbre <= 10:
        messages.error(request, "Los valores deben estar entre 1 y 10.")
        return redirect("variable_completa", variable_id=variable.id_variable)

    EvaluacionVariable.objects.update_or_create(
        variable=variable,
        usuario=request.user,
        defaults={
            "importancia": importancia,
            "incertidumbre": incertidumbre,
        },
    )

    # Caché V10
    cache.delete(f"foda_micmac_pestel_v10_{variable.subsistema.id_subsistema}")

    return redirect("variable_completa", variable_id=variable.id_variable)


class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.filter(activo=True)
    serializer_class = VariableSerializer
    permission_classes = [IsAuthenticated]
