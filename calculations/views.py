from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .helpers.get_data_by_inn import get_data
from .models import Calculation, ParameterGroup, Parameter, ParameterOption, CalculationParameterData
from django.db.models import Q, Prefetch
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
import json

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
            
            return redirect('calculations:rX', calc_id=new_calculation.id, group_code='r0')

    return render(request, 'calculations/newcalc.html')


PARAMETER_CODES = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8']

@login_required(login_url="/users/login/")
def rX_view(request, calc_id, group_code):
    calculation = get_object_or_404(Calculation, id=calc_id)
    if (calculation.is_complete):
        return redirect('calculations:history')
    group = get_object_or_404(ParameterGroup, code=group_code)

    if group_code == 'r0':
        all_parameters = Parameter.objects.all()
        for p in all_parameters:
            CalculationParameterData.objects.get_or_create(
                calculation=calculation,
                parameter=p,
                defaults={
                    "value_before": "",
                    "value_after": "",
                    "actions_description": ""
                }
            )

    parameters = Parameter.objects.filter(group=group).order_by('order_num')

    param_data_dict = {
        pd.parameter_id: pd
        for pd in CalculationParameterData.objects.filter(
            calculation=calculation,
            parameter__in=parameters
        )
    }

    for p in parameters:
        p.data = param_data_dict.get(p.id)
    
    next_code = None
    current_index = PARAMETER_CODES.index(group_code)
    prev_code = PARAMETER_CODES[current_index - 1] if current_index > 0 else None

    if request.method == "POST":
        for param in parameters:
            value_before = request.POST.get(f"before_{param.id}", "")
            value_after = request.POST.get(f"after_{param.id}", "")
            actions_description = request.POST.get(f"actions_{param.id}", "")

            CalculationParameterData.objects.filter(
                calculation=calculation,
                parameter=param
            ).update(
                value_before=value_before,
                value_after=value_after,
                actions_description=actions_description
            )

        current_index = PARAMETER_CODES.index(group_code)
        if current_index < len(PARAMETER_CODES) - 1:
            next_code = PARAMETER_CODES[current_index + 1]
            return redirect('calculations:rX', calc_id=calculation.id, group_code=next_code)
        else:
            calculation.is_complete = True
            calculation.save()
            return redirect('calculations:history')

    context = {
        "calculation": calculation,
        "group": group,
        "parameters": parameters,
        "next_code": next_code,
        "prev_code": prev_code,
    }

    return render(request, "calculations/rX.html", context)


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



@login_required
@csrf_exempt
def save_param_value(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"})

    try:
        data = json.loads(request.body)
        calc_id = data.get("calc_id")
        param_id = data.get("param_id")
        field_type = data.get("field_type")
        value = data.get("value")

        if field_type not in ["value_before", "value_after", "actions_description"]:
            return JsonResponse({"success": False, "error": "Invalid field type"})

        cp_data, created = CalculationParameterData.objects.get_or_create(
            calculation_id=calc_id,
            parameter_id=param_id,
            defaults={"value_before": "", "value_after": "", "actions_description": ""}
        )

        setattr(cp_data, field_type, value)
        cp_data.save()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})