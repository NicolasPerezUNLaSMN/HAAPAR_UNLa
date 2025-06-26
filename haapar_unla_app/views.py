from django.shortcuts import render

def inicio(request):
    return render(request, 'haapar_unla_app/index.html')
