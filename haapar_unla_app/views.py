from django.shortcuts import render

def inicio(request):
    return render(request, 'haapar_unla_app/index.html')

def about(request):
    return render(request, 'haapar_unla_app/about.html')

def blog_details(request):
    return render(request, 'haapar_unla_app/blog-details.html')

def blog(request):  # Esta es la vista que faltaba
    return render(request, 'haapar_unla_app/blog.html')

def contact(request):
    return render(request, 'haapar_unla_app/contact.html')

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