from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from haapar_unla_app.models import Sistema, Subsistema, Tema


# ---------------------------
# SUBSISTEMAS
# ---------------------------
@login_required
def subsistemas(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id, activo=True)

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para ver este proyecto.")

    sistemas = Sistema.objects.filter(tema=tema).prefetch_related(
        Prefetch("subsistema_set", queryset=Subsistema.objects.filter(activo=True))
    )
    return render(
        request,
        "haapar_unla_app/subsistemas.html",
        {"tema": tema, "sistemas": sistemas},
    )


@login_required
def crear_subsistema(request, tema_id):
    tema = get_object_or_404(Tema, pk=tema_id)
    sistema, _ = Sistema.objects.get_or_create(
        tema=tema,
        defaults={
            "nombre": f"Sistema de {tema.nombre}",
            "descripcion": "Sistema generado automáticamente",
        },
    )
    if request.method == "POST":
        Subsistema.objects.create(
            sistema=sistema,
            nombre=request.POST.get("nombre"),
            descripcion=request.POST.get("descripcion"),
            activo=True,
        )
        return redirect("subsistemas", tema_id=tema.id_tema)
    return render(request, "haapar_unla_app/crear-subsistema.html", {"tema": tema})


@login_required
def eliminar_subsistema(request, sub_id):
    sub = get_object_or_404(
        Subsistema, id_subsistema=sub_id, sistema__tema__user=request.user
    )
    if request.method == "POST":
        sub.activo = False
        sub.save()
    return redirect("subsistemas", tema_id=sub.sistema.tema.id_tema)
