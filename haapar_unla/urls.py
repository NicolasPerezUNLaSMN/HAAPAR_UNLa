"""
URL configuration for haapar_unla project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from haapar_unla_app import views

from django.conf.urls import handler400, handler403, handler404, handler500

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
]

handler400 = views.error_400_view
handler403 = views.error_403_view
handler404 = views.error_404_view
handler500 = views.error_500_view
