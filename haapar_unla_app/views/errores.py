from django.shortcuts import render


def error_400_view(request, exception):
    return render(request, "haapar_unla_app/error/400.html", status=400)


def error_403_view(request, exception):
    return render(request, "haapar_unla_app/error/403.html", status=403)


def error_404_view(request, exception):
    return render(request, "haapar_unla_app/error/404.html", status=404)


def error_500_view(request):
    return render(request, "haapar_unla_app/error/500.html", status=500)
