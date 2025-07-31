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
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('blog-details/', views.blog_details, name='blog-details'),
    path('crear-reporte/', views.crear_reporte, name='crear_reporte'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('portfolio-details/', views.portfolio_details, name='portfolio-details'),
    path('services/', views.services, name='services'),
    path('service-details/', views.service_details, name='service-details'),
    path('team/', views.team, name='team'),
    path('starter-page/', views.starter_page, name='starter-page'),
    path('signup/', views.registro, name='registro'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),
    path('signin/', views.iniciar_sesion, name='iniciar_sesion'),
]

handler400 = views.error_400_view
handler403 = views.error_403_view
handler404 = views.error_404_view
handler500 = views.error_500_view
