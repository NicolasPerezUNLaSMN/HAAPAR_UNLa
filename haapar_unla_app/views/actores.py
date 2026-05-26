from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from haapar_unla_app.models import ActorClave, RelacionActor, Subsistema


# ---------------------------
# ACTORES
# ---------------------------
@login_required
def actor_detalle(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

    # Ordenamos y paginamos los actores
    actores_list = ActorClave.objects.filter(
        subsistema=subsistema, activo=True
    ).order_by("-pk")
    paginator = Paginator(actores_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    tema = subsistema.sistema.tema

    return render(
        request,
        "haapar_unla_app/actor-detalle.html",
        {
            "subsistema": subsistema,
            "page_obj": page_obj,  # Pasamos page_obj en lugar de la lista cruda
            "tema": tema,
        },
    )


@login_required
def crear_actor(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        puesto = request.POST.get("puesto")
        actor = ActorClave.objects.create(
            subsistema=subsistema,
            nombre=nombre,
            descripcion=descripcion,
            puesto=puesto,
            activo=True,
        )

        influencia = request.POST.get("influencia")
        if influencia:
            RelacionActor.objects.create(
                actor_clave=actor, subsistema=subsistema, influencia=influencia
            )
        return redirect("actor-detalle", subsistema_id=subsistema.id_subsistema)

    return render(
        request, "haapar_unla_app/crear-actor.html", {"subsistema": subsistema}
    )


@login_required
def editar_actor(request, pk):
    actor = get_object_or_404(ActorClave, pk=pk)
    subsistema = actor.subsistema

    if request.method == "POST":
        actor.nombre = request.POST.get("nombre", actor.nombre)
        actor.descripcion = request.POST.get("descripcion", actor.descripcion)
        actor.puesto = request.POST.get("puesto", actor.puesto)
        actor.save()

        influencia = request.POST.get("influencia")
        if influencia:
            relacion, created = RelacionActor.objects.get_or_create(
                actor_clave=actor,
                subsistema=subsistema,
                defaults={"influencia": influencia},
            )
            if not created:
                relacion.influencia = influencia
                relacion.save()

        return redirect("actor-detalle", subsistema_id=subsistema.id_subsistema)

    try:
        relacion = RelacionActor.objects.get(actor_clave=actor, subsistema=subsistema)
        influencia = relacion.influencia
    except RelacionActor.DoesNotExist:
        influencia = None

    return render(
        request,
        "haapar_unla_app/editar-actor.html",
        {"actor": actor, "influencia": influencia, "subsistema": subsistema},
    )


@login_required
@require_POST
def eliminar_actor(request, pk):
    actor = get_object_or_404(ActorClave, pk=pk)
    actor.activo = False
    actor.save()
    return redirect("actor-detalle", subsistema_id=actor.subsistema.id_subsistema)
