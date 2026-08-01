from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Func, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from haapar_unla_app.models import Historial, Subsistema, TendenciaExterna


# ---------------------------
# TENDENCIAS
# ---------------------------
@login_required
def listar_tendencias(request):
    tendencias_por_subsistema = Subsistema.objects.annotate(
        num_tendencias=Count(
            "tendenciaexterna", filter=Q(tendenciaexterna__activo=True), distinct=True
        )
    ).filter(num_tendencias__gt=0)

    todas_las_tendencias = TendenciaExterna.objects.filter(activo=True).order_by(
        "-id_tendencia_externa"
    )

    paginator = Paginator(todas_las_tendencias, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "haapar_unla_app/tendencias.html",
        {
            "tendencias_por_subsistema": tendencias_por_subsistema,
            "page_obj": page_obj,
        },
    )


@login_required
def tendencia_detalle(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id, activo=True)
    tema = subsistema.sistema.tema

    # Ordenamos y paginamos las tendencias de este subsistema específico
    tendencias_list = TendenciaExterna.objects.filter(
        subsistema=subsistema, activo=True
    ).order_by("-id_tendencia_externa")

    paginator = Paginator(tendencias_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "haapar_unla_app/tendencia-detalle.html",
        {
            "tema": tema,
            "subsistema": subsistema,
            "page_obj": page_obj,  # Pasamos page_obj en lugar de la lista completa
        },
    )


@login_required
def crear_tendencia(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        nombre_corto = request.POST.get("nombre_corto")
        tipo_dato = request.POST.get("tipo_dato")
        descripcion = request.POST.get("descripcion")

        tendencia = TendenciaExterna.objects.create(
            subsistema=subsistema,
            nombre=nombre,
            nombre_corto=nombre_corto,
            tipo_dato=tipo_dato,
            descripcion=descripcion,
            activo=True,
        )

        Historial.objects.create(
            tendencia=tendencia,
            usuario=request.user,
            accion="CREADO",
        )

        return redirect("tendencia-detalle", subsistema_id=subsistema.id_subsistema)

    return render(
        request,
        "haapar_unla_app/crear-tendencia.html",
        {
            "subsistema": subsistema,
        },
    )


@login_required
def editar_tendencia(request, pk):
    tendencia = get_object_or_404(TendenciaExterna, pk=pk, activo=True)
    subsistema = tendencia.subsistema

    if request.method == "POST":

        old_nombre = tendencia.nombre
        old_nombre_corto = tendencia.nombre_corto

        new_nombre = request.POST.get("nombre")
        new_nombre_corto = request.POST.get("nombre_corto")

        tendencia.nombre = new_nombre
        tendencia.nombre_corto = new_nombre_corto
        tendencia.tipo_dato = request.POST.get("tipo_dato")
        tendencia.descripcion = request.POST.get("descripcion")
        tendencia.save()

        cambios = []

        if old_nombre != new_nombre:
            cambios.append(f"Nombre: '{old_nombre}' ➔ '{new_nombre}'")

        if old_nombre_corto != new_nombre_corto:
            cambios.append(f"Corto: '{old_nombre_corto}' ➔ '{new_nombre_corto}'")

        texto_detalle = (
            " | ".join(cambios)
            if cambios
            else "Modificación de descripción/tipo de dato"
        )

        Historial.objects.create(
            tendencia=tendencia,
            usuario=request.user,
            accion="MODIFICADO",
            detalles=texto_detalle,
        )

        return redirect("tendencia-detalle", subsistema_id=subsistema.id_subsistema)

    return render(
        request,
        "haapar_unla_app/editar-tendencia.html",
        {
            "tendencia": tendencia,
            "subsistema": subsistema,
        },
    )


@login_required
@require_POST
def eliminar_tendencia(request, pk):
    tendencia = get_object_or_404(TendenciaExterna, pk=pk, activo=True)

    subsistema_id = tendencia.subsistema.id_subsistema

    tendencia.activo = False
    tendencia.save()

    Historial.objects.create(
        tendencia=tendencia,
        usuario=request.user,
        accion="ELIMINADO",
    )

    return redirect("tendencia-detalle", subsistema_id=subsistema_id)


@login_required
def historial_tendencias(request, subsistema_id):

    historial = (
        Historial.objects.filter(tendencia__subsistema_id=subsistema_id)
        .select_related("tendencia", "usuario")
        .order_by("-fecha")
    )

    busqueda = request.GET.get("q", "").strip()

    if busqueda:
        historial = historial.annotate(
            tendencia_sin_acentos=Func("tendencia__nombre", function="unaccent")
        ).filter(tendencia_sin_acentos__icontains=busqueda)

    accion = request.GET.get("accion", "").strip()

    if accion:
        historial = historial.filter(accion=accion)

    paginator = Paginator(historial, 15)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "haapar_unla_app/historial-tendencias.html",
        {
            "page_obj": page_obj,
            "subsistema_id": subsistema_id,
            "busqueda": busqueda,
            "accion_seleccionada": accion,
        },
    )
