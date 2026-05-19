from django.shortcuts import render


def landing_page(request):
    return render(request, "pages/landing.html")


def contact_page(request):
    return render(request, "pages/contact.html")


def support_page(request):
    return render(request, "pages/support.html")


def learn_more_page(request):
    return render(request, "pages/learn_more.html")


def custom_404_view(request, exception):
    return render(request, "dashboard/under_maintenance.html", status=404)


def custom_500_view(request):
    return render(request, "dashboard/under_maintenance.html", status=500)