from django.contrib import admin
from django.urls import path
from haapar_unla_app import views
from django.urls import include

from django.conf.urls import handler400, handler403, handler404, handler500

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Autenticación
    path('', views.inicio, name='inicio'),
    path('signup/', views.registro, name='registro'),
    path('signin/', views.iniciar_sesion, name='iniciar_sesion'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),

    # Proyectos
    path('proyectos/', views.listar_proyectos, name='listar_proyectos'),
    path('proyecto/<int:tema_id>/<int:subsistema_id>/', views.proyecto_detalle, name='proyecto_detalle'),
    path('eliminar-proyecto/<int:id_tema>/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path('crear-reporte/', views.crear_reporte, name='crear-reporte'),
    
    # Graficos FODA
   path('foda/<int:subsistema_id>/', views.foda_graficos, name='foda_graficos'),
    path('matriz/<int:subsistema_id>/', views.editar_matriz, name='editar_matriz'),
    

    # Variables
    path('variables/<int:subsistema_id>/', views.variable_detalle, name='variable_detalle'),
    path("variables/<int:pk>/eliminar/", views.eliminar_variable, name="eliminar_variable"),
    path("variables/<int:pk>/editar/", views.editar_variable, name="editar_variable"),
    path('variables/crear/<int:subsistema_id>/', views.crear_variable, name='crear_variable'),
    path('variables/historial/<int:subsistema_id>/', views.historial_variables, name='historial_variables_subsistema'),

    # Perfil
    path('perfil/', views.perfil, name='perfil'),

    # Subsistemas
    path("tema/<int:tema_id>/subsistemas/", views.subsistemas, name="subsistemas"),
    path("tema/<int:tema_id>/crear-subsistema/", views.crear_subsistema, name="crear_subsistema"),
    path('subsistema/<int:sub_id>/eliminar/', views.eliminar_subsistema, name='eliminar_subsistema'),

    # Actores
    path('actor-detalle/<int:subsistema_id>/', views.actor_detalle, name='actor_detalle'),
    path("actores/<int:pk>/eliminar/", views.eliminar_actor, name="eliminar_actor"),
    path("actores/<int:pk>/editar/", views.editar_actor, name="editar_actor"),
    path("actores/crear/<int:subsistema_id>/", views.crear_actor, name="crear_actor"),

    # Recuperación de contraseña
    path('recuperar-contrasenia/', views.password_reset_request, name='password_reset_request'),
    path('restablecer/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password_reset_done/', views.password_reset_done, name='password_reset_done'),
    path('password_reset_complete/', views.password_reset_complete, name='password_reset_complete'),

    # Reactivar cuenta
    path('reactivar/<uidb64>/<token>/', views.reactivar_cuenta, name='reactivar_cuenta'),

    # Tendencias
    path('tendencias/', views.listar_tendencias, name='listar_tendencias'),
    path('tendencias-detalle/<int:subsistema_id>/', views.tendencia_detalle, name='tendencia_detalle'),
    path('tendencias/crear/<int:subsistema_id>/', views.crear_tendencia, name='crear_tendencia'),
    path('tendencias/<int:pk>/editar/', views.editar_tendencia, name='editar_tendencia'),
    path('tendencias/<int:pk>/eliminar/', views.eliminar_tendencia, name='eliminar_tendencia'),
    
    # API interna para ChatGPT
    path('api/', include('haapar_unla_app.infraestructura.api_urls')),
    
    #Agregar colaboradores
     path('tema/<int:tema_id>/colaboradores/', views.asignar_colaboradores, name='asignar_colaboradores'),
]

handler400 = 'haapar_unla_app.views.error_400_view'
handler403 = 'haapar_unla_app.views.error_403_view'
handler404 = 'haapar_unla_app.views.error_404_view'
handler500 = 'haapar_unla_app.views.error_500_view'
