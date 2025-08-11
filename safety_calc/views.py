from django.shortcuts import redirect


def base_page(request):
    return redirect("calculations:history")
