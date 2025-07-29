from django.shortcuts import render


def inicio(request):
    return render(request, 'haapar_unla_app/index.html')


def about(request):
    return render(request, 'haapar_unla_app/about.html')


def blog_details(request):
    return render(request, 'haapar_unla_app/blog-details.html')


def blog(request):  # Esta es la vista que faltaba
    return render(request, 'haapar_unla_app/blog.html')


def crear_reporte(request):
    return render(request, 'haapar_unla_app/crear-reporte.html')


def portfolio_details(request):
    return render(request, 'haapar_unla_app/portfolio-details.html')


def portfolio(request):
    return render(request, 'haapar_unla_app/portfolio.html')


def service_details(request):
    return render(request, 'haapar_unla_app/service-details.html')


def services(request):
    return render(request, 'haapar_unla_app/services.html')


def starter_page(request):
    return render(request, 'haapar_unla_app/starter-page.html')


def team(request):
    return render(request, 'haapar_unla_app/team.html')


# Vista para manejar el error 400
def error_400_view(request, exception):
    return render(request, 'haapar_unla_app/error/400.html', status=400)


# Vista para manejar el error 403
def error_403_view(request, exception):
    return render(request, 'haapar_unla_app/error/403.html', status=403)


# Vista para manejar el error 404
def error_404_view(request, exception):
    return render(request, 'haapar_unla_app/error/404.html', status=404)


# Vista para manejar el error 500
def error_500_view(request):
    return render(request, 'haapar_unla_app/error/500.html', status=500)

