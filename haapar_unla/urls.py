from django.contrib import admin
from django.urls import path, include
from haapar_unla_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('signup/', views.registro, name='registro'),
    path('signin/', views.iniciar_sesion, name='iniciar_sesion'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),
    path('proyectos/', views.listar_proyectos, name='listar_proyectos'),
    path('proyecto-detalle/<int:tema_id>/', views.proyecto_detalle, name='proyecto_detalle'),
    
    path('crear-reporte/', views.crear_reporte, name='crear-reporte'),
    path('eliminar-proyecto/<int:id_tema>/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path("variables/", views.variable_detalle, name="variable_detalle"),
    path("variables/<int:pk>/eliminar/", views.eliminar_variable, name="eliminar_variable"),
    path("variables/<int:pk>/editar/", views.editar_variable, name="editar_variable"),
    path("variables/crear/", views.crear_variable, name="crear_variable"),

    path('perfil/', views.perfil, name='perfil'),
    path('subsistemas/', views.subsistemas, name='subsistemas'),

    path('actor-detalle/<int:tema_id>/', views.actor_detalle, name='actor_detalle'),
    path("actores/<int:pk>/eliminar/", views.eliminar_actor, name="eliminar_actor"),
    path("actores/<int:pk>/editar/", views.editar_actor, name="editar_actor"),
    path("actores/crear/<int:tema_id>/", views.crear_actor, name="crear_actor"),
    
    # URLS PARA "OLVIDE MI CONTRASEÑA"
    path('olvide-contrasena/', views.password_reset_request, name='password_reset_request'),
    path('restablecer/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password_reset_done/', views.password_reset_done, name='password_reset_done'),
    path('password_reset_complete/', views.password_reset_complete, name='password_reset_complete'),

    # URLS PARA VISTAS Y GESTIÓN DE TENDENCIAS
    path('tendencias/', views.listar_tendencias, name='listar_tendencias'),
    path('tendencias-detalle/<int:tema_id>/', views.tendencia_detalle, name='tendencia_detalle'),
    path('tendencias/crear/<int:tema_id>/', views.crear_tendencia, name='crear_tendencia'),
    path('tendencias/<int:pk>/editar/', views.editar_tendencia, name='editar_tendencia'),
    path('tendencias/<int:pk>/eliminar/', views.eliminar_tendencia, name='eliminar_tendencia'),
]

handler400 = 'haapar_unla_app.views.error_400_view'
handler403 = 'haapar_unla_app.views.error_403_view'
handler404 = 'haapar_unla_app.views.error_404_view'
handler500 = 'haapar_unla_app.views.error_500_view'
