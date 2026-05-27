from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from haapar_unla_app.models import Variable
from haapar_unla_app.serializers import VariableSerializer
from haapar_unla_app.models import Historial, Subsistema, Variable


# ---------------------------
# VARIABLES
# ---------------------------
@login_required
def variable_detalle(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)

    # Ordenamos y paginamos las variables
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
            "page_obj": page_obj,  # Pasamos page_obj
            "tema": tema,
        },
    )


@login_required
def crear_variable(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    next_view = request.GET.get("next", "")

    if request.method == "POST":
        variable = Variable.objects.create(
            nombre=request.POST.get("nombre"),
            nombre_corto=request.POST.get("nombre_corto"),
            descripcion=request.POST.get("descripcion"),
            tipo=request.POST.get("tipo"),
            subsistema=subsistema,
        )
        Historial.objects.create(
            variable=variable, usuario=request.user, accion="AGREGADO"
        )

        next_post = request.POST.get("next", "")
        if next_post == "matriz":
            return redirect("editar-matriz", subsistema_id=subsistema_id)
        return redirect("variable-detalle", subsistema_id=subsistema_id)

    return render(
        request,
        "haapar_unla_app/crear-variable.html",
        {"subsistema": subsistema, "next": next_view},
    )


@login_required
def editar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema
    next_view = request.GET.get("next", "")

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

        next_post = request.POST.get("next", "")
        if next_post == "matriz":
            return redirect("editar-matriz", subsistema_id=subsistema_id)
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
    next_view = request.GET.get("next", "")

    variable.activo = False
    variable.save()

    Historial.objects.create(
        variable=variable, usuario=request.user, accion="ELIMINADO"
    )

    if next_view == "matriz":
        return redirect("editar-matriz", subsistema_id=subsistema_id)
    return redirect("variable-detalle", subsistema_id=subsistema_id)


@login_required
def historial_variables(request, subsistema_id):
    historial_list = (
        Historial.objects.select_related("variable", "usuario")
        .filter(variable__subsistema_id=subsistema_id)
        .order_by("-fecha")
    )

    # Paginación del historial: 15 registros por página
    paginator = Paginator(historial_list, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    from_view = request.GET.get("from", "")

    return render(
        request,
        "haapar_unla_app/historial-variable.html",
        {
            "page_obj": page_obj,
            "subsistema_id": subsistema_id,
            "from_view": from_view,
        },
    )
class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.filter(activo=True)
    serializer_class = VariableSerializer
    permission_classes = [IsAuthenticated]
