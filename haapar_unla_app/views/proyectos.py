from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from haapar_unla_app.models import Tema
from haapar_unla_app.serializers import TemaSerializer
from haapar_unla_app.models import Subsistema, Tema, Variable
from haapar_unla_app.services.ia_service import (
    generar_estructura_prospectiva,
    generar_evaluaciones_e_influencias,
)


# ---------------------------
# INICIO
# ---------------------------
def inicio(request):
    return render(request, "haapar_unla_app/crear-reporte.html")


# ---------------------------
# PROYECTOS
# ---------------------------
@login_required
def crear_reporte(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        horizonte = request.POST.get("horizonte")
        territorio = request.POST.get("territorio")

        tema = Tema.objects.create(
            user=request.user,
            nombre=nombre,
            descripcion=descripcion,
            horizonte=horizonte,
            territorio=territorio,
        )

        generar_estructura_prospectiva(tema)
        generar_evaluaciones_e_influencias(tema, request.user)
        return redirect("subsistemas", tema_id=tema.id_tema)


@login_required
def listar_proyectos(request):
    propios = Tema.objects.filter(user=request.user, activo=True)
    colaborando = Tema.objects.filter(colaboradores=request.user, activo=True)

    # 🔎 Optimización: precargar user y colaboradores con grupos
    temas = (
        (propios | colaborando)
        .distinct()
        .select_related("user")                       # carga el creador en la misma query
        .prefetch_related("colaboradores__groups")    # carga colaboradores y sus grupos
        .order_by("-id_tema")
    )

    paginator = Paginator(temas, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request, "haapar_unla_app/listar-proyectos.html", {"page_obj": page_obj}
    )


@login_required
def proyecto_detalle(request, tema_id, subsistema_id=None):
    # 🔎 Optimización: precargar user y colaboradores con grupos
    tema = (
        Tema.objects.select_related("user")
        .prefetch_related("colaboradores__groups")
        .get(pk=tema_id, activo=True)
    )

    subsistema, subsistemas, variables = None, None, []

    if subsistema_id:
        # 🔎 Optimización: precargar sistema y tema
        subsistema = Subsistema.objects.select_related("sistema", "sistema__tema").get(
            pk=subsistema_id, activo=True
        )
        # 🔎 Optimización: precargar subsistema en variables
        variables = Variable.objects.filter(subsistema=subsistema, activo=True).select_related("subsistema")
    else:
        subsistemas = Subsistema.objects.filter(sistema__tema=tema, activo=True).select_related("sistema")

    return render(
        request,
        "haapar_unla_app/proyecto-detalle.html",
        {
            "tema": tema,
            "subsistema": subsistema,
            "subsistemas": subsistemas,
            "variables": variables,
        },
    )


@login_required
def eliminar_proyecto(request, id_tema):
    tema = get_object_or_404(Tema, id_tema=id_tema, user=request.user)
    if request.method == "POST":
        tema.activo = False
        tema.save()
        return redirect("listar-proyectos")
    return render(
        request, "haapar_unla_app/eliminar-proyecto-confirmacion.html", {"tema": tema}
    )


@login_required
def asignar_colaboradores(request, tema_id):
    tema = get_object_or_404(Tema, pk=tema_id)
    es_creador = request.user == tema.user

    if request.method == "POST" and es_creador:
        colaboradores_ids = request.POST.getlist("colaboradores")
        colaboradores = User.objects.filter(id__in=colaboradores_ids)
        tema.colaboradores.set(colaboradores)

        grupo_colaborador, _ = Group.objects.get_or_create(name="colaborador")
        for u in colaboradores:
            u.groups.add(grupo_colaborador)

        return redirect("listar-proyectos")

    return render(
        request,
        "haapar_unla_app/asignar_colaboradores.html",
        {
            "tema": tema,
            "usuarios": User.objects.exclude(id=tema.user.id),
            "es_creador": es_creador,
        },
    )
class TemaViewSet(viewsets.ModelViewSet):
    queryset = Tema.objects.filter(activo=True)
    serializer_class = TemaSerializer
    permission_classes = [IsAuthenticated]