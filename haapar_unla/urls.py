from django.contrib import admin
from django.urls import path, include
import debug_toolbar
from haapar_unla_app import api, views  # endpoints de API
from rest_framework import routers
from haapar_unla_app.views.proyectos import TemaViewSet
from haapar_unla_app.views.variables import VariableViewSet
router = routers.DefaultRouter()
router.register(r"proyectos", TemaViewSet, basename="proyectos")
router.register(r"variables", VariableViewSet, basename="variables")
urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Autenticación
    path("", views.inicio, name="inicio"),
    path("sign-up/", views.registro, name="sign-up"),
    path("sign-in/", views.iniciar_sesion, name="sign-in"),
    path("log-out/", views.cerrar_sesion, name="log-out"),
    # Proyectos
    path("proyectos/", views.listar_proyectos, name="listar-proyectos"),
    path(
        "proyecto/<int:tema_id>/<int:subsistema_id>/",
        views.proyecto_detalle,
        name="proyecto-detalle",
    ),
    path(
        "eliminar-proyecto/<int:id_tema>/",
        views.eliminar_proyecto,
        name="eliminar-proyecto",
    ),
    path("crear-reporte/", views.crear_reporte, name="crear-reporte"),
    # Graficos FODA
    path("foda/<int:subsistema_id>/", views.foda_graficos, name="foda-graficos"),
    path("matriz/<int:subsistema_id>/", views.editar_matriz, name="editar-matriz"),
    # Variables
    path(
        "variables/<int:subsistema_id>/",
        views.variable_detalle,
        name="variable-detalle",
    ),
    path(
        "variables/<int:pk>/eliminar/",
        views.eliminar_variable,
        name="eliminar-variable",
    ),
    path("variables/<int:pk>/editar/", views.editar_variable, name="editar-variable"),
    path(
        "variables/crear/<int:subsistema_id>/",
        views.crear_variable,
        name="crear-variable",
    ),
    path(
        "variables/historial/<int:subsistema_id>/",
        views.historial_variables,
        name="historial-variables-subsistema",
    ),
    
    path(
    "variables/<int:pk>/editar-pestel/",
    views.editar_pestel,
    name="editar-pestel",
    ),
    
    path("__debug__/", include(debug_toolbar.urls)),
    path("api/", include(router.urls)), 
    # Perfil
    path("perfil/", views.perfil, name="perfil"),
    # Subsistemas
    path("tema/<int:tema_id>/subsistemas/", views.subsistemas, name="subsistemas"),
    path(
        "tema/<int:tema_id>/crear-subsistema/",
        views.crear_subsistema,
        name="crear-subsistema",
    ),
    path(
        "subsistema/<int:sub_id>/eliminar/",
        views.eliminar_subsistema,
        name="eliminar-subsistema",
    ),
    # Actores
    path(
        "actor-detalle/<int:subsistema_id>/", views.actor_detalle, name="actor-detalle"
    ),
    path("actores/<int:pk>/eliminar/", views.eliminar_actor, name="eliminar-actor"),
    path("actores/<int:pk>/editar/", views.editar_actor, name="editar-actor"),
    path("actores/crear/<int:subsistema_id>/", views.crear_actor, name="crear-actor"),
    # Recuperación de contraseña
    path(
        "recuperar-contrasenia/",
        views.password_reset_request,
        name="password-reset-request",
    ),
    path(
        "restablecer/<uidb64>/<token>/",
        views.password_reset_confirm,
        name="password-reset-confirm",
    ),
    path("password-reset-done/", views.password_reset_done, name="password-reset-done"),
    path(
        "password-reset-complete/",
        views.password_reset_complete,
        name="password-reset-complete",
    ),
    # Reactivar cuenta
    path(
        "reactivar/<uidb64>/<token>/", views.reactivar_cuenta, name="reactivar-cuenta"
    ),
    # Tendencias
    path("tendencias/", views.listar_tendencias, name="listar-tendencias"),
    path(
        "tendencias-detalle/<int:subsistema_id>/",
        views.tendencia_detalle,
        name="tendencia-detalle",
    ),
    path(
        "tendencias/crear/<int:subsistema_id>/",
        views.crear_tendencia,
        name="crear-tendencia",
    ),
    path(
        "tendencias/<int:pk>/editar/", views.editar_tendencia, name="editar-tendencia"
    ),
    path(
        "tendencias/<int:pk>/eliminar/",
        views.eliminar_tendencia,
        name="eliminar-tendencia",
    ),
    # Agregar colaboradores
    path(
        "tema/<int:tema_id>/colaboradores/",
        views.asignar_colaboradores,
        name="asignar-colaboradores",
    ),
    # ==========================================
    # Endpoints API REST
    # ==========================================
    path("api/temas/", api.api_listar_temas, name="api-temas"),
    path("api/variables/", api.api_listar_variables, name="api-variables"),
    path("api/foda/<int:tema_id>/", api.api_foda_tema, name="api-foda"),
]

handler400 = "haapar_unla_app.views.error_400_view"
handler403 = "haapar_unla_app.views.error_403_view"
handler404 = "haapar_unla_app.views.error_404_view"
handler500 = "haapar_unla_app.views.error_500_view"
