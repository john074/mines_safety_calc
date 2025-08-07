from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .helpers.get_data_by_inn import get_data
from .models import Calculation
from django.db.models import Q
from datetime import datetime

# Create your views here.
@login_required(login_url="/users/login/")
def newcalc_view(requset):
    return render(requset, "calculations/newcalc.html")


@login_required(login_url="/users/login/")
def company_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'fetch':
            inn = request.POST.get('inn', '').strip()
            if not inn:
                messages.error(request, "Поле ИНН обязательно для запроса.")
                return render(request, 'calculations/newcalc.html')
            data = get_data(inn)
            if isinstance(data, dict):
                data["inn"] = inn
                return render(request, 'calculations/newcalc.html', {'data': data})
            else:
                messages.error(request, data)
                return render(request, 'calculations/newcalc.html', {'data' : {"inn":inn}})

        elif action == 'calculate':
            required_fields = ['inn', 'name', 'kpp', 'ogrn', 'address']
            data = { i : request.POST.get(i, '').strip() for i in required_fields }
            if '' in data.values():
                messages.error(request, "Заполните все поля перед расчетом.")
                return render(request, 'calculations/newcalc.html', {'data': data})
            
            if (len(data["inn"]) != 12 and len(data["inn"]) != 10) or not all(i.isdigit() for i in data["inn"]):
                messages.error(request, "Некорректный формат ИНН.")
                return render(request, 'calculations/newcalc.html', {'data': data})

            if len(data["kpp"]) != 9 or not all(i.isdigit() for i in data["kpp"]):
                messages.error(request, "Некорректный формат КПП.")
                return render(request, 'calculations/newcalc.html', {'data': data})

            if len(data["ogrn"]) != 13 or not all(i.isdigit() for i in data["ogrn"]):
                messages.error(request, "Некорректный формат ОГРН.")
                return render(request, 'calculations/newcalc.html', {'data': data})

            new_calculation = Calculation(
                user = request.user,
                organisation_INN = data["inn"],
                organisation_KPP = data["kpp"],
                organisation_OGRN = data["ogrn"],
                organisation_name = data["name"],
                organisation_address = data["address"],
            )
            new_calculation.save()
            
            return redirect('calculations:r0')

    return render(request, 'calculations/newcalc.html')


@login_required(login_url="/users/login/")
def r0_view(request):
    return render(request, "calculations/r0.html")


@login_required(login_url="/users/login/")
def history_view(request):
    user = request.user
    sort_param = request.GET.get("sort", "-created")
    filter_by = request.GET.get("filter_by", "")
    query = request.GET.get("query", "").strip()
    created_from = request.GET.get("created_from")
    created_to = request.GET.get("created_to")

    qs = Calculation.objects.all() if user.groups.filter(name="boss").exists() else Calculation.objects.filter(user=user)

    if filter_by and query:
        if filter_by == "organisation_INN":
            qs = qs.filter(organisation_INN__icontains=query)
        elif filter_by == "organisation_name":
            qs = qs.filter(organisation_name__icontains=query)
        elif filter_by == "user":
            qs = qs.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__username__icontains=query)
            )

    if created_from:
        try:
            created_from_date = datetime.strptime(created_from, "%Y-%m-%d")
            qs = qs.filter(created__date__gte=created_from_date)
        except ValueError:
            pass
    if created_to:
        try:
            created_to_date = datetime.strptime(created_to, "%Y-%m-%d")
            qs = qs.filter(created__date__lte=created_to_date)
        except ValueError:
            pass

    allowed_sort_fields = {
        "user", "-user", "created", "-created",
        "organisation_INN", "-organisation_INN",
        "organisation_name", "-organisation_name",
        "is_complete", "-is_complete"
    }
    if sort_param not in allowed_sort_fields:
        sort_param = "-created"

    qs = qs.order_by(sort_param)

    headers = {
        "user": "Пользователь",
        "created": "Дата создания",
        "organisation_INN": "ИНН",
        "organisation_name": "Наименование",
        "is_complete": "Статус",
    }

    return render(request, "calculations/history.html", {
        "calculations": qs,
        "headers": headers,
        "current_sort": sort_param,
    })


@login_required(login_url="/users/login/")
def calc_details_view(request, pk):
    calc = get_object_or_404(Calculation, pk=pk)
    return render(request, 'calculations/calc_details.html', {'calc': calc})
